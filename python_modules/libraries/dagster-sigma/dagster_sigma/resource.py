from collections import defaultdict
from enum import Enum
from typing import AbstractSet, Any, Dict, List, Mapping, Optional

import requests
from dagster import ConfigurableResource
from dagster._record import record
from dagster._utils.cached_method import cached_method
from pydantic import Field, PrivateAttr
from sqlglot import exp, parse_one


class SigmaBaseUrl(str, Enum):
    AWS_US = "https://aws-api.sigmacomputing.com"
    AWS_CANADA = "https://api.ca.aws.sigmacomputing.com"
    AWS_EUROPE = "https://api.eu.aws.sigmacomputing.com"
    AWS_UK = "https://api.uk.aws.sigmacomputing.com"
    AZURE_US = "https://api.us.azure.sigmacomputing.com"
    GCP = "https://api.sigmacomputing.com"


@record
class SigmaWorkbook:
    properties: Dict[str, Any]
    datasets: AbstractSet[str]


@record
class SigmaDataset:
    properties: Dict[str, Any]
    columns: AbstractSet[str]
    inputs: AbstractSet[str]


def _inode_from_url(url: str) -> str:
    """Builds a Sigma internal inode value from a Sigma URL."""
    return f'inode-{url.split("/")[-1]}'


@record
class SigmaOrganizationData:
    workbooks: List[SigmaWorkbook]
    datasets: List[SigmaDataset]


class SigmaOrganization(ConfigurableResource):
    """Represents a workspace in PowerBI and provides utilities
    to interact with the PowerBI API.
    """

    base_url: str = Field(
        ...,
        description=(
            "Base URL for the cloud type of your Sigma organization, found under the Administration -> Account -> Site settings."
            " See https://help.sigmacomputing.com/reference/get-started-sigma-api#identify-your-api-request-url for more information."
        ),
    )
    client_id: str = Field(..., description="A client ID with access to the Sigma API.")
    client_secret: str = Field(..., description="A client secret with access to the Sigma API.")

    _api_token: Optional[str] = PrivateAttr(None)

    def _fetch_api_token(self) -> str:
        response = requests.post(
            url=f"{self.base_url}/v2/auth/token",
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
            url=f"{self.base_url}/v2/{endpoint}",
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
    def get_organization_data(self) -> SigmaOrganizationData:
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
