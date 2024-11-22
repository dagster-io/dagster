import asyncio
import contextlib
import os
import urllib.parse
import warnings
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
)

import aiohttp
import dagster._check as check
import requests
from aiohttp.client_exceptions import ClientResponseError
from dagster import ConfigurableResource
from dagster._annotations import deprecated, experimental, public
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.definitions_load_context import StateBackedDefinitionsLoader
from dagster._core.definitions.repository_definition.repository_definition import RepositoryLoadData
from dagster._record import IHaveNew, record_custom
from dagster._serdes.serdes import deserialize_value
from dagster._utils.cached_method import cached_method
from dagster._utils.log import get_dagster_logger
from pydantic import Field, PrivateAttr
from sqlglot import exp, parse_one

from dagster_sigma.cli import SIGMA_RECON_DATA_PREFIX, SNAPSHOT_ENV_VAR_NAME
from dagster_sigma.translator import (
    DagsterSigmaTranslator,
    SigmaDataset,
    SigmaOrganizationData,
    SigmaTable,
    SigmaWorkbook,
    _inode_from_url,
)

SIGMA_PARTNER_ID_TAG = {"X-Sigma-Partner-Id": "dagster"}

logger = get_dagster_logger("dagster_sigma")


@record_custom
class SigmaFilter(IHaveNew):
    """Filters the set of Sigma objects to fetch.

    Args:
        workbook_folders (Optional[Sequence[Sequence[str]]]): A list of folder paths to fetch workbooks from.
            Each folder path is a list of folder names, starting from the root folder. All workbooks
            contained in the specified folders will be fetched. If not provided, all workbooks will be fetched.
        include_unused_datasets (bool): Whether to include datasets that are not used in any workbooks.
            Defaults to True.
    """

    workbook_folders: Optional[Sequence[Sequence[str]]] = None
    include_unused_datasets: bool = True

    def __new__(
        cls,
        workbook_folders: Optional[Sequence[Sequence[str]]] = None,
        include_unused_datasets: bool = True,
    ):
        return super().__new__(
            cls,
            workbook_folders=tuple([tuple(folder) for folder in workbook_folders or []]),
            include_unused_datasets=include_unused_datasets,
        )


