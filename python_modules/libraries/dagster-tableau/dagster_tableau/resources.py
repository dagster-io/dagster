import datetime
import logging
import time
import uuid
from abc import abstractmethod
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import Any, Optional, Union

import jwt
import requests
import tableauserverclient as TSC
from dagster import (
    AssetSpec,
    ConfigurableResource,
    Definitions,
    Failure,
    ObserveResult,
    Output,
    _check as check,
    get_dagster_logger,
)
from dagster._annotations import beta, deprecated
from dagster._core.definitions.definitions_load_context import StateBackedDefinitionsLoader
from dagster._record import record
from dagster._utils.cached_method import cached_method
from dagster._utils.warnings import deprecation_warning
from pydantic import Field, PrivateAttr
from tableauserverclient.server.endpoint.auth_endpoint import Auth

from dagster_tableau.translator import (
    DagsterTableauTranslator,
    TableauContentData,
    TableauContentType,
    TableauMetadataSet,
    TableauTagSet,
    TableauTranslatorData,
    TableauWorkspaceData,
)

DEFAULT_POLL_INTERVAL_SECONDS = 10
DEFAULT_POLL_TIMEOUT = 600

TABLEAU_RECONSTRUCTION_METADATA_KEY_PREFIX = "dagster-tableau/reconstruction_metadata"


