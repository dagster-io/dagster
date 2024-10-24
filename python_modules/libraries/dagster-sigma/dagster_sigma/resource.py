import asyncio
import contextlib
import urllib.parse
import warnings
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import (
    AbstractSet,
    Any,
    Callable,
    Concatenate,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
)

import aiohttp
import dagster._check as check
import requests
from aiohttp.client_exceptions import ClientResponseError
from dagster import ConfigurableResource
from dagster._annotations import deprecated, public
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.definitions_load_context import StateBackedDefinitionsLoader
from dagster._record import IHaveNew, record_custom
from dagster._seven import get_arg_names
from dagster._utils.cached_method import CACHED_METHOD_CACHE_FIELD, _make_key
from dagster._utils.log import get_dagster_logger
from pydantic import Field, PrivateAttr
from sqlglot import exp, parse_one
from typing_extensions import Concatenate, ParamSpec

from dagster_sigma.translator import (
    DagsterSigmaTranslator,
    SigmaDataset,
    SigmaOrganizationData,
    SigmaWorkbook,
    _inode_from_url,
)

logger = get_dagster_logger("dagster_sigma")

S = TypeVar("S")
T = TypeVar("T")
T_Callable = TypeVar("T_Callable", bound=Callable)
P = ParamSpec("P")


def _cached_method(method: Callable[Concatenate[S, P], T]) -> Callable[Concatenate[S, P], T]:
    # Cache these once self is first observed to avoid expensive work on each access
    arg_names = None

    def get_canonical_kwargs(*args: P.args, **kwargs: P.kwargs) -> Dict[str, Any]:
        canonical_kwargs = None
        if args:
            # Entering this block introduces about 15% overhead per call
            # See top-level docblock for more details.

            # nonlocal required to bind to variable in enclosing scope
            nonlocal arg_names
            # only create the lookup table on demand to avoid overhead
            # if the cached method is never called with positional arguments
            arg_names = arg_names if arg_names is not None else get_arg_names(method)[1:]

            translated_kwargs = {}
            for arg_ordinal, arg_value in enumerate(args):
                arg_name = arg_names[arg_ordinal]
                translated_kwargs[arg_name] = arg_value
            if kwargs:
                # only copy if both args and kwargs were passed
                canonical_kwargs = {**translated_kwargs, **kwargs}
            else:
                # no copy
                canonical_kwargs = translated_kwargs
        else:
            # no copy
            canonical_kwargs = kwargs

        return canonical_kwargs

    if asyncio.iscoroutinefunction(method):

        @wraps(method)
        async def _async_cached_method_wrapper(self: S, *args: P.args, **kwargs: P.kwargs) -> T:
            if not hasattr(self, CACHED_METHOD_CACHE_FIELD):
                setattr(self, CACHED_METHOD_CACHE_FIELD, {})

            cache_dict = getattr(self, CACHED_METHOD_CACHE_FIELD)
            if method.__name__ not in cache_dict:
                cache_dict[method.__name__] = {}

            cache = cache_dict[method.__name__]

            canonical_kwargs = get_canonical_kwargs(*args, **kwargs)
            key = _make_key(canonical_kwargs)

            if key not in cache:
                result = await method(self, *args, **kwargs)
                cache[key] = result
            return cache[key]

        return cast(Callable[Concatenate[S, P], T], _async_cached_method_wrapper)

    else:

        @wraps(method)
        def _cached_method_wrapper(self: S, *args: P.args, **kwargs: P.kwargs) -> T:
            if not hasattr(self, CACHED_METHOD_CACHE_FIELD):
                setattr(self, CACHED_METHOD_CACHE_FIELD, {})

            cache_dict = getattr(self, CACHED_METHOD_CACHE_FIELD)
            if method.__name__ not in cache_dict:
                cache_dict[method.__name__] = {}

            cache = cache_dict[method.__name__]

            canonical_kwargs = get_canonical_kwargs(*args, **kwargs)
            key = _make_key(canonical_kwargs)
            if key not in cache:
                result = method(self, *args, **kwargs)
                cache[key] = result
            return cache[key]

        return _cached_method_wrapper


SIGMA_PARTNER_ID_TAG = {"X-Sigma-Partner-Id": "dagster"}