class SigmaBaseUrl(str, Enum):
    """Enumeration of Sigma API base URLs for different cloud providers.

    https://help.sigmacomputing.com/reference/get-started-sigma-api#identify-your-api-request-url
    """

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

    base_url: str = Field(
        ...,
        description=(
            "Base URL for the cloud type of your Sigma organization, found under the Administration -> Account -> Site settings."
            " See https://help.sigmacomputing.com/reference/get-started-sigma-api#identify-your-api-request-url for more information."
        ),
    )
    client_id: str = Field(..., description="A client ID with access to the Sigma API.")
    client_secret: str = Field(..., description="A client secret with access to the Sigma API.")
    warn_on_lineage_fetch_error: bool = Field(
        default=False,
        description="Whether to warn rather than raise when lineage data cannot be fetched for an element.",
    )

    _api_token: Optional[str] = PrivateAttr(None)

    def _fetch_api_token(self) -> str:
        response = requests.post(
            url=f"{self.base_url}/v2/auth/token",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                **SIGMA_PARTNER_ID_TAG,
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

    async def _fetch_json_async(
        self,
        endpoint: str,
        method: str = "GET",
        query_params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}/v2/{endpoint}"
        if query_params:
            url = f"{url}?{urllib.parse.urlencode(query_params)}"

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self.api_token}",
                    **SIGMA_PARTNER_ID_TAG,
                },
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def _fetch_json_async_paginated_entries(
        self, endpoint: str, query_params: Optional[dict[str, Any]] = None, limit: int = 1000
    ) -> list[dict[str, Any]]:
        entries = []

        query_params_with_limit = {
            **(query_params or {}),
            "limit": limit,
        }

        result = await self._fetch_json_async(endpoint, query_params=query_params_with_limit)
        entries.extend(result["entries"])
        logger.debug(
            "Fetched %s\n  Query params %s\n  Received %s entries%s",
            endpoint,
            query_params_with_limit,
            len(entries),
            ", fetching additional results" if result.get("hasMore") else "",
        )

        while result.get("hasMore") in (True, "true", "True"):
            next_page = result["nextPage"]
            query_params_with_limit_and_page = {
                **query_params_with_limit,
                "page": next_page,
            }
            result = await self._fetch_json_async(
                endpoint, query_params=query_params_with_limit_and_page
            )
            entries.extend(result["entries"])
            logger.debug(
                "Fetched %s\n  Query params %s\n  Received %s entries%s",
                endpoint,
                query_params_with_limit_and_page,
                len(result["entries"]),
                ", fetching additional results" if result.get("hasMore") else "",
            )
        return entries

    @cached_method
    async def _fetch_workbooks(self) -> list[dict[str, Any]]:
        return await self._fetch_json_async_paginated_entries("workbooks")

    @cached_method
    async def _fetch_datasets(self) -> list[dict[str, Any]]:
        return await self._fetch_json_async_paginated_entries("datasets")

    @cached_method
    async def _fetch_tables(self) -> list[dict[str, Any]]:
        return await self._fetch_json_async_paginated_entries(
            "files", query_params={"typeFilters": "table"}
        )

    @cached_method
    async def _fetch_pages_for_workbook(self, workbook_id: str) -> list[dict[str, Any]]:
        return await self._fetch_json_async_paginated_entries(f"workbooks/{workbook_id}/pages")

    @cached_method
    async def _fetch_elements_for_page(
        self, workbook_id: str, page_id: str
    ) -> list[dict[str, Any]]:
        return await self._fetch_json_async_paginated_entries(
            f"workbooks/{workbook_id}/pages/{page_id}/elements"
        )

    @cached_method
    async def _fetch_lineage_for_element(self, workbook_id: str, element_id: str) -> dict[str, Any]:
        return await self._fetch_json_async(
            f"workbooks/{workbook_id}/lineage/elements/{element_id}"
        )

    @cached_method
    async def _fetch_columns_for_element(
        self, workbook_id: str, element_id: str
    ) -> list[dict[str, Any]]:
        return (
            await self._fetch_json_async(f"workbooks/{workbook_id}/elements/{element_id}/columns")
        )["entries"]

    @cached_method
    async def _fetch_queries_for_workbook(self, workbook_id: str) -> list[dict[str, Any]]:
        return (await self._fetch_json_async(f"workbooks/{workbook_id}/queries"))["entries"]

    @contextlib.contextmanager
    def try_except_http_warn(self, should_catch: bool, msg: str) -> Iterator[None]:
        try:
            yield
        except ClientResponseError as e:
            if should_catch:
                warnings.warn(f"{msg} {e}")
            else:
                raise

    @cached_method
    async def _fetch_dataset_upstreams_by_inode(self) -> Mapping[str, AbstractSet[str]]:
        """Builds a mapping of dataset inodes to the upstream inputs they depend on.
        Sigma does not expose this information directly, so we have to infer it from
        the lineage of workbooks and the workbook queries.
        """
        deps_by_dataset_inode = defaultdict(set)

        logger.debug("Fetching dataset dependencies")

        raw_workbooks = await self._fetch_workbooks()

        async def process_workbook(workbook: dict[str, Any]) -> None:
            logger.info("Inferring dataset dependencies for workbook %s", workbook["workbookId"])
            queries = await self._fetch_queries_for_workbook(workbook["workbookId"])
            queries_by_element_id = defaultdict(list)
            for query in queries:
                queries_by_element_id[query["elementId"]].append(query)

            pages = await self._fetch_pages_for_workbook(workbook["workbookId"])
            elements = await asyncio.gather(
                *[
                    self._fetch_elements_for_page(workbook["workbookId"], page["pageId"])
                    for page in pages
                ]
            )

            async def build_deps_from_element(element: dict[str, Any]) -> None:
                # We extract the list of dataset dependencies from the lineage of each element
                # If there is a single dataset dependency, we can then know the queries for that element
                # are associated with that dataset
                with self.try_except_http_warn(
                    self.warn_on_lineage_fetch_error,
                    f"Failed to fetch lineage for element {element['elementId']} in workbook {workbook['workbookId']}",
                ):
                    lineage = await self._fetch_lineage_for_element(
                        workbook["workbookId"], element["elementId"]
                    )
                    dataset_dependencies = [
                        dep
                        for dep in lineage["dependencies"].values()
                        if dep.get("type") == "dataset"
                    ]
                    if len(dataset_dependencies) != 1:
                        return

                    inode = dataset_dependencies[0]["nodeId"]
                    for query in queries_by_element_id[element["elementId"]]:
                        # Use sqlglot to extract the tables used in each query and add them to the dataset's
                        # list of dependencies
                        table_deps = set(
                            [
                                f"{table.catalog}.{table.db}.{table.this}"
                                for table in list(parse_one(query["sql"]).find_all(exp.Table))
                                if table.catalog
                            ]
                        )

                        deps_by_dataset_inode[inode] = deps_by_dataset_inode[inode].union(
                            table_deps
                        )

            await asyncio.gather(
                *[
                    build_deps_from_element(element)
                    for page_elements in elements
                    for element in page_elements
                ]
            )

        await asyncio.gather(*[process_workbook(workbook) for workbook in raw_workbooks])

        return deps_by_dataset_inode

    @cached_method
    async def _fetch_dataset_columns_by_inode(self) -> Mapping[str, AbstractSet[str]]:
        """Builds a mapping of dataset inodes to the columns they contain. Note that
        this is a partial list and will only include columns which are referenced in
        workbooks, since Sigma does not expose a direct API for querying dataset columns.
        """
        columns_by_dataset_inode = defaultdict(set)

        workbooks = await self._fetch_workbooks()

        async def process_workbook(workbook: dict[str, Any]) -> None:
            logger.info("Fetching column data from workbook %s", workbook["workbookId"])
            pages = await self._fetch_pages_for_workbook(workbook["workbookId"])
            elements = [
                element
                for page_elements in await asyncio.gather(
                    *[
                        self._fetch_elements_for_page(workbook["workbookId"], page["pageId"])
                        for page in pages
                    ]
                )
                for element in page_elements
            ]
            columns = [
                column
                for element_cols in await asyncio.gather(
                    *[
                        self._fetch_columns_for_element(
                            workbook["workbookId"], element["elementId"]
                        )
                        for element in elements
                    ]
                )
                for column in element_cols
            ]
            for column in columns:
                split = column["columnId"].split("/")
                if len(split) == 2:
                    inode, column_name = split
                    columns_by_dataset_inode[inode].add(column_name)

        await asyncio.gather(*[process_workbook(workbook) for workbook in workbooks])

        return columns_by_dataset_inode

    @cached_method
    async def build_member_id_to_email_mapping(self) -> Mapping[str, str]:
        """Retrieves all members in the Sigma organization and builds a mapping
        from member ID to email address.
        """
        members = (await self._fetch_json_async("members", query_params={"limit": 500}))["entries"]
        return {member["memberId"]: member["email"] for member in members}

    async def load_workbook_data(self, raw_workbook_data: dict[str, Any]) -> SigmaWorkbook:
        dataset_deps = set()
        direct_table_deps = set()

        logger.info("Fetching data for workbook %s", raw_workbook_data["workbookId"])

        pages = await self._fetch_pages_for_workbook(raw_workbook_data["workbookId"])
        elements = [
            element
            for page_elements in await asyncio.gather(
                *[
                    self._fetch_elements_for_page(raw_workbook_data["workbookId"], page["pageId"])
                    for page in pages
                ]
            )
            for element in page_elements
        ]

        async def safe_fetch_lineage_for_element(
            workbook_id: str, element_id: str
        ) -> dict[str, Any]:
            with self.try_except_http_warn(
                self.warn_on_lineage_fetch_error,
                f"Failed to fetch lineage for element {element_id} in workbook {workbook_id}",
            ):
                return await self._fetch_lineage_for_element(workbook_id, element_id)

            return {"dependencies": {}}

        lineages = await asyncio.gather(
            *[
                safe_fetch_lineage_for_element(
                    raw_workbook_data["workbookId"], element["elementId"]
                )
                for element in elements
            ]
        )
        for lineage in lineages:
            for item in lineage["dependencies"].values():
                if item.get("type") == "dataset":
                    dataset_deps.add(item["nodeId"])
                if item.get("type") == "table":
                    direct_table_deps.add(item["nodeId"])

        return SigmaWorkbook(
            properties=raw_workbook_data,
            datasets=dataset_deps,
            direct_table_deps=direct_table_deps,
            owner_email=None,
            lineage=lineages,
        )

    @cached_method
    async def build_organization_data(
        self, sigma_filter: Optional[SigmaFilter], fetch_column_data: bool
    ) -> SigmaOrganizationData:
        """Retrieves all workbooks and datasets in the Sigma organization and builds a
        SigmaOrganizationData object representing the organization's assets.
        """
        _sigma_filter = sigma_filter or SigmaFilter()

        logger.info("Beginning Sigma organization data fetch")
        raw_workbooks = await self._fetch_workbooks()
        workbooks_to_fetch = []
        if _sigma_filter.workbook_folders:
            workbook_filter_strings = [
                "/".join(folder).lower() for folder in _sigma_filter.workbook_folders
            ]
            for workbook in raw_workbooks:
                workbook_path = str(workbook["path"]).lower()
                if any(
                    workbook_path.startswith(folder_str) for folder_str in workbook_filter_strings
                ):
                    workbooks_to_fetch.append(workbook)
        else:
            workbooks_to_fetch = raw_workbooks

        workbooks: list[SigmaWorkbook] = await asyncio.gather(
            *[self.load_workbook_data(workbook) for workbook in workbooks_to_fetch]
        )

        datasets: list[SigmaDataset] = []
        deps_by_dataset_inode = await self._fetch_dataset_upstreams_by_inode()

        columns_by_dataset_inode = (
            await self._fetch_dataset_columns_by_inode() if fetch_column_data else {}
        )

        used_datasets = set()
        used_tables = set()
        for workbook in workbooks:
            if _sigma_filter and not _sigma_filter.include_unused_datasets:
                used_datasets.update(workbook.datasets)
            used_tables.update(workbook.direct_table_deps)

        logger.info("Fetching dataset data")
        for dataset in await self._fetch_datasets():
            inode = _inode_from_url(dataset["url"])
            if _sigma_filter.include_unused_datasets or inode in used_datasets:
                datasets.append(
                    SigmaDataset(
                        properties=dataset,
                        columns=columns_by_dataset_inode.get(inode, set()),
                        inputs=deps_by_dataset_inode[inode],
                    )
                )

        tables: list[SigmaTable] = []
        logger.info("Fetching table data")
        for table in await self._fetch_tables():
            inode = _inode_from_url(table["urlId"])
            if inode in used_tables:
                tables.append(
                    SigmaTable(
                        properties=table,
                    )
                )

        return SigmaOrganizationData(workbooks=workbooks, datasets=datasets, tables=tables)

    @public
    @deprecated(
        breaking_version="1.9.0",
        additional_warn_text="Use dagster_sigma.load_sigma_asset_specs instead",
    )
    def build_defs(
        self,
        dagster_sigma_translator: type[DagsterSigmaTranslator] = DagsterSigmaTranslator,
        sigma_filter: Optional[SigmaFilter] = None,
        fetch_column_data: bool = True,
    ) -> Definitions:
        """Returns a Definitions object representing the Sigma content in the organization.

        Args:
            dagster_sigma_translator (Type[DagsterSigmaTranslator]): The translator to use
                to convert Sigma content into AssetSpecs. Defaults to DagsterSigmaTranslator.

        Returns:
            Definitions: The set of assets representing the Sigma content in the organization.
        """
        return Definitions(
            assets=load_sigma_asset_specs(
                self, dagster_sigma_translator, sigma_filter, fetch_column_data
            )
        )


