from collections import defaultdict
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Sequence, Type

import requests
from dagster import (
    ConfigurableResource,
    _check as check,
)
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.external_asset import external_assets_from_specs
from dagster._serdes.serdes import deserialize_value, serialize_value
from dagster._utils.cached_method import cached_method
from pydantic import Field, PrivateAttr
from sqlglot import exp, parse_one

from dagster_sigma.translator import (
    DagsterSigmaTranslator,
    SigmaDataset,
    SigmaOrganizationData,
    SigmaWorkbook,
    _inode_from_url,
)


class SigmaCloudType(Enum):
    AWS_US = "https://aws-api.sigmacomputing.com"
    AWS_CANADA = "https://api.ca.aws.sigmacomputing.com"
    AWS_EUROPE = "https://api.eu.aws.sigmacomputing.com"
    AWS_UK = "https://api.uk.aws.sigmacomputing.com"
    AZURE_US = "https://api.us.azure.sigmacomputing.com"
    GCP = "https://api.sigmacomputing.com"


class SigmaOrganization(ConfigurableResource):
    """Represents a workspace in Sigma and provides utilities
    to interact with the Sigma API.
    """

    cloud_type: SigmaCloudType = Field(
        ...,
        description="The cloud type for your Sigma organization, found under the Administration -> Account -> Site settings.",
    )
    client_id: str = Field(..., description="A client ID with access to the Sigma API.")
    client_secret: str = Field(..., description="A client secret with access to the Sigma API.")

    _api_token: Optional[str] = PrivateAttr(None)

    def _fetch_api_token(self) -> str:
        response = requests.post(
            url=f"{self.cloud_type.value}/v2/auth/token",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        response.raise_for_status()
        return response.json()["access_token"]

    @property
    def api_token(self) -> str:
        if self._api_token is None:
            self._api_token = self._fetch_api_token()

        return self._api_token

    def fetch_json(self, endpoint: str, method: str = "GET") -> Dict[str, Any]:
        response = requests.request(
            method=method,
            url=f"{self.cloud_type.value}/v2/{endpoint}",
            headers={"Accept": "application/json", "Authorization": f"Bearer {self.api_token}"},
        )
        response.raise_for_status()
        return response.json()

    @cached_method
    def fetch_workbooks(self) -> List[Dict[str, Any]]:
        return self.fetch_json("workbooks")["entries"]

    @cached_method
    def fetch_datasets(self) -> List[Dict[str, Any]]:
        return self.fetch_json("datasets")["entries"]

    @cached_method
    def fetch_pages_for_workbook(self, workbook_id: str) -> List[Dict[str, Any]]:
        return self.fetch_json(f"workbooks/{workbook_id}/pages")["entries"]

    @cached_method
    def fetch_elements_for_page(self, workbook_id: str, page_id: str) -> List[Dict[str, Any]]:
        return self.fetch_json(f"workbooks/{workbook_id}/pages/{page_id}/elements")["entries"]

    @cached_method
    def fetch_lineage_for_element(self, workbook_id: str, element_id: str) -> Dict[str, Any]:
        return self.fetch_json(f"workbooks/{workbook_id}/lineage/elements/{element_id}")

    @cached_method
    def fetch_columns_for_element(self, workbook_id: str, element_id: str) -> List[Dict[str, Any]]:
        return self.fetch_json(f"workbooks/{workbook_id}/elements/{element_id}/columns")["entries"]

    @cached_method
    def fetch_queries_for_workbook(self, workbook_id: str) -> List[Dict[str, Any]]:
        return self.fetch_json(f"workbooks/{workbook_id}/queries")["entries"]

    @cached_method
    def build_organization_data(self) -> SigmaOrganizationData:
        raw_workbooks = self.fetch_workbooks()

        dataset_inode_to_name: Mapping[str, str] = {}
        columns_by_dataset_inode = defaultdict(set)
        deps_by_dataset_inode = defaultdict(set)
        dataset_element_to_inode: Mapping[str, str] = {}

        workbooks: List[SigmaWorkbook] = []

        # Unfortunately, Sigma's API does not nicely model the relationship between various assets.
        # We have to do some manual work to infer these relationships ourselves.
        for workbook in raw_workbooks:
            workbook_deps = set()
            pages = self.fetch_pages_for_workbook(workbook["workbookId"])
            for page in pages:
                elements = self.fetch_elements_for_page(workbook["workbookId"], page["pageId"])
                for element in elements:
                    # We extract the list of dataset dependencies from the lineage of each workbook.
                    lineage = self.fetch_lineage_for_element(
                        workbook["workbookId"], element["elementId"]
                    )
                    for inode, item in lineage["dependencies"].items():
                        if item.get("type") == "dataset":
                            workbook_deps.add(item["nodeId"])
                            dataset_inode_to_name[inode] = item["name"]
                            dataset_element_to_inode[element["elementId"]] = item["nodeId"]

                    # We can't query the list of columns in a dataset directly, so we have to build a partial
                    # list from the columns which appear in any workbook.
                    columns = self.fetch_columns_for_element(
                        workbook["workbookId"], element["elementId"]
                    )
                    for column in columns:
                        split = column["columnId"].split("/")
                        if len(split) == 2:
                            inode, column_name = split
                            columns_by_dataset_inode[inode].add(column_name)

            # Finally, we extract the list of tables used in each query in the workbook with
            # the help of sqlglot. Each query is associated with an "element", or section of the
            # workbook. We know which dataset each element is associated with, so we can infer
            # the dataset for each query, and from there build a list of tables which the dataset
            # depends on.
            queries = self.fetch_queries_for_workbook(workbook["workbookId"])
            for query in queries:
                element_id = query["elementId"]
                table_deps = set(
                    [
                        f"{table.catalog}.{table.db}.{table.this}"
                        for table in list(parse_one(query["sql"]).find_all(exp.Table))
                        if table.catalog
                    ]
                )

                deps_by_dataset_inode[dataset_element_to_inode[element_id]] = deps_by_dataset_inode[
                    dataset_element_to_inode[element_id]
                ].union(table_deps)

            workbooks.append(SigmaWorkbook(properties=workbook, datasets=workbook_deps))

        datasets: List[SigmaDataset] = []
        for dataset in self.fetch_datasets():
            inode = _inode_from_url(dataset["url"])
            datasets.append(
                SigmaDataset(
                    properties=dataset,
                    columns=columns_by_dataset_inode.get(inode, set()),
                    inputs=deps_by_dataset_inode[inode],
                )
            )

        return SigmaOrganizationData(workbooks=workbooks, datasets=datasets)

    def build_assets(
        self,
        dagster_sigma_translator: Type[DagsterSigmaTranslator],
    ) -> Sequence[CacheableAssetsDefinition]:
        """Returns a set of CacheableAssetsDefinition which will load Sigma content from
        the organization and translates it into AssetSpecs, using the provided translator.

        Args:
            dagster_sigma_translator (Type[DagsterSigmaTranslator]): The translator to use
                to convert Sigma content into AssetSpecs. Defaults to DagsterSigmaTranslator.

        Returns:
            Sequence[CacheableAssetsDefinition]: A list of CacheableAssetsDefinitions which
                will load the Sigma content.
        """
        return [
            SigmaCacheableAssetsDefinition(
                self,
                dagster_sigma_translator,
            )
        ]

    def build_defs(
        self, dagster_sigma_translator: Type[DagsterSigmaTranslator] = DagsterSigmaTranslator
    ) -> Definitions:
        """Returns a Definitions object which will load Power BI content from
        the organization and translates it into AssetSpecs, using the provided translator.

        Args:
            dagster_sigma_translator (Type[DagsterSigmaTranslator]): The translator to use
                to conver Sigma content into AssetSpecs. Defaults to DagsterSigmaTranslator.

        Returns:
            Definitions: A Definitions object which will load the Sigma content.
        """
        return Definitions(
            assets=self.build_assets(dagster_sigma_translator=dagster_sigma_translator)
        )


class SigmaCacheableAssetsDefinition(CacheableAssetsDefinition):
    def __init__(
        self,
        organization: SigmaOrganization,
        translator: Type[DagsterSigmaTranslator],
    ):
        self._organization = organization
        self._translator_cls = translator
        super().__init__(unique_id=f"sigma_{self._organization.client_id}")

    def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:
        organization_data = self._organization.build_organization_data()
        return [
            AssetsDefinitionCacheableData(
                extra_metadata={
                    "workbooks": [
                        serialize_value(workbook) for workbook in organization_data.workbooks
                    ],
                    "datasets": [
                        serialize_value(dataset) for dataset in organization_data.datasets
                    ],
                }
            )
        ]

    def build_definitions(
        self,
        data: Sequence[AssetsDefinitionCacheableData],
    ) -> Sequence[AssetsDefinition]:
        cached_data = check.not_none(data[0].extra_metadata)
        workbooks = [
            deserialize_value(workbook, as_type=SigmaWorkbook)
            for workbook in cached_data["workbooks"]
        ]
        datasets = [
            deserialize_value(dataset, as_type=SigmaDataset) for dataset in cached_data["datasets"]
        ]

        org_data = SigmaOrganizationData(workbooks=workbooks, datasets=datasets)

        translator = self._translator_cls(context=org_data)

        asset_specs = [
            *[translator.get_workbook_spec(workbook) for workbook in org_data.workbooks],
            *[translator.get_dataset_spec(dataset) for dataset in org_data.datasets],
        ]

        return [*external_assets_from_specs(asset_specs)]