@record_custom
class SigmaFilter(IHaveNew):
    """Filters the set of Sigma objects to fetch.

    Args:
        workbook_folders (Optional[Sequence[Sequence[str]]]): A list of folder paths to fetch workbooks from.
            Each folder path is a list of folder names, starting from the root folder. All workbooks
            contained in the specified folders will be fetched. If not provided, all workbooks will be fetched.
    """

    workbook_folders: Optional[Sequence[Sequence[str]]] = None

    def __new__(cls, workbook_folders: Optional[Sequence[Sequence[str]]] = None):
        return super().__new__(
            cls, workbook_folders=tuple([tuple(folder) for folder in workbook_folders or []])
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
        query_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/v2/{endpoint}"
        if query_params:
            url = f"{url}?{urllib.parse.urlencode(query_params)}"

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=f"{self.base_url}/v2/{endpoint}",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self.api_token}",
                    **SIGMA_PARTNER_ID_TAG,
                },
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def _fetch_json_async_paginated_entries(
        self, endpoint: str, query_params: Optional[Dict[str, Any]] = None, limit: int = 1000
    ) -> List[Dict[str, Any]]:
        entries = []

        query_params_with_limit = {
            **(query_params or {}),
            "limit": limit,
        }
        result = await self._fetch_json_async(endpoint, query_params=query_params)
        entries.extend(result["entries"])

        while result.get("hasMore"):
            next_page = result["nextPage"]
            query_params_with_limit_and_page = {
                **query_params_with_limit,
                "page": next_page,
            }
            result = await self._fetch_json_async(
                endpoint, query_params=query_params_with_limit_and_page
            )
            entries.extend(result["entries"])

        return entries

    @_cached_method
    async def _fetch_workbooks(self) -> List[Dict[str, Any]]:
        return await self._fetch_json_async_paginated_entries("workbooks")

    @_cached_method
    async def _fetch_datasets(self) -> List[Dict[str, Any]]:
        return await self._fetch_json_async_paginated_entries("datasets")

    @_cached_method
    async def _fetch_pages_for_workbook(self, workbook_id: str) -> List[Dict[str, Any]]:
        return await self._fetch_json_async_paginated_entries(f"workbooks/{workbook_id}/pages")

    @_cached_method
    async def _fetch_elements_for_page(
        self, workbook_id: str, page_id: str
    ) -> List[Dict[str, Any]]:
        return await self._fetch_json_async_paginated_entries(
            f"workbooks/{workbook_id}/pages/{page_id}/elements"
        )

    @_cached_method
    async def _fetch_lineage_for_element(self, workbook_id: str, element_id: str) -> Dict[str, Any]:
        return await self._fetch_json_async(
            f"workbooks/{workbook_id}/lineage/elements/{element_id}"
        )

    @_cached_method
    async def _fetch_columns_for_element(
        self, workbook_id: str, element_id: str
    ) -> List[Dict[str, Any]]:
        return (
            await self._fetch_json_async(f"workbooks/{workbook_id}/elements/{element_id}/columns")
        )["entries"]

    @_cached_method
    async def _fetch_queries_for_workbook(self, workbook_id: str) -> List[Dict[str, Any]]:
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

    @_cached_method
    async def _fetch_dataset_upstreams_by_inode(self) -> Mapping[str, AbstractSet[str]]:
        """Builds a mapping of dataset inodes to the upstream inputs they depend on.
        Sigma does not expose this information directly, so we have to infer it from
        the lineage of workbooks and the workbook queries.
        """
        deps_by_dataset_inode = defaultdict(set)

        logger.debug("Fetching dataset dependencies")

        raw_workbooks = await self._fetch_workbooks()

        async def process_workbook(workbook: Dict[str, Any]) -> None:
            logger.debug("Inferring dataset dependencies for workbook %s", workbook["workbookId"])
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

            async def build_deps_from_element(element: Dict[str, Any]) -> None:
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

    @_cached_method
    async def _fetch_dataset_columns_by_inode(self) -> Mapping[str, AbstractSet[str]]:
        """Builds a mapping of dataset inodes to the columns they contain. Note that
        this is a partial list and will only include columns which are referenced in
        workbooks, since Sigma does not expose a direct API for querying dataset columns.
        """
        columns_by_dataset_inode = defaultdict(set)

        workbooks = await self._fetch_workbooks()

        async def process_workbook(workbook: Dict[str, Any]) -> None:
            logger.debug("Fetching column data from workbook %s", workbook["workbookId"])
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

    @_cached_method
    async def build_member_id_to_email_mapping(self) -> Mapping[str, str]:
        """Retrieves all members in the Sigma organization and builds a mapping
        from member ID to email address.
        """
        members = (await self._fetch_json_async("members", query_params={"limit": 500}))["entries"]
        return {member["memberId"]: member["email"] for member in members}

    async def load_workbook_data(self, raw_workbook_data: Dict[str, Any]) -> SigmaWorkbook:
        workbook_deps = set()

        logger.debug("Fetching data for workbook %s", raw_workbook_data["workbookId"])

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
        ) -> Dict[str, Any]:
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
                    workbook_deps.add(item["nodeId"])

        return SigmaWorkbook(
            properties=raw_workbook_data,
            datasets=workbook_deps,
            owner_email=None,
        )

    @_cached_method
    async def build_organization_data(
        self, sigma_filter: Optional[SigmaFilter], skip_fetch_column_data: bool
    ) -> SigmaOrganizationData:
        """Retrieves all workbooks and datasets in the Sigma organization and builds a
        SigmaOrganizationData object representing the organization's assets.
        """
        _sigma_filter = sigma_filter or SigmaFilter()

        logger.debug("Beginning Sigma organization data fetch")
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

        workbooks: List[SigmaWorkbook] = await asyncio.gather(
            *[self.load_workbook_data(workbook) for workbook in workbooks_to_fetch]
        )

        datasets: List[SigmaDataset] = []
        deps_by_dataset_inode = await self._fetch_dataset_upstreams_by_inode()

        columns_by_dataset_inode = (
            await self._fetch_dataset_columns_by_inode() if not skip_fetch_column_data else {}
        )

        logger.debug("Fetching dataset data")
        for dataset in await self._fetch_datasets():
            inode = _inode_from_url(dataset["url"])
            datasets.append(
                SigmaDataset(
                    properties=dataset,
                    columns=columns_by_dataset_inode.get(inode, set()),
                    inputs=deps_by_dataset_inode[inode],
                )
            )

        return SigmaOrganizationData(workbooks=workbooks, datasets=datasets)

    @public
    @deprecated(
        breaking_version="1.9.0",
        additional_warn_text="Use dagster_sigma.load_sigma_asset_specs instead",
    )
    def build_defs(
        self,
        dagster_sigma_translator: Type[DagsterSigmaTranslator] = DagsterSigmaTranslator,
        sigma_filter: Optional[SigmaFilter] = None,
        skip_fetch_column_data: bool = False,
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
                self, dagster_sigma_translator, sigma_filter, skip_fetch_column_data
            )
        )