@experimental
def load_sigma_asset_specs(
    organization: SigmaOrganization,
    dagster_sigma_translator: Callable[
        [SigmaOrganizationData], DagsterSigmaTranslator
    ] = DagsterSigmaTranslator,
    sigma_filter: Optional[SigmaFilter] = None,
    fetch_column_data: bool = True,
    snapshot_path: Optional[Union[str, Path]] = None,
) -> Sequence[AssetSpec]:
    """Returns a list of AssetSpecs representing the Sigma content in the organization.

    Args:
        organization (SigmaOrganization): The Sigma organization to fetch assets from.
        dagster_sigma_translator (Callable[[SigmaOrganizationData], DagsterSigmaTranslator]): The translator to use
            to convert Sigma content into AssetSpecs. Defaults to DagsterSigmaTranslator.
        sigma_filter (Optional[SigmaFilter]): Filters the set of Sigma objects to fetch.
        fetch_column_data (bool): Whether to fetch column data for datasets, which can be slow.
        snapshot_path (Optional[Union[str, Path]]): Path to a snapshot file to load Sigma data from,
            rather than fetching it from the Sigma API.

    Returns:
        List[AssetSpec]: The set of assets representing the Sigma content in the organization.
    """
    snapshot = None
    if snapshot_path and not os.getenv(SNAPSHOT_ENV_VAR_NAME):
        snapshot = deserialize_value(Path(snapshot_path).read_text(), RepositoryLoadData)

    with organization.process_config_and_initialize_cm() as initialized_organization:
        return check.is_list(
            SigmaOrganizationDefsLoader(
                organization=initialized_organization,
                translator_cls=dagster_sigma_translator,
                sigma_filter=sigma_filter,
                fetch_column_data=fetch_column_data,
                snapshot=snapshot,
            )
            .build_defs()
            .assets,
            AssetSpec,
        )


