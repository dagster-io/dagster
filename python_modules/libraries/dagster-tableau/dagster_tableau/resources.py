import datetime
import logging
import time
import uuid
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import Optional, Union

import jwt
import requests
import tableauserverclient as TSC
from dagster import (
    AssetExecutionContext,
    AssetObservation,
    AssetSpec,
    ConfigurableResource,
    Definitions,
    Failure,
    ObserveResult,
    Output,
    _check as check,
    get_dagster_logger,
)
from dagster._annotations import beta, beta_param, superseded
from dagster._core.definitions.definitions_load_context import StateBackedDefinitionsLoader
from dagster._record import record
from dagster._utils.cached_method import cached_method
from pydantic import Field, PrivateAttr
from tableauserverclient.server.endpoint.auth_endpoint import Auth

from dagster_tableau.asset_utils import (
    create_data_source_asset_event,
    create_view_asset_event,
    create_view_asset_observation,
)
from dagster_tableau.translator import (
    DagsterTableauTranslator,
    TableauContentData,
    TableauContentType,
    TableauDataSourceMetadataSet,
    TableauMetadataSet,
    TableauTagSet,
    TableauTranslatorData,
    TableauViewMetadataSet,
    TableauWorkspaceData,
    WorkbookSelectorFn,
)

DEFAULT_POLL_INTERVAL_SECONDS = 10
DEFAULT_POLL_TIMEOUT = 600
DEFAULT_PAGE_SIZE = 100

TABLEAU_RECONSTRUCTION_METADATA_KEY_PREFIX = "dagster-tableau/reconstruction_metadata"


