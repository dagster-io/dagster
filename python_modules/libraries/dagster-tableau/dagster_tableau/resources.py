import datetime
import json
import uuid
from abc import abstractmethod
from contextlib import contextmanager
from typing import Any, List, Mapping, Optional, Sequence, Type, Union

import jwt
import requests
import tableauserverclient as TSC
import xmltodict
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
from dagster._core.definitions.definitions_load_context import StateBackedDefinitionsLoader
from dagster._record import record
from dagster._utils.cached_method import cached_method
from pydantic import Field, PrivateAttr
from tableauserverclient.server.endpoint.auth_endpoint import Auth

from dagster_tableau.translator import (
    DagsterTableauTranslator,
    TableauContentData,
    TableauContentType,
    TableauWorkspaceData,
)

TABLEAU_RECONSTRUCTION_METADATA_KEY_PREFIX = "dagster-tableau/reconstruction_metadata"


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
        self._server = TSC.Server(self.base_url)
        self._server.use_server_version()

    @property
    @abstractmethod
    def base_url(self) -> str:
        raise NotImplementedError()

    @cached_method
    def get_workbooks(self) -> Mapping[str, object]:
        """Fetches a list of all Tableau workbooks in the workspace."""
        return self._response_to_dict(
            self._server.workbooks.get_request(self._server.workbooks.baseurl)
        )

    @cached_method
    def get_workbook(self, workbook_id) -> Mapping[str, object]:
        """Fetches information, including sheets, dashboards and data sources, for a given workbook."""
        return self._server.metadata.query(
            query=self.workbook_graphql_query, variables={"luid": workbook_id}
        )

    @cached_method
    def get_view(
        self,
        view_id: str,
    ) -> Mapping[str, object]:
        """Fetches information for a given view."""
        return self._response_to_dict(
            self._server.views.get_request(f"{self._server.views.baseurl}/{view_id}")
        )

    def sign_in(self) -> Auth.contextmgr:
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

        tableau_auth = TSC.JWTAuth(jwt_token, site_id=self.site_name)  # pyright: ignore (reportAttributeAccessIssue)
        return self._server.auth.sign_in(tableau_auth)

    @staticmethod
    def _response_to_dict(response: requests.Response):
        return json.loads(
            json.dumps(xmltodict.parse(response.text, attr_prefix="", cdata_key="")["tsResponse"])
        )

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
    def base_url(self) -> str:
        """Base URL for Tableau Cloud."""
        return f"https://{self.pod_name}.online.tableau.com"


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
    def base_url(self) -> str:
        """Base URL for Tableau Cloud."""
        return f"https://{self.server_name}"


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
        with self._client.sign_in():
            yield self._client

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
        return TableauDefsLoader(
            workspace=self, translator_cls=dagster_tableau_translator
        ).build_defs()


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


@record
class TableauDefsLoader(StateBackedDefinitionsLoader[Mapping[str, Any]]):
    workspace: BaseTableauWorkspace
    translator_cls: Type[DagsterTableauTranslator]

    @property
    def defs_key(self) -> str:
        return f"{TABLEAU_RECONSTRUCTION_METADATA_KEY_PREFIX}/{self.workspace.site_name}"

    def fetch_state(self) -> Sequence[Mapping[str, Any]]:
        workspace_data: TableauWorkspaceData = self.workspace.fetch_tableau_workspace_data()
        return [
            data.to_cached_data()
            for data in [
                *workspace_data.workbooks_by_id.values(),
                *workspace_data.sheets_by_id.values(),
                *workspace_data.dashboards_by_id.values(),
                *workspace_data.data_sources_by_id.values(),
            ]
        ]

    def defs_from_state(self, state: Sequence[Mapping[str, Any]]) -> Definitions:
        workspace_data = TableauWorkspaceData.from_content_data(
            self.workspace.site_name,
            [TableauContentData.from_cached_data(check.not_none(entry)) for entry in state],
        )

        translator = self.translator_cls(context=workspace_data)

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

        return Definitions(assets=external_assets + tableau_assets)

    def _build_tableau_assets_from_workspace_data(
        self,
        workspace_data: TableauWorkspaceData,
        translator: DagsterTableauTranslator,
    ) -> List[AssetsDefinition]:
        @multi_asset(
            name=f"tableau_sync_site_{self.workspace.site_name.replace('-', '_')}",
            compute_kind="tableau",
            can_subset=False,
            specs=[
                translator.get_asset_spec(content)
                for content in [
                    *workspace_data.sheets_by_id.values(),
                    *workspace_data.dashboards_by_id.values(),
                ]
            ],
            resource_defs={"tableau": self.workspace.get_resource_definition()},
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