@beta
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

    @property
    @cached_method
    def _log(self) -> logging.Logger:
        return get_dagster_logger()

    @cached_method
    def get_workbooks(self) -> list[TSC.WorkbookItem]:
        """Fetches a list of all Tableau workbooks in the workspace."""
        workbooks, _ = self._server.workbooks.get()
        return workbooks

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
    ) -> TSC.ViewItem:
        """Fetches information for a given view."""
        return self._server.views.get_by_id(view_id)

    def get_job(
        self,
        job_id: str,
    ) -> TSC.JobItem:
        """Fetches information for a given job."""
        return self._server.jobs.get_by_id(job_id)

    def cancel_job(
        self,
        job_id: str,
    ) -> requests.Response:
        """Cancels a given job."""
        return self._server.jobs.cancel(job_id)

    def refresh_and_materialize_workbooks(
        self, specs: Sequence[AssetSpec], refreshable_workbook_ids: Optional[Sequence[str]]
    ):
        """Refreshes workbooks for the given workbook IDs and materializes workbook views given the asset specs."""
        refreshed_workbooks = set()
        for refreshable_workbook_id in refreshable_workbook_ids or []:
            refreshed_workbooks.add(self.refresh_and_poll(refreshable_workbook_id))
        for spec in specs:
            view_id = check.inst(TableauMetadataSet.extract(spec.metadata).id, str)
            data = self.get_view(view_id)
            asset_key = spec.key
            workbook_id = TableauMetadataSet.extract(spec.metadata).workbook_id
            if workbook_id and workbook_id in refreshed_workbooks:
                yield Output(
                    value=None,
                    output_name="__".join(asset_key.path),
                    metadata={
                        "workbook_id": data.workbook_id,
                        "owner_id": data.owner_id,
                        "name": data.name,
                        "contentUrl": data.content_url,
                        "createdAt": data.created_at.strftime("%Y-%m-%dT%H:%M:%S")
                        if data.created_at
                        else None,
                        "updatedAt": data.updated_at.strftime("%Y-%m-%dT%H:%M:%S")
                        if data.updated_at
                        else None,
                    },
                )
            else:
                yield ObserveResult(
                    asset_key=asset_key,
                    metadata={
                        "workbook_id": data.workbook_id,
                        "owner_id": data.owner_id,
                        "name": data.name,
                        "contentUrl": data.content_url,
                        "createdAt": data.created_at.strftime("%Y-%m-%dT%H:%M:%S")
                        if data.created_at
                        else None,
                        "updatedAt": data.updated_at.strftime("%Y-%m-%dT%H:%M:%S")
                        if data.updated_at
                        else None,
                    },
                )

    def refresh_workbook(self, workbook_id) -> TSC.JobItem:
        """Refreshes all extracts for a given workbook and return the JobItem object."""
        return self._server.workbooks.refresh(workbook_id)

    def refresh_and_poll(
        self,
        workbook_id: str,
        poll_interval: Optional[float] = None,
        poll_timeout: Optional[float] = None,
    ) -> Optional[str]:
        job = self.refresh_workbook(workbook_id)

        if not poll_interval:
            poll_interval = DEFAULT_POLL_INTERVAL_SECONDS
        if not poll_timeout:
            poll_timeout = DEFAULT_POLL_TIMEOUT

        self._log.info(f"Job {job.id} initialized for workbook_id={workbook_id}.")
        start = time.monotonic()

        try:
            while True:
                if poll_timeout and start + poll_timeout < time.monotonic():
                    raise Failure(
                        f"Timeout: Tableau job {job.id} is not ready after the timeout"
                        f" {poll_timeout} seconds"
                    )
                time.sleep(poll_interval)
                job = self.get_job(job_id=job.id)

                if job.finish_code == -1:
                    # -1 is the default value for JobItem.finish_code, when the job is in progress
                    continue
                elif job.finish_code == TSC.JobItem.FinishCode.Success:
                    break
                elif job.finish_code == TSC.JobItem.FinishCode.Failed:
                    raise Failure(f"Job failed: {job.id}")
                elif job.finish_code == TSC.JobItem.FinishCode.Cancelled:
                    raise Failure(f"Job was cancelled: {job.id}")
                else:
                    raise Failure(
                        f"Encountered unexpected finish code `{job.finish_code}` for job {job.id}"
                    )
        finally:
            # if Tableau sync has not completed, make sure to cancel it so that it doesn't outlive
            # the python process
            if job.finish_code not in (
                TSC.JobItem.FinishCode.Success,
                TSC.JobItem.FinishCode.Failed,
                TSC.JobItem.FinishCode.Cancelled,
            ):
                self.cancel_job(job.id)

        return job.workbook_id

    def add_data_quality_warning_to_data_source(
        self,
        data_source_id: str,
        warning_type: Optional[TSC.DQWItem.WarningType] = None,
        message: Optional[str] = None,
        active: Optional[bool] = None,
        severe: Optional[bool] = None,
    ) -> Sequence[TSC.DQWItem]:
        """Add a data quality warning to a data source.

        Args:
            data_source_id (str): The ID of the data source for which a data quality warning is to be added.
            warning_type (Optional[tableauserverclient.DQWItem.WarningType]): The warning type
                for the data quality warning. Defaults to `TSC.DQWItem.WarningType.WARNING`.
            message (Optional[str]): The message for the data quality warning. Defaults to `None`.
            active (Optional[bool]): Whether the data quality warning is active or not. Defaults to `True`.
            severe (Optional[bool]): Whether the data quality warning is sever or not. Defaults to `False`.

        Returns:
            Sequence[tableauserverclient.DQWItem]: The list of tableauserverclient.DQWItems which
                exist for the data source.
        """
        data_source: TSC.DatasourceItem = self._server.datasources.get_by_id(
            datasource_id=data_source_id
        )
        warning: TSC.DQWItem = TSC.DQWItem(
            warning_type=str(warning_type) or TSC.DQWItem.WarningType.WARNING,
            message=message,
            active=active or True,
            severe=severe or False,
        )
        return self._server.datasources.add_dqw(item=data_source, warning=warning)

    def sign_in(self) -> Auth.contextmgr:
        """Sign in to the site in Tableau."""
        jwt_token = jwt.encode(
            {
                "iss": self.connected_app_client_id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
                "jti": str(uuid.uuid4()),
                "aud": "tableau",
                "sub": self.username,
                "scp": ["tableau:content:read", "tableau:tasks:run"],
            },
            self.connected_app_secret_value,
            algorithm="HS256",
            headers={"kid": self.connected_app_secret_id, "iss": self.connected_app_client_id},
        )

        tableau_auth = TSC.JWTAuth(jwt_token, site_id=self.site_name)
        return self._server.auth.sign_in(tableau_auth)

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
                    id
                    name
                    hasExtracts
                    upstreamTables {
                        id
                        name
                        connectionType
                        schema
                        isEmbedded
                        tableType
                        fullName
                        projectName
                        database {
                            id
                            name
                            projectName
                        }
                    }   
                    parentPublishedDatasources {
                        luid
                        name
                        id
                        name
                        hasExtracts
                        upstreamTables {
                            name
                            fullName
                            connectionType
                            schema
                            database {
                                id
                                name
                                projectName
                            }
                        }
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


@beta
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


@beta
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


@beta
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
    def get_client(self) -> Iterator[Union[TableauCloudClient, TableauServerClient]]:
        if not self._client:
            self.build_client()

        client = check.not_none(self._client, "build_client failed to set _client")
        with client.sign_in():
            yield client

    def fetch_tableau_workspace_data(
        self,
    ) -> TableauWorkspaceData:
        """Retrieves all Tableau content from the workspace and returns it as a TableauWorkspaceData object.
        Future work will cache this data to avoid repeated calls to the Tableau API.

        Returns:
            TableauWorkspaceData: A snapshot of the Tableau workspace's content.
        """
        with self.get_client() as client:
            workbook_ids = [workbook.id for workbook in client.get_workbooks()]

            workbooks: list[TableauContentData] = []
            sheets: list[TableauContentData] = []
            dashboards: list[TableauContentData] = []
            data_sources: list[TableauContentData] = []
            data_source_ids: set[str] = set()
            for workbook_id in workbook_ids:
                workbook = client.get_workbook(workbook_id=workbook_id)
                workbook_data_list = check.is_list(
                    workbook["data"]["workbooks"],  # pyright: ignore[reportIndexIssue]
                    additional_message=f"Invalid data for Tableau workbook for id {workbook_id}.",
                )
                if not workbook_data_list:
                    raise Exception(
                        f"Could not retrieve data for Tableau workbook for id {workbook_id}."
                    )
                workbook_data = workbook_data_list[0]
                workbooks.append(
                    TableauContentData(
                        content_type=TableauContentType.WORKBOOK, properties=workbook_data
                    )
                )

                for sheet_data in workbook_data["sheets"]:
                    sheet_id = sheet_data["luid"]
                    if sheet_id:
                        augmented_sheet_data = {**sheet_data, "workbook": {"luid": workbook_id}}
                        sheets.append(
                            TableauContentData(
                                content_type=TableauContentType.SHEET,
                                properties=augmented_sheet_data,
                            )
                        )
                    """
                    Lineage formation depends on the availability of published data sources.
                    If published data sources are available (i.e., parentPublishedDatasources exists and is not empty), it means you can form the lineage by using the luid of those published sources.
                    If the published data sources are missing, you create assets for embedded data sources by using their id.
                    """
                    for embedded_data_source_data in sheet_data.get(
                        "parentEmbeddedDatasources", []
                    ):
                        published_data_source_list = embedded_data_source_data.get(
                            "parentPublishedDatasources", []
                        )
                        for published_data_source_data in published_data_source_list:
                            data_source_id = published_data_source_data["luid"]
                            if data_source_id and data_source_id not in data_source_ids:
                                data_source_ids.add(data_source_id)
                                data_sources.append(
                                    TableauContentData(
                                        content_type=TableauContentType.DATA_SOURCE,
                                        properties=published_data_source_data,
                                    )
                                )
                        if not published_data_source_list:
                            """While creating TableauWorkspaceData luid is mandatory for all TableauContentData
                            and in case of embedded_data_source its missing hence we are using its id as luid"""
                            data_source_id = embedded_data_source_data["id"]
                            if data_source_id and data_source_id not in data_source_ids:
                                data_source_ids.add(data_source_id)
                                embedded_data_source_data["luid"] = data_source_id
                                data_sources.append(
                                    TableauContentData(
                                        content_type=TableauContentType.DATA_SOURCE,
                                        properties=embedded_data_source_data,
                                    )
                                )

                for dashboard_data in workbook_data["dashboards"]:
                    dashboard_id = dashboard_data["luid"]
                    if dashboard_id:
                        augmented_dashboard_data = {
                            **dashboard_data,
                            "workbook": {"luid": workbook_id},
                        }
                        dashboards.append(
                            TableauContentData(
                                content_type=TableauContentType.DASHBOARD,
                                properties=augmented_dashboard_data,
                            )
                        )

        return TableauWorkspaceData.from_content_data(
            self.site_name,
            workbooks + sheets + dashboards + data_sources,
        )

    @deprecated(
        breaking_version="1.9.0",
        additional_warn_text="Use dagster_tableau.load_tableau_asset_specs instead",
    )
    def build_defs(
        self,
        refreshable_workbook_ids: Optional[Sequence[str]] = None,
        dagster_tableau_translator: type[DagsterTableauTranslator] = DagsterTableauTranslator,
    ) -> Definitions:
        """Returns a Definitions object which will load Tableau content from
        the workspace and translate it into assets, using the provided translator.

        Args:
            refreshable_workbook_ids (Optional[Sequence[str]]): A list of workbook IDs. The workbooks provided must
                have extracts as data sources and be refreshable in Tableau.

                When materializing your Tableau assets, the workbooks provided are refreshed,
                refreshing their sheets and dashboards before pulling their data in Dagster.

                This feature is equivalent to selecting Refreshing Extracts for a workbook in Tableau UI
                and only works for workbooks for which the data sources are extracts.
                See https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_workbooks_and_views.htm#update_workbook_now
                for documentation.
            dagster_tableau_translator (Type[DagsterTableauTranslator]): The translator to use
                to convert Tableau content into AssetSpecs. Defaults to DagsterTableauTranslator.

        Returns:
            Definitions: A Definitions object which will build and return the Power BI content.
        """
        from dagster_tableau.assets import build_tableau_materializable_assets_definition

        resource_key = "tableau"

        asset_specs = load_tableau_asset_specs(self, dagster_tableau_translator())

        non_executable_asset_specs = [
            spec
            for spec in asset_specs
            if TableauTagSet.extract(spec.tags).asset_type == "data_source"
        ]

        executable_asset_specs = [
            spec
            for spec in asset_specs
            if TableauTagSet.extract(spec.tags).asset_type in ["dashboard", "sheet"]
        ]

        return Definitions(
            assets=[
                build_tableau_materializable_assets_definition(
                    resource_key=resource_key,
                    specs=executable_asset_specs,
                    refreshable_workbook_ids=refreshable_workbook_ids,
                ),
                *non_executable_asset_specs,
            ],
            resources={resource_key: self},
        )


@beta
def load_tableau_asset_specs(
    workspace: BaseTableauWorkspace,
    dagster_tableau_translator: Optional[
        Union[DagsterTableauTranslator, type[DagsterTableauTranslator]]
    ] = None,
) -> Sequence[AssetSpec]:
    """Returns a list of AssetSpecs representing the Tableau content in the workspace.

    Args:
        workspace (Union[TableauCloudWorkspace, TableauServerWorkspace]): The Tableau workspace to fetch assets from.
        dagster_tableau_translator (Optional[Union[DagsterTableauTranslator, Type[DagsterTableauTranslator]]]):
            The translator to use to convert Tableau content into :py:class:`dagster.AssetSpec`.
            Defaults to :py:class:`DagsterTableauTranslator`.

    Returns:
        List[AssetSpec]: The set of assets representing the Tableau content in the workspace.
    """
    if isinstance(dagster_tableau_translator, type):
        deprecation_warning(
            subject="Support of `dagster_tableau_translator` as a Type[DagsterTableauTranslator]",
            breaking_version="1.10",
            additional_warn_text=(
                "Pass an instance of DagsterTableauTranslator or subclass to `dagster_tableau_translator` instead."
            ),
        )
        dagster_tableau_translator = dagster_tableau_translator()

    with workspace.process_config_and_initialize_cm() as initialized_workspace:
        return check.is_list(
            TableauWorkspaceDefsLoader(
                workspace=initialized_workspace,
                translator=dagster_tableau_translator or DagsterTableauTranslator(),
            )
            .build_defs()
            .assets,
            AssetSpec,
        )


@beta
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


@beta
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
class TableauWorkspaceDefsLoader(StateBackedDefinitionsLoader[Mapping[str, Any]]):
    workspace: BaseTableauWorkspace
    translator: DagsterTableauTranslator

    @property
    def defs_key(self) -> str:
        return f"{TABLEAU_RECONSTRUCTION_METADATA_KEY_PREFIX}/{self.workspace.site_name}"

    def fetch_state(self) -> TableauWorkspaceData:  # pyright: ignore[reportIncompatibleMethodOverride]
        return self.workspace.fetch_tableau_workspace_data()

    def defs_from_state(self, state: TableauWorkspaceData) -> Definitions:  # pyright: ignore[reportIncompatibleMethodOverride]
        all_external_data = [
            *state.data_sources_by_id.values(),
            *state.sheets_by_id.values(),
            *state.dashboards_by_id.values(),
        ]

        all_external_asset_specs = [
            self.translator.get_asset_spec(
                TableauTranslatorData(content_data=content, workspace_data=state)
            )
            for content in all_external_data
        ]

        return Definitions(assets=all_external_asset_specs)