def _paginate_get(
    get_fn,
    page_size: int = DEFAULT_PAGE_SIZE,
):
    """Generic pagination function for Tableau Server Client get methods.

    Args:
        get_fn: The get function to paginate (e.g., server.datasources.get, server.workbooks.get)
        page_size: Number of items to fetch per page. Defaults to DEFAULT_PAGE_SIZE.

    Returns:
        List of all items from all pages.
    """
    all_items = []
    items, pagination = get_fn(TSC.RequestOptions(pagenumber=1, pagesize=page_size))
    all_items.extend(items)

    page_number = 2
    while pagination.page_number * pagination.page_size < pagination.total_available:
        items, pagination = get_fn(TSC.RequestOptions(pagenumber=page_number, pagesize=page_size))
        all_items.extend(items)
        page_number += 1

    return all_items


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
    def get_data_sources(self) -> list[TSC.DatasourceItem]:
        return _paginate_get(self._server.datasources.get)

    @cached_method
    def get_data_source(
        self,
        data_source_id: str,
    ) -> TSC.DatasourceItem:
        """Fetches information for a given data source."""
        return self._server.datasources.get_by_id(data_source_id)

    def refresh_data_source(self, data_source_id) -> TSC.JobItem:
        """Refreshes all extracts for a given data source and return the JobItem object."""
        return self._server.datasources.refresh(data_source_id)

    @cached_method
    def get_workbooks(self) -> list[TSC.WorkbookItem]:
        """Fetches a list of all Tableau workbooks in the workspace."""
        return _paginate_get(self._server.workbooks.get)

    @cached_method
    def get_workbook(self, workbook_id) -> Mapping[str, object]:
        """Fetches information, including sheets, dashboards and data sources, for a given workbook."""
        return self._server.metadata.query(
            query=self.workbook_graphql_query, variables={"luid": workbook_id}
        )

    def refresh_workbook(self, workbook_id) -> TSC.JobItem:
        """Refreshes all extracts for a given workbook and return the JobItem object."""
        return self._server.workbooks.refresh(workbook_id)

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

    @superseded(additional_warn_text="Use `refresh_and_poll` on the tableau resource instead.")
    def refresh_and_materialize_workbooks(
        self, specs: Sequence[AssetSpec], refreshable_workbook_ids: Optional[Sequence[str]]
    ) -> Iterator[Union[AssetObservation, Output]]:
        """Refreshes workbooks for the given workbook IDs and materializes workbook views given the asset specs."""
        refreshed_workbook_ids = set()
        for refreshable_workbook_id in refreshable_workbook_ids or []:
            refreshed_workbook_ids.add(self.refresh_and_poll_workbook(refreshable_workbook_id))

        for spec in specs:
            view_id = check.inst(TableauMetadataSet.extract(spec.metadata).id, str)
            yield from create_view_asset_event(
                view=self.get_view(view_id),
                spec=spec,
                refreshed_workbook_ids=refreshed_workbook_ids,
            )

    def refresh_and_poll_workbook(
        self,
        workbook_id: str,
        poll_interval: Optional[float] = None,
        poll_timeout: Optional[float] = None,
    ) -> Optional[str]:
        job = self.refresh_workbook(workbook_id)
        self._log.info(f"Job {job.id} initialized for workbook_id={workbook_id}.")

        job = self.poll_job(job_id=job.id, poll_interval=poll_interval, poll_timeout=poll_timeout)
        return job.workbook_id

    @superseded(additional_warn_text="Use `refresh_and_poll` on the tableau resource instead.")
    def refresh_and_materialize(
        self, specs: Sequence[AssetSpec], refreshable_data_source_ids: Optional[Sequence[str]]
    ) -> Iterator[Union[AssetObservation, Output]]:
        """Refreshes data sources for the given data source IDs and materializes Tableau assets given the asset specs.
        Only data sources with extracts can be refreshed.
        """
        refreshed_data_source_ids = set()
        for refreshable_data_source_id in refreshable_data_source_ids or []:
            refreshed_data_source_ids.add(
                self.refresh_and_poll_data_source(refreshable_data_source_id)
            )

        # If a sheet depends on a refreshed data source, then its workbook is considered refreshed
        refreshed_workbook_ids = set()
        specs_by_asset_key = {spec.key: spec for spec in specs}
        for spec in specs:
            if TableauTagSet.extract(spec.tags).asset_type == "sheet":
                for dep in spec.deps:
                    # Only materializable data sources are included in materializable asset specs,
                    # so we must verify for None values - data sources that are external specs are not available here.
                    dep_spec = specs_by_asset_key.get(dep.asset_key, None)
                    if (
                        dep_spec
                        and TableauMetadataSet.extract(dep_spec.metadata).id
                        in refreshed_data_source_ids
                    ):
                        refreshed_workbook_ids.add(
                            TableauViewMetadataSet.extract(spec.metadata).workbook_id
                        )
                        break

        for spec in specs:
            asset_type = check.inst(TableauTagSet.extract(spec.tags).asset_type, str)
            asset_id = check.inst(TableauMetadataSet.extract(spec.metadata).id, str)

            if asset_type == "data_source":
                yield from create_data_source_asset_event(
                    data_source=self.get_data_source(asset_id),
                    spec=spec,
                    refreshed_data_source_ids=refreshed_data_source_ids,
                )
            else:
                yield from create_view_asset_event(
                    view=self.get_view(asset_id),
                    spec=spec,
                    refreshed_workbook_ids=refreshed_workbook_ids,
                )

    def refresh_and_poll_data_source(
        self,
        data_source_id: str,
        poll_interval: Optional[float] = None,
        poll_timeout: Optional[float] = None,
    ) -> Optional[str]:
        job = self.refresh_data_source(data_source_id)
        self._log.info(f"Job {job.id} initialized for data_source_id={data_source_id}.")

        job = self.poll_job(job_id=job.id, poll_interval=poll_interval, poll_timeout=poll_timeout)
        return job.datasource_id

    def refresh_and_poll_data_sources(
        self,
        data_source_ids: Sequence[str],
        poll_interval: Optional[float] = None,
        poll_timeout: Optional[float] = None,
    ) -> Iterator[str]:
        """Refreshes multiple data sources and yields their IDs as they complete.

        Args:
            data_source_ids: List of data source IDs to refresh
            poll_interval: Optional polling interval in seconds
            poll_timeout: Optional timeout in seconds

        Yields:
            str: Data source IDs as their refresh jobs complete
        """
        # First, kick off all refresh jobs
        job_ids = []
        for data_source_id in data_source_ids:
            job = self.refresh_data_source(data_source_id)
            self._log.info(f"Job {job.id} initialized for data_source_id={data_source_id}.")
            job_ids.append(job.id)

        # Then poll all jobs until they complete, yielding datasource_id as each completes
        for job in self.poll_jobs(
            job_ids=job_ids, poll_interval=poll_interval, poll_timeout=poll_timeout
        ):
            if job.datasource_id:
                yield job.datasource_id

    def poll_jobs(
        self,
        job_ids: Sequence[str],
        poll_interval: Optional[float] = None,
        poll_timeout: Optional[float] = None,
    ) -> Iterator[TSC.JobItem]:
        """Polls multiple jobs and yields them as they complete.

        Args:
            job_ids: List of job IDs to poll
            poll_interval: Optional polling interval in seconds
            poll_timeout: Optional timeout in seconds

        Yields:
            TSC.JobItem: Completed job items as they finish successfully
        """
        if not poll_interval:
            poll_interval = DEFAULT_POLL_INTERVAL_SECONDS
        if not poll_timeout:
            poll_timeout = DEFAULT_POLL_TIMEOUT

        start = time.monotonic()
        pending_job_ids = set(job_ids)

        try:
            while pending_job_ids:
                if poll_timeout and start + poll_timeout < time.monotonic():
                    raise Failure(
                        f"Timeout: Tableau jobs {pending_job_ids} are not ready after the timeout"
                        f" {poll_timeout} seconds"
                    )

                time.sleep(poll_interval)

                # Check status of all pending jobs
                for job_id in list(pending_job_ids):
                    job = self.get_job(job_id=job_id)

                    if job.finish_code == -1:
                        # -1 is the default value for JobItem.finish_code, when the job is in progress
                        continue
                    elif job.finish_code == TSC.JobItem.FinishCode.Success:
                        pending_job_ids.remove(job_id)
                        yield job
                    elif job.finish_code == TSC.JobItem.FinishCode.Failed:
                        pending_job_ids.remove(job_id)
                        raise Failure(f"Job failed: {job.id}")
                    elif job.finish_code == TSC.JobItem.FinishCode.Cancelled:
                        pending_job_ids.remove(job_id)
                        raise Failure(f"Job was cancelled: {job.id}")
                    else:
                        pending_job_ids.remove(job_id)
                        raise Failure(
                            f"Encountered unexpected finish code `{job.finish_code}` for job {job.id}"
                        )
        finally:
            # if any Tableau syncs have not completed, make sure to cancel them so they don't outlive
            # the python process
            for job_id in pending_job_ids:
                job = self.get_job(job_id=job_id)
                if job.finish_code not in (
                    TSC.JobItem.FinishCode.Success,
                    TSC.JobItem.FinishCode.Failed,
                    TSC.JobItem.FinishCode.Cancelled,
                ):
                    self.cancel_job(job_id)

    def poll_job(
        self,
        job_id: str,
        poll_interval: Optional[float] = None,
        poll_timeout: Optional[float] = None,
    ) -> TSC.JobItem:
        """Polls a single job until it completes.

        Args:
            job_id: The job ID to poll
            poll_interval: Optional polling interval in seconds
            poll_timeout: Optional timeout in seconds

        Returns:
            TSC.JobItem: The completed job item
        """
        jobs = list(
            self.poll_jobs(job_ids=[job_id], poll_interval=poll_interval, poll_timeout=poll_timeout)
        )
        return jobs[0]

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
                "scp": ["tableau:content:read", "tableau:tasks:run", "tableau:jobs:read"],
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
                projectName
                projectLuid
                sheets {
                  luid
                  id
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
                    id
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
        json_schema_extra={"dagster__is_secret": True},
    )
    username: str = Field(..., description="The username to authenticate to Tableau Workspace.")
    site_name: str = Field(..., description="The name of the Tableau site to use.")

    _client: Optional[Union[TableauCloudClient, TableauServerClient]] = PrivateAttr(default=None)

    @property
    @cached_method
    def _log(self) -> logging.Logger:
        return get_dagster_logger()

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

    @cached_method
    def fetch_tableau_workspace_data(
        self,
    ) -> TableauWorkspaceData:
        """Retrieves all Tableau content from the workspace and returns it as a TableauWorkspaceData object.
        Future work will cache this data to avoid repeated calls to the Tableau API.

        Returns:
            TableauWorkspaceData: A snapshot of the Tableau workspace's content.
        """
        with self.get_client() as client:
            all_workbooks = list(client.get_workbooks())
            workbooks: list[TableauContentData] = []
            sheets: list[TableauContentData] = []
            dashboards: list[TableauContentData] = []
            data_sources: list[TableauContentData] = []
            data_source_ids: set[str] = set()
            for wb in all_workbooks:
                workbook_id = wb.id
                workbook_name = wb.name
                workbook = client.get_workbook(workbook_id=workbook_id)
                workbook_data_list = check.is_list(
                    workbook["data"]["workbooks"],  # pyright: ignore[reportIndexIssue]
                    additional_message=f"Invalid data for Tableau workbook for id {workbook_id}.",
                )
                if not workbook_data_list:
                    self._log.warning(
                        f"No data retrieved for Tableau workbook {workbook_name} with id {workbook_id}. Skipping."
                    )
                    continue
                workbook_data = workbook_data_list[0]
                workbooks.append(
                    TableauContentData(
                        content_type=TableauContentType.WORKBOOK, properties=workbook_data
                    )
                )

                # We keep track of data source IDs for each sheet to augment the dashboard data.
                # Hidden sheets don't have LUIDs, so we use metadata IDs as keys.
                data_source_ids_by_sheet_metadata_id = defaultdict(set)
                for sheet_data in workbook_data["sheets"]:
                    sheet_id = sheet_data["luid"]
                    sheet_metadata_id = sheet_data["id"]
                    if sheet_id or sheet_metadata_id:
                        augmented_sheet_data = {**sheet_data, "workbook": {"luid": workbook_id}}
                        sheets.append(
                            TableauContentData(
                                content_type=TableauContentType.SHEET,
                                properties=augmented_sheet_data,
                            )
                        )
                    """
                    Lineage formation depends on the availability of published data sources.
                    If published data sources are available (i.e., parentPublishedDatasources exists and is not empty), 
                    it means you can form the lineage by using the luid of those published sources.
                    If the published data sources are missing, 
                    you create assets for embedded data sources by using their id.
                    """
                    for embedded_data_source_data in sheet_data.get(
                        "parentEmbeddedDatasources", []
                    ):
                        published_data_source_list = embedded_data_source_data.get(
                            "parentPublishedDatasources", []
                        )
                        for published_data_source_data in published_data_source_list:
                            data_source_id = published_data_source_data["luid"]
                            data_source_ids_by_sheet_metadata_id[sheet_metadata_id].add(
                                data_source_id
                            )
                            if data_source_id and data_source_id not in data_source_ids:
                                data_source_ids.add(data_source_id)
                                augmented_published_data_source_data = {
                                    **published_data_source_data,
                                    "isPublished": True,
                                }
                                data_sources.append(
                                    TableauContentData(
                                        content_type=TableauContentType.DATA_SOURCE,
                                        properties=augmented_published_data_source_data,
                                    )
                                )
                        if not published_data_source_list:
                            """While creating TableauWorkspaceData luid is mandatory for all TableauContentData
                            and in case of embedded_data_source its missing hence we are using its id as luid"""
                            data_source_id = embedded_data_source_data["id"]
                            data_source_ids_by_sheet_metadata_id[sheet_metadata_id].add(
                                data_source_id
                            )
                            if data_source_id and data_source_id not in data_source_ids:
                                data_source_ids.add(data_source_id)
                                embedded_data_source_data["luid"] = data_source_id
                                augmented_embedded_data_source_data = {
                                    **embedded_data_source_data,
                                    "isPublished": False,
                                    "workbook": {"luid": workbook_id},
                                }
                                data_sources.append(
                                    TableauContentData(
                                        content_type=TableauContentType.DATA_SOURCE,
                                        properties=augmented_embedded_data_source_data,
                                    )
                                )

                for dashboard_data in workbook_data["dashboards"]:
                    dashboard_id = dashboard_data["luid"]
                    if dashboard_id:
                        dashboard_upstream_sheets = dashboard_data.get("sheets", [])
                        # Sheets for which LUID is null are hidden sheets
                        hidden_sheet_metadata_ids = {
                            sheet["id"] for sheet in dashboard_upstream_sheets if not sheet["luid"]
                        }
                        dashboard_upstream_data_source_ids = set()
                        for hidden_sheet_metadata_id in hidden_sheet_metadata_ids:
                            dashboard_upstream_data_source_ids.update(
                                data_source_ids_by_sheet_metadata_id.get(
                                    hidden_sheet_metadata_id, []
                                )
                            )

                        augmented_dashboard_data = {
                            **dashboard_data,
                            "workbook": {"luid": workbook_id},
                            "data_source_ids": list(dashboard_upstream_data_source_ids),
                        }
                        dashboards.append(
                            TableauContentData(
                                content_type=TableauContentType.DASHBOARD,
                                properties=augmented_dashboard_data,
                            )
                        )

            """
            We add to the data all the published-data-sources, that weren't already added from a workbook.
            """
            for published_data_source in client.get_data_sources():
                # if we already processed this data_source, skip it
                if published_data_source.id in data_source_ids:
                    continue

                data_sources.append(
                    TableauContentData(
                        content_type=TableauContentType.DATA_SOURCE,
                        properties={
                            "id": published_data_source.id,
                            "name": published_data_source.name,
                            "hasExtracts": published_data_source.has_extracts,
                            "luid": published_data_source.id,
                            "isPublished": True,
                            "workbook": None,
                        },
                    )
                )

        return TableauWorkspaceData.from_content_data(
            self.site_name,
            workbooks + sheets + dashboards + data_sources,
        )

    def get_or_fetch_workspace_data(
        self,
    ) -> TableauWorkspaceData:
        """Retrieves all Tableau content from the workspace using the TableauWorkspaceDefsLoader
        and returns it as a TableauWorkspaceData object. If the workspace data has already been fetched,
        the cached TableauWorkspaceData object is returned.

        Returns:
            TableauWorkspaceData: A snapshot of the Tableau workspace's content.
        """
        return TableauWorkspaceDefsLoader(
            workspace=self, translator=DagsterTableauTranslator()
        ).get_or_fetch_state()

    # Cache spec retrieval for a specific translator class and workbook_selector_fn
    @cached_method
    def load_asset_specs(
        self,
        dagster_tableau_translator: Optional[DagsterTableauTranslator] = None,
        workbook_selector_fn: Optional[WorkbookSelectorFn] = None,
    ) -> Sequence[AssetSpec]:
        """Returns a list of AssetSpecs representing the Tableau content in the workspace.

        Args:
            dagster_tableau_translator (Optional[DagsterTableauTranslator]):
                The translator to use to convert Tableau content into :py:class:`dagster.AssetSpec`.
                Defaults to :py:class:`DagsterTableauTranslator`.
            workbook_selector_fn (Optional[WorkbookSelectorFn]):
                A function that allows for filtering which Tableau workbook assets are created for,
                including data sources, sheets and dashboards.

        Returns:
            List[AssetSpec]: The set of assets representing the Tableau content in the workspace.
        """
        with self.process_config_and_initialize_cm() as initialized_workspace:
            return check.is_list(
                TableauWorkspaceDefsLoader(
                    workspace=initialized_workspace,
                    translator=dagster_tableau_translator or DagsterTableauTranslator(),
                    workbook_selector_fn=workbook_selector_fn,
                )
                .build_defs()
                .assets,
                AssetSpec,
            )

    def refresh_and_poll(
        self, context: AssetExecutionContext
    ) -> Iterator[Union[Output, ObserveResult, AssetObservation]]:
        """Executes a refresh and poll process to materialize Tableau assets,
        including data sources with extracts, views and workbooks.
        This method can only be used in the context of an asset execution.
        """
        assets_def = context.assets_def
        specs = [
            assets_def.specs_by_key[selected_key] for selected_key in context.selected_asset_keys
        ]
        refreshable_data_source_ids = [
            check.not_none(TableauDataSourceMetadataSet.extract(spec.metadata).id)
            for spec in specs
            if check.inst(TableauTagSet.extract(spec.tags).asset_type, str) == "data_source"
            and TableauDataSourceMetadataSet.extract(spec.metadata).has_extracts
        ]

        with self.get_client() as client:
            refreshed_data_source_ids = set()
            for refreshable_data_source_id in refreshable_data_source_ids:
                refreshed_data_source_ids.add(
                    client.refresh_and_poll_data_source(refreshable_data_source_id)
                )

            data_source_specs = [
                spec
                for spec in specs
                if check.inst(TableauTagSet.extract(spec.tags).asset_type, str) == "data_source"
            ]
            sheet_source_specs = [
                spec
                for spec in specs
                if check.inst(TableauTagSet.extract(spec.tags).asset_type, str) == "sheet"
            ]
            dashboards_source_specs = [
                spec
                for spec in specs
                if check.inst(TableauTagSet.extract(spec.tags).asset_type, str) == "dashboard"
            ]

            # Order of materialization matters - first we materialize data sources, then sheets, and finally dashboards.
            for spec in data_source_specs:
                yield from create_data_source_asset_event(
                    data_source=client.get_data_source(
                        check.inst(TableauMetadataSet.extract(spec.metadata).id, str)
                    ),
                    spec=spec,
                    refreshed_data_source_ids=refreshed_data_source_ids,
                )

            for spec in sheet_source_specs:
                yield from create_view_asset_observation(
                    view=client.get_view(
                        check.inst(TableauMetadataSet.extract(spec.metadata).id, str)
                    ),
                    spec=spec,
                )

            for spec in dashboards_source_specs:
                yield from create_view_asset_observation(
                    view=client.get_view(
                        check.inst(TableauMetadataSet.extract(spec.metadata).id, str)
                    ),
                    spec=spec,
                )