def load_sigma_asset_specs(
    organization: SigmaOrganization,
    dagster_sigma_translator: Callable[
        [SigmaOrganizationData], DagsterSigmaTranslator
    ] = DagsterSigmaTranslator,
    sigma_filter: Optional[SigmaFilter] = None,
    skip_fetch_column_data: bool = False,
) -> Sequence[AssetSpec]:
    """Returns a list of AssetSpecs representing the Sigma content in the organization.

    Args:
        organization (SigmaOrganization): The Sigma organization to fetch assets from.

    Returns:
        List[AssetSpec]: The set of assets representing the Sigma content in the organization.
    """
    with organization.process_config_and_initialize_cm() as initialized_organization:
        return check.is_list(
            SigmaOrganizationDefsLoader(
                organization=initialized_organization,
                translator_cls=dagster_sigma_translator,
                sigma_filter=sigma_filter,
                skip_fetch_column_data=skip_fetch_column_data,
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
    sigma_filter: Optional[SigmaFilter] = None
    skip_fetch_column_data: bool = False

    @property
    def defs_key(self) -> str:
        return f"sigma_{self.organization.client_id}"

    def fetch_state(self) -> SigmaOrganizationData:
        return asyncio.run(
            self.organization.build_organization_data(
                sigma_filter=self.sigma_filter, skip_fetch_column_data=self.skip_fetch_column_data
            )
        )

    def defs_from_state(self, state: SigmaOrganizationData) -> Definitions:
        translator = self.translator_cls(state)
        asset_specs = [
            _get_translator_spec_assert_keys_match(translator, obj)
            for obj in [*state.workbooks, *state.datasets]
        ]
        return Definitions(assets=asset_specs)
