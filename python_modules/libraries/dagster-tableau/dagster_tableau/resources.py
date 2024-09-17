import datetime
import uuid
from abc import abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, List, Mapping, Optional, Sequence, Type, Union, cast

import jwt
import requests
from dagster import (
    AssetsDefinition,
    ConfigurableResource,
    Definitions,
    ObserveResult,
    _check as check,
    external_assets_from_specs,
    multi_asset,
)
from dagster._annotations import experimental
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._utils.cached_method import cached_method
from pydantic import Field, PrivateAttr

from dagster_tableau.translator import (
    DagsterTableauTranslator,
    TableauContentData,
    TableauContentType,
    TableauWorkspaceData,
)

TABLEAU_REST_API_VERSION = "3.23"


@experimental
class BaseTableauClient:
    def __init__(
        self,
        connected_app_client_id: str,
        connected_app_secret_id: str,
        connected_app_secret_value: str,
        username: str,
        site_name: str,
    ):
        self.connected_app_client_id = connected_app_client_id
        self.connected_app_secret_id = connected_app_secret_id
        self.connected_app_secret_value = connected_app_secret_value
        self.username = username
        self.site_name = site_name
        self._api_token = None
        self._site_id = None

    @property
    @abstractmethod
    def rest_api_base_url(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def metadata_api_base_url(self) -> str:
        raise NotImplementedError()

    def _fetch_json(
        self,
        url: str,
        data: Optional[Mapping[str, object]] = None,
        method: str = "GET",
        with_auth_header: bool = True,
    ) -> Mapping[str, object]:
        """Fetch JSON data from the Tableau APIs given the URL. Raises an exception if the request fails.

        Args:
            url (str): The url to fetch data from.
            data (Optional[Dict[str, Any]]): JSON-formatted data string to be included in the request.
            method (str): The HTTP method to use for the request.
            with_auth_header (bool): Whether to add X-Tableau-Auth header to the request. Enabled by default.

        Returns:
            Dict[str, Any]: The JSON data returned from the API.
        """
        response = self._make_request(
            url=url, data=data, method=method, with_auth_header=with_auth_header
        )
        return response.json()

    def _make_request(
        self,
        url: str,
        data: Optional[Mapping[str, object]] = None,
        method: str = "GET",
        with_auth_header: bool = True,
    ) -> requests.Response:
        headers: Mapping[str, object] = {
            "accept": "application/json",
            "content-type": "application/json",
        }
        if with_auth_header:
            headers = {**headers, "X-tableau-auth": self._api_token}
        request_args: Dict[str, Any] = dict(
            method=method,
            url=url,
            headers=headers,
        )
        if data:
            request_args = {**request_args, "json": data}
        response = requests.request(**request_args)
        response.raise_for_status()
        return response

    @cached_method
    def get_workbooks(self) -> Mapping[str, object]:
        """Fetches a list of all Tableau workbooks in the workspace."""
        endpoint = self._with_site_id("workbooks")
        return self._fetch_json(url=f"{self.rest_api_base_url}/{endpoint}")

    @cached_method
    def get_workbook(self, workbook_id) -> Mapping[str, object]:
        """Fetches information, including sheets, dashboards and data sources, for a given workbook."""
        data = {"query": self.workbook_graphql_query, "variables": {"luid": workbook_id}}
        return self._fetch_json(url=self.metadata_api_base_url, data=data, method="POST")

    @cached_method
    def get_view(
        self,
        view_id: str,
    ) -> Mapping[str, object]:
        """Fetches information for a given view."""
        endpoint = self._with_site_id(f"views/{view_id}")
        return self._fetch_json(url=f"{self.rest_api_base_url}/{endpoint}")

    def sign_in(self) -> Mapping[str, object]:
        """Sign in to the site in Tableau."""
        jwt_token = jwt.encode(
            {
                "iss": self.connected_app_client_id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
                "jti": str(uuid.uuid4()),
                "aud": "tableau",
                "sub": self.username,
                "scp": ["tableau:content:read"],
            },
            self.connected_app_secret_value,
            algorithm="HS256",
            headers={"kid": self.connected_app_secret_id, "iss": self.connected_app_client_id},
        )
        data = {
            "credentials": {
                "jwt": jwt_token,
                "site": {"contentUrl": self.site_name},
            }
        }
        response = self._fetch_json(
            url=f"{self.rest_api_base_url}/auth/signin",
            data=data,
            method="POST",
            with_auth_header=False,
        )

        response = cast(Dict[str, Any], response)
        self._api_token = response["credentials"]["token"]
        self._site_id = response["credentials"]["site"]["id"]
        return response

    def sign_out(self) -> None:
        """Sign out from the site in Tableau."""
        self._make_request(url=f"{self.rest_api_base_url}/auth/signout", method="POST")
        self._api_token = None
        self._site_id = None

    def _with_site_id(self, endpoint: str) -> str:
        return f"sites/{self._site_id}/{endpoint}"

    @property
    def workbook_graphql_query(self) -> str:
        return """
            query workbooks($luid: String!) { 
              workbooks(filter: {luid: $luid}) {
                luid
                name
                createdAt
                updatedAt
                uri
                sheets {
                  luid
                  name
                  createdAt
                  updatedAt
                  path
                  parentEmbeddedDatasources {
                    parentPublishedDatasources {
                      luid
                      name
                    }
                  }
                }
                dashboards {
                  luid
                  name
                  createdAt
                  updatedAt
                  path
                  sheets {
                    luid
                  }
                }
              }
            }
        """


@experimental
class TableauCloudClient(BaseTableauClient):
    """Represents a client for Tableau Cloud and provides utilities
    to interact with the Tableau API.
    """

    def __init__(
        self,
        connected_app_client_id: str,
        connected_app_secret_id: str,
        connected_app_secret_value: str,
        username: str,
        site_name: str,
        pod_name: str,
    ):
        self.pod_name = pod_name
        super().__init__(
            connected_app_client_id=connected_app_client_id,
            connected_app_secret_id=connected_app_secret_id,
            connected_app_secret_value=connected_app_secret_value,
            username=username,
            site_name=site_name,
        )

    @property
    def rest_api_base_url(self) -> str:
        """REST API base URL for Tableau Cloud."""
        return f"https://{self.pod_name}.online.tableau.com/api/{TABLEAU_REST_API_VERSION}"

    @property
    def metadata_api_base_url(self) -> str:
        """Metadata API base URL for Tableau Cloud."""
        return f"https://{self.pod_name}.online.tableau.com/api/metadata/graphql"


@experimental
class TableauServerClient(BaseTableauClient):
    """Represents a client for Tableau Server and provides utilities
    to interact with Tableau APIs.
    """

    def __init__(
        self,
        connected_app_client_id: str,
        connected_app_secret_id: str,
        connected_app_secret_value: str,
        username: str,
        site_name: str,
        server_name: str,
    ):
        self.server_name = server_name
        super().__init__(
            connected_app_client_id=connected_app_client_id,
            connected_app_secret_id=connected_app_secret_id,
            connected_app_secret_value=connected_app_secret_value,
            username=username,
            site_name=site_name,
        )

    @property
    def rest_api_base_url(self) -> str:
        """REST API base URL for Tableau Server."""
        return f"https://{self.server_name}/api/{TABLEAU_REST_API_VERSION}"

    @property
    def metadata_api_base_url(self) -> str:
        """Metadata API base URL for Tableau Server."""
        return f"https://{self.server_name}/api/metadata/graphql"


@experimental
class BaseTableauWorkspace(ConfigurableResource):
    """Base class to represent a workspace in Tableau and provides utilities
    to interact with Tableau APIs.
    """

    connected_app_client_id: str = Field(
        ..., description="The client id of the connected app used to connect to Tableau Workspace."
    )
    connected_app_secret_id: str = Field(
        ..., description="The secret id of the connected app used to connect to Tableau Workspace."
    )
    connected_app_secret_value: str = Field(
        ...,
        description="The secret value of the connected app used to connect to Tableau Workspace.",
    )
    username: str = Field(..., description="The username to authenticate to Tableau Workspace.")
    site_name: str = Field(..., description="The name of the Tableau site to use.")

    _client: Optional[Union[TableauCloudClient, TableauServerClient]] = PrivateAttr(default=None)

    @abstractmethod
    def build_client(self) -> None:
        raise NotImplementedError()

    @contextmanager
    def get_client(self):
        if not self._client:
            self.build_client()
        self._client.sign_in()
        try:
            yield self._client
        finally:
            self._client.sign_out()

    def fetch_tableau_workspace_data(
        self,
    ) -> TableauWorkspaceData:
        """Retrieves all Tableau content from the workspace and returns it as a TableauWorkspaceData object.
        Future work will cache this data to avoid repeated calls to the Tableau API.

        Returns:
            TableauWorkspaceData: A snapshot of the Tableau workspace's content.
        """
        with self.get_client() as client:
            workbooks_data = client.get_workbooks()["workbooks"]
            workbook_ids = [workbook["id"] for workbook in workbooks_data["workbook"]]

            workbooks_by_id = {}
            sheets_by_id = {}
            dashboards_by_id = {}
            data_sources_by_id = {}
            for workbook_id in workbook_ids:
                workbook_data = client.get_workbook(workbook_id=workbook_id)["data"]["workbooks"][0]
                workbooks_by_id[workbook_id] = TableauContentData(
                    content_type=TableauContentType.WORKBOOK, properties=workbook_data
                )

                for sheet_data in workbook_data["sheets"]:
                    sheet_id = sheet_data["luid"]
                    if sheet_id:
                        augmented_sheet_data = {**sheet_data, "workbook": {"luid": workbook_id}}
                        sheets_by_id[sheet_id] = TableauContentData(
                            content_type=TableauContentType.SHEET, properties=augmented_sheet_data
                        )

                    for embedded_data_source_data in sheet_data.get(
                        "parentEmbeddedDatasources", []
                    ):
                        for published_data_source_data in embedded_data_source_data.get(
                            "parentPublishedDatasources", []
                        ):
                            data_source_id = published_data_source_data["luid"]
                            if data_source_id and data_source_id not in data_sources_by_id:
                                data_sources_by_id[data_source_id] = TableauContentData(
                                    content_type=TableauContentType.DATA_SOURCE,
                                    properties=published_data_source_data,
                                )

                for dashboard_data in workbook_data["dashboards"]:
                    dashboard_id = dashboard_data["luid"]
                    if dashboard_id:
                        augmented_dashboard_data = {
                            **dashboard_data,
                            "workbook": {"luid": workbook_id},
                        }
                        dashboards_by_id[dashboard_id] = TableauContentData(
                            content_type=TableauContentType.DASHBOARD,
                            properties=augmented_dashboard_data,
                        )

        return TableauWorkspaceData.from_content_data(
            self.site_name,
            list(workbooks_by_id.values())
            + list(sheets_by_id.values())
            + list(dashboards_by_id.values())
            + list(data_sources_by_id.values()),
        )

    def build_assets(
        self,
        dagster_tableau_translator: Type[DagsterTableauTranslator],
    ) -> Sequence[CacheableAssetsDefinition]:
        """Returns a set of CacheableAssetsDefinition which will load Tableau content from
        the workspace and translates it into AssetSpecs, using the provided translator.

        Args:
            dagster_tableau_translator (Type[DagsterTableauTranslator]): The translator to use
                to convert Tableau content into AssetSpecs. Defaults to DagsterTableauTranslator.

        Returns:
            Sequence[CacheableAssetsDefinition]: A list of CacheableAssetsDefinitions which
                will load the Tableau content.
        """
        return [TableauCacheableAssetsDefinition(self, dagster_tableau_translator)]

    def build_defs(
        self, dagster_tableau_translator: Type[DagsterTableauTranslator] = DagsterTableauTranslator
    ) -> Definitions:
        """Returns a Definitions object which will load Tableau content from
        the workspace and translate it into assets, using the provided translator.

        Args:
            dagster_tableau_translator (Type[DagsterTableauTranslator]): The translator to use
                to convert Tableau content into AssetSpecs. Defaults to DagsterTableauTranslator.

        Returns:
            Definitions: A Definitions object which will build and return the Power BI content.
        """
        defs = Definitions(
            assets=self.build_assets(dagster_tableau_translator=dagster_tableau_translator)
        )
        return defs


@experimental
class TableauCloudWorkspace(BaseTableauWorkspace):
    """Represents a workspace in Tableau Cloud and provides utilities
    to interact with Tableau APIs.
    """

    pod_name: str = Field(..., description="The pod name of the Tableau Cloud workspace.")

    def build_client(self) -> None:
        self._client = TableauCloudClient(
            connected_app_client_id=self.connected_app_client_id,
            connected_app_secret_id=self.connected_app_secret_id,
            connected_app_secret_value=self.connected_app_secret_value,
            username=self.username,
            site_name=self.site_name,
            pod_name=self.pod_name,
        )


@experimental
class TableauServerWorkspace(BaseTableauWorkspace):
    """Represents a workspace in Tableau Server and provides utilities
    to interact with Tableau APIs.
    """

    server_name: str = Field(..., description="The server name of the Tableau Server workspace.")

    def build_client(self) -> None:
        self._client = TableauServerClient(
            connected_app_client_id=self.connected_app_client_id,
            connected_app_secret_id=self.connected_app_secret_id,
            connected_app_secret_value=self.connected_app_secret_value,
            username=self.username,
            site_name=self.site_name,
            server_name=self.server_name,
        )


class TableauCacheableAssetsDefinition(CacheableAssetsDefinition):
    def __init__(self, workspace: BaseTableauWorkspace, translator: Type[DagsterTableauTranslator]):
        self._workspace = workspace
        self._translator_cls = translator
        super().__init__(unique_id=self._workspace.site_name)

    def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:
        workspace_data: TableauWorkspaceData = self._workspace.fetch_tableau_workspace_data()
        return [
            AssetsDefinitionCacheableData(extra_metadata=data.to_cached_data())
            for data in [
                *workspace_data.workbooks_by_id.values(),
                *workspace_data.sheets_by_id.values(),
                *workspace_data.dashboards_by_id.values(),
                *workspace_data.data_sources_by_id.values(),
            ]
        ]

    def build_definitions(
        self, data: Sequence[AssetsDefinitionCacheableData]
    ) -> Sequence[AssetsDefinition]:
        workspace_data = TableauWorkspaceData.from_content_data(
            self._workspace.site_name,
            [
                TableauContentData.from_cached_data(check.not_none(entry.extra_metadata))
                for entry in data
            ],
        )

        translator = self._translator_cls(context=workspace_data)

        external_assets = external_assets_from_specs(
            [
                translator.get_asset_spec(content)
                for content in workspace_data.data_sources_by_id.values()
            ]
        )

        tableau_assets = self._build_tableau_assets_from_workspace_data(
            workspace_data=workspace_data,
            translator=translator,
        )

        return external_assets + tableau_assets

    def _build_tableau_assets_from_workspace_data(
        self,
        workspace_data: TableauWorkspaceData,
        translator: DagsterTableauTranslator,
    ) -> List[AssetsDefinition]:
        @multi_asset(
            name=f"tableau_sync_site_{self._workspace.site_name.replace('-', '_')}",
            compute_kind="tableau",
            can_subset=False,
            specs=[
                translator.get_asset_spec(content)
                for content in [
                    *workspace_data.sheets_by_id.values(),
                    *workspace_data.dashboards_by_id.values(),
                ]
            ],
            resource_defs={"tableau": self._workspace.get_resource_definition()},
        )
        def _assets(tableau: BaseTableauWorkspace):
            with tableau.get_client() as client:
                for view_id, view_content_data in [
                    *workspace_data.sheets_by_id.items(),
                    *workspace_data.dashboards_by_id.items(),
                ]:
                    data = client.get_view(view_id)["view"]
                    if view_content_data.content_type == TableauContentType.SHEET:
                        asset_key = translator.get_sheet_asset_key(view_content_data)
                    elif view_content_data.content_type == TableauContentType.DASHBOARD:
                        asset_key = translator.get_dashboard_asset_key(view_content_data)
                    else:
                        check.assert_never(view_content_data.content_type)
                    yield ObserveResult(
                        asset_key=asset_key,
                        metadata={
                            "workbook_id": data["workbook"]["id"],
                            "owner_id": data["owner"]["id"],
                            "name": data["name"],
                            "contentUrl": data["contentUrl"],
                            "createdAt": data["createdAt"],
                            "updatedAt": data["updatedAt"],
                        },
                    )

        return [_assets]