@beta
@beta_param(param="workbook_selector_fn")
def load_tableau_asset_specs(
    workspace: BaseTableauWorkspace,
    dagster_tableau_translator: Optional[DagsterTableauTranslator] = None,
    workbook_selector_fn: Optional[WorkbookSelectorFn] = None,
) -> Sequence[AssetSpec]:
    """Returns a list of AssetSpecs representing the Tableau content in the workspace.

    Args:
        workspace (Union[TableauCloudWorkspace, TableauServerWorkspace]): The Tableau workspace to fetch assets from.
        dagster_tableau_translator (Optional[DagsterTableauTranslator]):
            The translator to use to convert Tableau content into :py:class:`dagster.AssetSpec`.
            Defaults to :py:class:`DagsterTableauTranslator`.
        workbook_selector_fn (Optional[WorkbookSelectorFn]):
            A function that allows for filtering which Tableau workbook assets are created for,
            including data sources, sheets and dashboards.

    Returns:
        List[AssetSpec]: The set of assets representing the Tableau content in the workspace.
    """
    return workspace.load_asset_specs(
        dagster_tableau_translator=dagster_tableau_translator,
        workbook_selector_fn=workbook_selector_fn,
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
class TableauWorkspaceDefsLoader(StateBackedDefinitionsLoader[TableauWorkspaceData]):
    workspace: BaseTableauWorkspace
    translator: DagsterTableauTranslator
    workbook_selector_fn: Optional[WorkbookSelectorFn] = None

    @property
    def defs_key(self) -> str:
        return f"{TABLEAU_RECONSTRUCTION_METADATA_KEY_PREFIX}/{self.workspace.site_name}"

    def fetch_state(self) -> TableauWorkspaceData:
        return self.workspace.fetch_tableau_workspace_data()

    def defs_from_state(self, state: TableauWorkspaceData) -> Definitions:
        selected_state = state.to_workspace_data_selection(
            workbook_selector_fn=self.workbook_selector_fn
        )

        # Filter hidden sheets:
        # 1. They typically lack a path.
        # 2. They are required in workspace data to maintain data source lineage.
        visible_sheets = [
            sheet
            for sheet in selected_state.sheets_by_id.values()
            if sheet.properties.get("path") != ""
        ]

        all_external_data = [
            *selected_state.data_sources_by_id.values(),
            *visible_sheets,
            *selected_state.dashboards_by_id.values(),
        ]

        all_external_asset_specs = [
            self.translator.get_asset_spec(
                TableauTranslatorData(content_data=content, workspace_data=selected_state)
            )
            for content in all_external_data
        ]

        return Definitions(assets=all_external_asset_specs)