def _get_translator_spec_assert_keys_match(
    translator: DagsterSigmaTranslator, data: Union[SigmaDataset, SigmaWorkbook]
) -> AssetSpec:
    key = translator.get_asset_key(data)
    spec = translator.get_asset_spec(data)
    if spec.key != key:
        check.invariant(
            spec.key == key,
            f"Key on AssetSpec returned by {translator.__class__.__name__}.get_asset_spec {spec.key} does not match input key {key}",
        )
    return spec


@dataclass
class SigmaOrganizationDefsLoader(StateBackedDefinitionsLoader[SigmaOrganizationData]):
    organization: SigmaOrganization
    translator_cls: Callable[[SigmaOrganizationData], DagsterSigmaTranslator]
    snapshot: Optional[RepositoryLoadData]
    sigma_filter: Optional[SigmaFilter] = None
    fetch_column_data: bool = True

    @property
    def defs_key(self) -> str:
        return f"{SIGMA_RECON_DATA_PREFIX}{self.organization.client_id}"

    def fetch_state(self) -> SigmaOrganizationData:
        if self.snapshot and self.defs_key in self.snapshot.reconstruction_metadata:
            return deserialize_value(self.snapshot.reconstruction_metadata[self.defs_key])  # type: ignore

        return asyncio.run(
            self.organization.build_organization_data(
                sigma_filter=self.sigma_filter, fetch_column_data=self.fetch_column_data
            )
        )

    def defs_from_state(self, state: SigmaOrganizationData) -> Definitions:
        translator = self.translator_cls(state)
        asset_specs = [
            _get_translator_spec_assert_keys_match(translator, obj)
            for obj in [*state.workbooks, *state.datasets]
        ]
        return Definitions(assets=asset_specs)
