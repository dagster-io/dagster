import logging
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, ClassVar, Optional, Union
from urllib.parse import parse_qsl, urlparse

import requests
from dagster import (
    AssetExecutionContext,
    AssetMaterialization,
    AssetSpec,
    ConfigurableResource,
    Definitions,
    Failure,
    MaterializeResult,
    _check as check,
    get_dagster_logger,
)
from dagster._annotations import superseded
from dagster._core.definitions.definitions_load_context import StateBackedDefinitionsLoader
from dagster._symbol_annotations import beta, public
from dagster_shared.dagster_model import DagsterModel
from dagster_shared.record import record
from dagster_shared.utils.cached_method import cached_method
from pydantic import Field, PrivateAttr, model_validator
from requests.exceptions import RequestException

from dagster_airbyte.translator import (
    AirbyteConnection,
    AirbyteConnectionTableProps,
    AirbyteDestination,
    AirbyteJob,
    AirbyteJobStatusType,
    AirbyteMetadataSet,
    AirbyteWorkspaceData,
    DagsterAirbyteTranslator,
)
from dagster_airbyte.types import AirbyteOutput
from dagster_airbyte.utils import (
    DAGSTER_AIRBYTE_TRANSLATOR_METADATA_KEY,
    get_airbyte_connection_table_name,
    get_translator_from_airbyte_assets,
)

AIRBYTE_CLOUD_REST_API_BASE = "https://api.airbyte.com"
AIRBYTE_CLOUD_REST_API_VERSION = "v1"
AIRBYTE_CLOUD_REST_API_BASE_URL = f"{AIRBYTE_CLOUD_REST_API_BASE}/{AIRBYTE_CLOUD_REST_API_VERSION}"
AIRBYTE_CLOUD_CONFIGURATION_API_BASE = "https://cloud.airbyte.com/api"
AIRBYTE_CLOUD_CONFIGURATION_API_VERSION = "v1"
AIRBYTE_CLOUD_CONFIGURATION_API_BASE_URL = (
    f"{AIRBYTE_CLOUD_CONFIGURATION_API_BASE}/{AIRBYTE_CLOUD_CONFIGURATION_API_VERSION}"
)

DEFAULT_POLL_INTERVAL_SECONDS = 10

# The access token expire every 3 minutes in Airbyte Cloud.
# Refresh is needed after 2.5 minutes to avoid the "token expired" error message.
AIRBYTE_REFRESH_TIMEDELTA_SECONDS = 150

AIRBYTE_RECONSTRUCTION_METADATA_KEY_PREFIX = "dagster-airbyte/reconstruction_metadata"


@beta
class AirbyteClient(DagsterModel):
    """This class exposes methods on top of the Airbyte APIs for Airbyte."""

    rest_api_base_url: str = Field(
        default=AIRBYTE_CLOUD_REST_API_BASE_URL,
        description=(
            "The base URL for the Airbyte REST API. "
            "For Airbyte Cloud, leave this as the default. "
            "For self-managed Airbyte, this is usually <your Airbyte host>/api/public/v1."
        ),
    )
    configuration_api_base_url: str = Field(
        default=AIRBYTE_CLOUD_CONFIGURATION_API_BASE_URL,
        description=(
            "The base URL for the Airbyte Configuration API. "
            "For Airbyte Cloud, leave this as the default. "
            "For self-managed Airbyte, this is usually <your Airbyte host>/api/v1."
        ),
    )
    workspace_id: str = Field(..., description="The Airbyte workspace ID")
    client_id: Optional[str] = Field(default=None, description="The Airbyte client ID.")
    client_secret: Optional[str] = Field(default=None, description="The Airbyte client secret.")
    username: Optional[str] = Field(
        default=None,
        description="The Airbyte username for authentication. Used for self-managed Airbyte with basic auth.",
    )
    password: Optional[str] = Field(
        default=None,
        description="The Airbyte password for authentication. Used for self-managed Airbyte with basic auth.",
    )
    request_max_retries: int = Field(
        ...,
        description=(
            "The maximum number of times requests to the Airbyte API should be retried "
            "before failing."
        ),
    )
    request_retry_delay: float = Field(
        ...,
        description="Time (in seconds) to wait between each request retry.",
    )
    request_timeout: int = Field(
        ...,
        description="Time (in seconds) after which the requests to Airbyte are declared timed out.",
    )
    max_items_per_page: int = Field(
        default=100,
        description=(
            "The maximum number of items per page. "
            "Used for paginated resources like connections, destinations, etc. "
        ),
    )
    poll_interval: float = Field(
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        description="The time (in seconds) that will be waited between successive polls.",
    )
    poll_timeout: Optional[float] = Field(
        default=None,
        description=(
            "The maximum time that will wait before this operation is timed "
            "out. By default, this will never time out."
        ),
    )
    cancel_on_termination: bool = Field(
        default=True,
        description=(
            "Whether to cancel a sync in Airbyte if the Dagster runner is terminated. "
            "This may be useful to disable if using Airbyte sources that cannot be cancelled and "
            "resumed easily, or if your Dagster deployment may experience runner interruptions "
            "that do not impact your Airbyte deployment."
        ),
    )
    poll_previous_running_sync: bool = Field(
        default=False,
        description=(
            "If set to True, Dagster will check for previous running sync for the same connection "
            "and begin polling it instead of starting a new sync."
        ),
    )

    _access_token_value: Optional[str] = PrivateAttr(default=None)
    _access_token_timestamp: Optional[float] = PrivateAttr(default=None)

    @model_validator(mode="before")
    def validate_authentication(cls, values):
        has_client_id = values.get("client_id") is not None
        has_client_secret = values.get("client_secret") is not None
        has_username = values.get("username") is not None
        has_password = values.get("password") is not None

        check.invariant(
            has_username == has_password,
            "Missing config: both username and password are required for Airbyte authentication.",
        )

        check.invariant(
            has_client_id == has_client_secret,
            "Missing config: both client_id and client_secret are required for Airbyte authentication.",
        )

        check.invariant(
            not ((has_client_id or has_client_secret) and (has_username or has_password)),
            "Invalid config: cannot provide both client_id/client_secret and username/password for Airbyte authentication.",
        )
        return values

    @property
    @cached_method
    def _log(self) -> logging.Logger:
        return get_dagster_logger()

    @property
    def all_additional_request_headers(self) -> Mapping[str, Any]:
        return {**self.authorization_request_headers, **self.user_agent_request_headers}

    @property
    def authorization_request_headers(self) -> Mapping[str, Any]:
        # Make sure the access token is refreshed before using it when calling the API.
        if not (self.client_id and self.client_secret):
            return {}

        if self._needs_refreshed_access_token():
            self._refresh_access_token()
        return {
            "Authorization": f"Bearer {self._access_token_value}",
        }

    @property
    def user_agent_request_headers(self) -> Mapping[str, Any]:
        return {
            "User-Agent": "dagster",
        }

    def _refresh_access_token(self) -> None:
        response = check.not_none(
            self._single_request(
                method="POST",
                url=f"{self.rest_api_base_url}/applications/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                # Must not pass the bearer access token when refreshing it.
                include_additional_request_headers=False,
            )
        )
        self._access_token_value = str(response["access_token"])
        self._access_token_timestamp = datetime.now().timestamp()

    def _needs_refreshed_access_token(self) -> bool:
        return (
            not self._access_token_value
            or not self._access_token_timestamp
            or self._access_token_timestamp
            <= (datetime.now() - timedelta(seconds=AIRBYTE_REFRESH_TIMEDELTA_SECONDS)).timestamp()
        )

    def _get_session(self, include_additional_request_headers: bool) -> requests.Session:
        headers = {"accept": "application/json"}
        if include_additional_request_headers:
            headers = {
                **headers,
                **self.all_additional_request_headers,
            }
        session = requests.Session()
        session.headers.update(headers)

        if self.username and self.password:
            session.auth = (self.username, self.password)

        return session

    def _single_request(
        self,
        method: str,
        url: str,
        data: Optional[Mapping[str, Any]] = None,
        params: Optional[Mapping[str, Any]] = None,
        include_additional_request_headers: bool = True,
    ) -> Mapping[str, Any]:
        """Execute a single HTTP request with retry logic."""
        num_retries = 0
        while True:
            try:
                session = self._get_session(
                    include_additional_request_headers=include_additional_request_headers
                )
                response = session.request(
                    method=method, url=url, json=data, params=params, timeout=self.request_timeout
                )
                response.raise_for_status()
                return response.json()
            except RequestException as e:
                self._log.error(
                    f"Request to Airbyte API failed for url {url} with method {method} : {e}"
                )
                if num_retries == self.request_max_retries:
                    break
                num_retries += 1
                time.sleep(self.request_retry_delay)

            raise Failure(f"Max retries ({self.request_max_retries}) exceeded with url: {url}.")

        return {}

    def _paginated_request(
        self,
        method: str,
        url: str,
        params: dict[str, Any],
        data: Optional[Mapping[str, Any]] = None,
        include_additional_request_params: bool = True,
    ) -> Sequence[Mapping[str, Any]]:
        """Execute paginated requests and yield all items."""
        result_data = []
        params = {"limit": self.max_items_per_page, **params}
        while True:
            response = self._single_request(
                method=method,
                url=url,
                data=data,
                params=params,
                include_additional_request_headers=include_additional_request_params,
            )

            # Handle different response structures
            result_data.extend(response.get("data", []))
            next_url = response.get("next", "")
            if not next_url:
                break

            # Parse the query string for the next page
            next_params = parse_qsl(urlparse(next_url).query)
            # Overwrite the pagination params with the ones for the next page
            params.update(dict(next_params))

        return result_data

    def validate_workspace_id(self) -> None:
        """Fetches workspace details. This is used to validate that the workspace exists."""
        self._single_request(
            method="GET",
            url=f"{self.rest_api_base_url}/workspaces/{self.workspace_id}",
        )

    def get_connections(self) -> Sequence[Mapping[str, Any]]:
        """Fetches all connections of an Airbyte workspace from the Airbyte REST API."""
        return self._paginated_request(
            method="GET",
            url=f"{self.rest_api_base_url}/connections",
            params={"workspaceIds": self.workspace_id},
        )

    def get_jobs_for_connection(
        self, connection_id: str, created_after: datetime | None = None
    ) -> Sequence[AirbyteJob]:
        """Fetches all jobs for a specific connection of an Airbyte workspace from the Airbyte REST API."""
        params = {"workspaceIds": self.workspace_id, "connectionId": connection_id}
        if created_after:
            params["createdAtStart"] = created_after.strftime("%Y-%m-%dT%H:%M:%SZ")

        return [
            AirbyteJob.from_job_details(job_details=job_details)
            for job_details in self._paginated_request(
                method="GET",
                url=f"{self.rest_api_base_url}/jobs",
                params=params,
            )
        ]

    def get_connection_details(self, connection_id) -> Mapping[str, Any]:
        """Fetches details about a given connection from the Airbyte Configuration API.
        The Airbyte Configuration API is an internal and may change in the future.
        """
        # Using the Airbyte Configuration API to get the connection details, including streams and their configs.
        # https://airbyte-public-api-docs.s3.us-east-2.amazonaws.com/rapidoc-api-docs.html#post-/v1/connections/get
        # https://github.com/airbytehq/airbyte-platform/blob/v1.0.0/airbyte-api/server-api/src/main/openapi/config.yaml
        return self._single_request(
            method="POST",
            url=f"{self.configuration_api_base_url}/connections/get",
            data={"connectionId": connection_id},
        )

    def get_destination_details(self, destination_id: str) -> Mapping[str, Any]:
        """Fetches details about a given destination from the Airbyte REST API."""
        return self._single_request(
            method="GET",
            url=f"{self.rest_api_base_url}/destinations/{destination_id}",
        )

    def start_sync_job(self, connection_id: str) -> Mapping[str, Any]:
        return self._single_request(
            method="POST",
            url=f"{self.rest_api_base_url}/jobs",
            data={
                "connectionId": connection_id,
                "jobType": "sync",
            },
        )

    def get_job_details(self, job_id: int) -> Mapping[str, Any]:
        return self._single_request(
            method="GET",
            url=f"{self.rest_api_base_url}/jobs/{job_id}",
        )

    def cancel_job(self, job_id: int) -> Mapping[str, Any]:
        return self._single_request(
            method="DELETE",
            url=f"{self.rest_api_base_url}/jobs/{job_id}",
        )

    def sync_and_poll(self, connection_id: str) -> AirbyteOutput:
        """Initializes a sync operation for the given connection, and polls until it completes.

        Args:
            connection_id (str): The Airbyte Connection ID. You can retrieve this value from the
                "Connection" tab of a given connection in the Airbyte UI.

        Returns:
            :py:class:`~AirbyteOutput`:
                Details of the sync job.
        """
        connection_details = self.get_connection_details(connection_id)

        existing_jobs = [
            job
            for job in self.get_jobs_for_connection(
                connection_id=connection_id,
                created_after=datetime.now() - timedelta(days=2),
            )
            if job.status
            in (
                AirbyteJobStatusType.RUNNING,
                AirbyteJobStatusType.PENDING,
                AirbyteJobStatusType.INCOMPLETE,
            )
        ]

        if not existing_jobs:
            start_job_details = self.start_sync_job(connection_id)
            job = AirbyteJob.from_job_details(job_details=start_job_details)
            self._log.info(f"Job {job.id} initialized for connection_id={connection_id}.")
        else:
            if self.poll_previous_running_sync:
                if len(existing_jobs) == 1:
                    job = existing_jobs[0]
                    self._log.info(
                        f"Job {job.id} already running for connection_id={connection_id}. Resume polling."
                    )
                else:
                    raise Failure(f"Found multiple running jobs for connection_id={connection_id}.")
            else:
                raise Failure(f"Found sync job for connection_id={connection_id} already running.")

        poll_start = datetime.now()

        try:
            while True:
                if self.poll_timeout and datetime.now() > poll_start + timedelta(
                    seconds=self.poll_timeout
                ):
                    raise Failure(
                        f"Timeout: Airbyte job {job.id} is not ready after the timeout"
                        f" {self.poll_timeout} seconds"
                    )

                time.sleep(self.poll_interval)
                # We return these job details in the AirbyteOutput when the job succeeds
                poll_job_details = self.get_job_details(job.id)
                self._log.debug(poll_job_details)
                job = AirbyteJob.from_job_details(job_details=poll_job_details)
                if job.status in (
                    AirbyteJobStatusType.RUNNING,
                    AirbyteJobStatusType.PENDING,
                    AirbyteJobStatusType.INCOMPLETE,
                ):
                    continue
                elif job.status == AirbyteJobStatusType.SUCCEEDED:
                    break
                elif job.status in [AirbyteJobStatusType.ERROR, AirbyteJobStatusType.FAILED]:
                    raise Failure(f"Job failed: {job.id}")
                elif job.status == AirbyteJobStatusType.CANCELLED:
                    raise Failure(f"Job was cancelled: {job.id}")
                else:
                    raise Failure(
                        f"Encountered unexpected state `{job.status}` for job_id {job.id}"
                    )
        finally:
            # if Airbyte sync has not completed, make sure to cancel it so that it doesn't outlive
            # the python process
            if self.cancel_on_termination and job.status not in (
                AirbyteJobStatusType.SUCCEEDED,
                AirbyteJobStatusType.ERROR,
                AirbyteJobStatusType.CANCELLED,
                AirbyteJobStatusType.FAILED,
            ):
                self.cancel_job(job.id)

        return AirbyteOutput(job_details=poll_job_details, connection_details=connection_details)


@beta
class BaseAirbyteWorkspace(ConfigurableResource):
    """This class represents a Airbyte workspace and provides utilities
    to interact with Airbyte APIs.
    """

    request_max_retries: int = Field(
        default=3,
        description=(
            "The maximum number of times requests to the Airbyte API should be retried "
            "before failing."
        ),
    )
    request_retry_delay: float = Field(
        default=0.25,
        description="Time (in seconds) to wait between each request retry.",
    )
    request_timeout: int = Field(
        default=15,
        description="Time (in seconds) after which the requests to Airbyte are declared timed out.",
    )
    max_items_per_page: int = Field(
        default=100,
        description=(
            "The maximum number of items per page. "
            "Used for paginated resources like connections, destinations, etc. "
        ),
    )
    poll_interval: float = Field(
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        description="The time (in seconds) that will be waited between successive polls.",
    )
    poll_timeout: Optional[float] = Field(
        default=None,
        description=(
            "The maximum time that will wait before this operation is timed "
            "out. By default, this will never time out."
        ),
    )
    cancel_on_termination: bool = Field(
        default=True,
        description=(
            "Whether to cancel a sync in Airbyte if the Dagster runner is terminated. "
            "This may be useful to disable if using Airbyte sources that cannot be cancelled and "
            "resumed easily, or if your Dagster deployment may experience runner interruptions "
            "that do not impact your Airbyte deployment."
        ),
    )
    poll_previous_running_sync: bool = Field(
        default=False,
        description=(
            "If set to True, Dagster will check for previous running sync for the same connection "
            "and begin polling it instead of starting a new sync."
        ),
    )

    _client: AirbyteClient = PrivateAttr(default=None)  # type: ignore

    @cached_method
    def fetch_airbyte_workspace_data(
        self,
    ) -> AirbyteWorkspaceData:
        """Retrieves all Airbyte content from the workspace and returns it as a AirbyteWorkspaceData object.

        Returns:
            AirbyteWorkspaceData: A snapshot of the Airbyte workspace's content.
        """
        connections_by_id = {}
        destinations_by_id = {}

        client = self.get_client()

        client.validate_workspace_id()

        connections = client.get_connections()

        for partial_connection_details in connections:
            full_connection_details = client.get_connection_details(
                connection_id=partial_connection_details["connectionId"]
            )
            connection = AirbyteConnection.from_connection_details(
                connection_details=full_connection_details
            )
            connections_by_id[connection.id] = connection

            destination_details = client.get_destination_details(
                destination_id=connection.destination_id
            )
            destination = AirbyteDestination.from_destination_details(
                destination_details=destination_details
            )
            destinations_by_id[destination.id] = destination

        return AirbyteWorkspaceData(
            connections_by_id=connections_by_id,
            destinations_by_id=destinations_by_id,
        )

    @cached_method
    def load_asset_specs(
        self,
        dagster_airbyte_translator: Optional[DagsterAirbyteTranslator] = None,
        connection_selector_fn: Optional[Callable[[AirbyteConnection], bool]] = None,
    ) -> Sequence[AssetSpec]:
        """Returns a list of AssetSpecs representing the Airbyte content in the workspace.

        Args:
            dagster_airbyte_translator (Optional[DagsterAirbyteTranslator], optional): The translator to use
                to convert Airbyte content into :py:class:`dagster.AssetSpec`.
                Defaults to :py:class:`DagsterAirbyteTranslator`.
            connection_selector_fn (Optional[Callable[[AirbyteConnection], bool]]): A function that allows for filtering
                which Airbyte connection assets are created for.

        Returns:
            List[AssetSpec]: The set of assets representing the Airbyte content in the workspace.

        Examples:
            Loading the asset specs for a given Airbyte workspace:
            .. code-block:: python

                from dagster_airbyte import AirbyteWorkspace

                import dagster as dg

                airbyte_workspace = AirbyteWorkspace(
                    workspace_id=dg.EnvVar("AIRBYTE_WORKSPACE_ID"),
                    client_id=dg.EnvVar("AIRBYTE_CLIENT_ID"),
                    client_secret=dg.EnvVar("AIRBYTE_CLIENT_SECRET"),
                )

                airbyte_specs = airbyte_workspace.load_asset_specs()
                dg.Definitions(assets=airbyte_specs, resources={"airbyte": airbyte_workspace})
        """
        dagster_airbyte_translator = dagster_airbyte_translator or DagsterAirbyteTranslator()

        return load_airbyte_asset_specs(
            workspace=self,
            dagster_airbyte_translator=dagster_airbyte_translator,
            connection_selector_fn=connection_selector_fn,
        )

    def _generate_materialization(
        self,
        airbyte_output: AirbyteOutput,
        dagster_airbyte_translator: DagsterAirbyteTranslator,
    ):
        connection = AirbyteConnection.from_connection_details(
            connection_details=airbyte_output.connection_details
        )

        for stream in connection.streams.values():
            if stream.selected:
                connection_table_name = get_airbyte_connection_table_name(
                    stream_prefix=connection.stream_prefix,
                    stream_name=stream.name,
                )
                stream_asset_spec = dagster_airbyte_translator.get_asset_spec(
                    props=AirbyteConnectionTableProps(
                        table_name=connection_table_name,
                        stream_prefix=connection.stream_prefix,
                        stream_name=stream.name,
                        json_schema=stream.json_schema,
                        connection_id=connection.id,
                        connection_name=connection.name,
                        destination_type=None,
                        database=None,
                        schema=None,
                    )
                )

                yield AssetMaterialization(
                    asset_key=stream_asset_spec.key,
                    description=(
                        f"Table generated via Airbyte sync "
                        f"for connection {connection.name}: {connection_table_name}"
                    ),
                    metadata=stream_asset_spec.metadata,
                )

    @public
    @beta
    def sync_and_poll(self, context: AssetExecutionContext):
        """Executes a sync and poll process to materialize Airbyte assets.
            This method can only be used in the context of an asset execution.

        Args:
            context (AssetExecutionContext): The execution context
                from within `@airbyte_assets`.

        Returns:
            Iterator[Union[AssetMaterialization, MaterializeResult]]: An iterator of MaterializeResult
                or AssetMaterialization.
        """
        assets_def = context.assets_def
        dagster_airbyte_translator = get_translator_from_airbyte_assets(assets_def)
        connection_id = next(
            check.not_none(AirbyteMetadataSet.extract(spec.metadata).connection_id)
            for spec in assets_def.specs
        )

        client = self.get_client()
        airbyte_output = client.sync_and_poll(
            connection_id=connection_id,
        )

        materialized_asset_keys = set()
        for materialization in self._generate_materialization(
            airbyte_output=airbyte_output, dagster_airbyte_translator=dagster_airbyte_translator
        ):
            # Scan through all tables actually created, if it was expected then emit a MaterializeResult.
            # Otherwise, emit a runtime AssetMaterialization.
            if materialization.asset_key in context.selected_asset_keys:
                yield MaterializeResult(
                    asset_key=materialization.asset_key, metadata=materialization.metadata
                )
                materialized_asset_keys.add(materialization.asset_key)
            else:
                context.log.warning(
                    f"An unexpected asset was materialized: {materialization.asset_key}. "
                    f"Yielding a materialization event."
                )
                yield materialization

        unmaterialized_asset_keys = context.selected_asset_keys - materialized_asset_keys
        if unmaterialized_asset_keys:
            context.log.warning(f"Assets were not materialized: {unmaterialized_asset_keys}")

    @contextmanager
    def process_config_and_initialize_cm_cached(self) -> Iterator["AirbyteWorkspace"]:
        # Hack to avoid reconstructing initialized copies of this resource, which invalidates
        # @cached_method caches. This means that multiple calls to load_airbyte_asset_specs
        # will not trigger multiple API calls to fetch the workspace data.
        # Bespoke impl since @cached_method doesn't play nice with iterators; it's exhausted after
        # the first call.
        if hasattr(self, "_initialized"):
            yield getattr(self, "_initialized")
        else:
            with self.process_config_and_initialize_cm() as initialized_workspace:
                initialized = initialized_workspace
                setattr(self, "_initialized", initialized)
                yield initialized


@beta
class AirbyteWorkspace(BaseAirbyteWorkspace):
    """This resource allows users to programatically interface with the Airbyte REST API to launch
    syncs and monitor their progress for a given Airbyte workspace.

    **Examples:**
    Using OAuth client credentials:

    .. code-block:: python

        import dagster as dg
        from dagster_airbyte import AirbyteWorkspace, build_airbyte_assets_definitions

        airbyte_workspace = AirbyteWorkspace(
            rest_api_base_url=dg.EnvVar("AIRBYTE_REST_API_BASE_URL"),
            configuration_api_base_url=dg.EnvVar("AIRBYTE_CONFIGURATION_API_BASE_URL"),
            workspace_id=dg.EnvVar("AIRBYTE_WORKSPACE_ID"),
            client_id=dg.EnvVar("AIRBYTE_CLIENT_ID"),
            client_secret=dg.EnvVar("AIRBYTE_CLIENT_SECRET"),
        )

        all_airbyte_assets = build_airbyte_assets_definitions(workspace=airbyte_workspace)

        defs = dg.Definitions(
            assets=all_airbyte_assets,
            resources={"airbyte": airbyte_workspace},
        )

    Using basic Authentication:

    .. code-block:: python

        import dagster as dg
        from dagster_airbyte import AirbyteWorkspace, build_airbyte_assets_definitions

        airbyte_workspace = AirbyteWorkspace(
            rest_api_base_url=dg.EnvVar("AIRBYTE_REST_API_BASE_URL"),
            configuration_api_base_url=dg.EnvVar("AIRBYTE_CONFIGURATION_API_BASE_URL"),
            workspace_id=dg.EnvVar("AIRBYTE_WORKSPACE_ID"),
            username=dg.EnvVar("AIRBYTE_USERNAME"),
            password=dg.EnvVar("AIRBYTE_PASSWORD"),
        )

        all_airbyte_assets = build_airbyte_assets_definitions(workspace=airbyte_workspace)

        defs = dg.Definitions(
            assets=all_airbyte_assets,
            resources={"airbyte": airbyte_workspace},
        )

    Using no authentication:

    .. code-block:: python

        import dagster as dg
        from dagster_airbyte import AirbyteWorkspace, build_airbyte_assets_definitions

        airbyte_workspace = AirbyteWorkspace(
            rest_api_base_url=dg.EnvVar("AIRBYTE_REST_API_BASE_URL"),
            configuration_api_base_url=dg.EnvVar("AIRBYTE_CONFIGURATION_API_BASE_URL"),
            workspace_id=dg.EnvVar("AIRBYTE_WORKSPACE_ID"),
        )

        all_airbyte_assets = build_airbyte_assets_definitions(workspace=airbyte_workspace)

        defs = dg.Definitions(
            assets=all_airbyte_assets,
            resources={"airbyte": airbyte_workspace},
        )
    """

    rest_api_base_url: str = Field(
        ...,
        description="The base URL for the Airbyte REST API.",
        examples=[
            "http://localhost:8000/api/public/v1",
            "https://my-airbyte-server.com/api/public/v1",
            "http://airbyte-airbyte-server-svc.airbyte.svc.cluster.local:8001/api/public/v1",
        ],
    )
    configuration_api_base_url: str = Field(
        ...,
        description="The base URL for the Airbyte Configuration API.",
        examples=[
            "http://localhost:8000/api/v1",
            "https://my-airbyte-server.com/api/v1",
            "http://airbyte-airbyte-server-svc.airbyte.svc.cluster.local:8001/api/v1",
        ],
    )
    workspace_id: str = Field(..., description="The Airbyte workspace ID")
    client_id: Optional[str] = Field(default=None, description="The Airbyte client ID.")
    client_secret: Optional[str] = Field(default=None, description="The Airbyte client secret.")
    username: Optional[str] = Field(
        default=None, description="The Airbyte username for authentication."
    )
    password: Optional[str] = Field(
        default=None, description="The Airbyte password for authentication."
    )

    @cached_method
    def get_client(self) -> AirbyteClient:
        return AirbyteClient(
            rest_api_base_url=self.rest_api_base_url,
            configuration_api_base_url=self.configuration_api_base_url,
            workspace_id=self.workspace_id,
            client_id=self.client_id,
            client_secret=self.client_secret,
            username=self.username,
            password=self.password,
            request_max_retries=self.request_max_retries,
            request_retry_delay=self.request_retry_delay,
            request_timeout=self.request_timeout,
            max_items_per_page=self.max_items_per_page,
            poll_interval=self.poll_interval,
            poll_timeout=self.poll_timeout,
            cancel_on_termination=self.cancel_on_termination,
            poll_previous_running_sync=self.poll_previous_running_sync,
        )


@beta
class AirbyteCloudWorkspace(BaseAirbyteWorkspace):
    """This resource allows users to programatically interface with the Airbyte Cloud REST API to launch
    syncs and monitor their progress for a given Airbyte Cloud workspace.

    **Examples:**

    .. code-block:: python

        from dagster_airbyte import AirbyteCloudWorkspace, build_airbyte_assets_definitions

        import dagster as dg

        airbyte_workspace = AirbyteCloudWorkspace(
            workspace_id=dg.EnvVar("AIRBYTE_CLOUD_WORKSPACE_ID"),
            client_id=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_ID"),
            client_secret=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_SECRET"),
        )

        all_airbyte_assets = build_airbyte_assets_definitions(workspace=airbyte_workspace)

        defs = dg.Definitions(
            assets=all_airbyte_assets,
            resources={"airbyte": airbyte_workspace},
        )
    """

    rest_api_base_url: ClassVar[str] = AIRBYTE_CLOUD_REST_API_BASE_URL
    configuration_api_base_url: ClassVar[str] = AIRBYTE_CLOUD_CONFIGURATION_API_BASE_URL
    workspace_id: str = Field(..., description="The Airbyte workspace ID")
    client_id: str = Field(..., description="The Airbyte client ID.")
    client_secret: str = Field(..., description="The Airbyte client secret.")

    @cached_method
    def get_client(self) -> AirbyteClient:
        return AirbyteClient(
            rest_api_base_url=self.rest_api_base_url,
            configuration_api_base_url=self.configuration_api_base_url,
            workspace_id=self.workspace_id,
            client_id=self.client_id,
            client_secret=self.client_secret,
            request_max_retries=self.request_max_retries,
            request_retry_delay=self.request_retry_delay,
            request_timeout=self.request_timeout,
            max_items_per_page=self.max_items_per_page,
            poll_interval=self.poll_interval,
            poll_timeout=self.poll_timeout,
            cancel_on_termination=self.cancel_on_termination,
            poll_previous_running_sync=self.poll_previous_running_sync,
        )


@public
@beta
def load_airbyte_asset_specs(
    workspace: BaseAirbyteWorkspace,
    dagster_airbyte_translator: Optional[DagsterAirbyteTranslator] = None,
    connection_selector_fn: Optional[Callable[[AirbyteConnection], bool]] = None,
) -> Sequence[AssetSpec]:
    """Returns a list of AssetSpecs representing the Airbyte content in the workspace.

    Args:
        workspace (BaseAirbyteWorkspace): The Airbyte workspace to fetch assets from.
        dagster_airbyte_translator (Optional[DagsterAirbyteTranslator], optional): The translator to use
            to convert Airbyte content into :py:class:`dagster.AssetSpec`.
            Defaults to :py:class:`DagsterAirbyteTranslator`.
        connection_selector_fn (Optional[Callable[[AirbyteConnection], bool]]): A function that allows for filtering
            which Airbyte connection assets are created for.

    Returns:
        List[AssetSpec]: The set of assets representing the Airbyte content in the workspace.

    Examples:
        Loading the asset specs for a given Airbyte workspace:

        .. code-block:: python

            from dagster_airbyte import AirbyteWorkspace, load_airbyte_asset_specs

            import dagster as dg

            airbyte_workspace = AirbyteWorkspace(
                workspace_id=dg.EnvVar("AIRBYTE_WORKSPACE_ID"),
                client_id=dg.EnvVar("AIRBYTE_CLIENT_ID"),
                client_secret=dg.EnvVar("AIRBYTE_CLIENT_SECRET"),
            )

            airbyte_specs = load_airbyte_asset_specs(airbyte_workspace)
            dg.Definitions(assets=airbyte_specs)

        Filter connections by name:

        .. code-block:: python

            from dagster_airbyte import AirbyteWorkspace, load_airbyte_asset_specs

            import dagster as dg

            airbyte_workspace = AirbyteWorkspace(
                workspace_id=dg.EnvVar("AIRBYTE_WORKSPACE_ID"),
                client_id=dg.EnvVar("AIRBYTE_CLIENT_ID"),
                client_secret=dg.EnvVar("AIRBYTE_CLIENT_SECRET"),
            )

            airbyte_specs = load_airbyte_asset_specs(
                workspace=airbyte_workspace,
                connection_selector_fn=lambda connection: connection.name in ["connection1", "connection2"]
            )
            dg.Definitions(assets=airbyte_specs)
    """
    dagster_airbyte_translator = dagster_airbyte_translator or DagsterAirbyteTranslator()

    with workspace.process_config_and_initialize_cm_cached() as initialized_workspace:
        return [
            spec.merge_attributes(
                metadata={DAGSTER_AIRBYTE_TRANSLATOR_METADATA_KEY: dagster_airbyte_translator}
            )
            for spec in check.is_list(
                AirbyteWorkspaceDefsLoader(
                    workspace=initialized_workspace,
                    translator=dagster_airbyte_translator,
                    connection_selector_fn=connection_selector_fn,
                )
                .build_defs()
                .assets,
                AssetSpec,
            )
        ]


@public
@superseded(additional_warn_text="Use load_airbyte_asset_specs instead.")
def load_airbyte_cloud_asset_specs(
    workspace: AirbyteCloudWorkspace,
    dagster_airbyte_translator: Optional[DagsterAirbyteTranslator] = None,
    connection_selector_fn: Optional[Callable[[AirbyteConnection], bool]] = None,
) -> Sequence[AssetSpec]:
    """Returns a list of AssetSpecs representing the Airbyte content in the workspace.

    Args:
        workspace (AirbyteCloudWorkspace): The Airbyte Cloud workspace to fetch assets from.
        dagster_airbyte_translator (Optional[DagsterAirbyteTranslator], optional): The translator to use
            to convert Airbyte content into :py:class:`dagster.AssetSpec`.
            Defaults to :py:class:`DagsterAirbyteTranslator`.
        connection_selector_fn (Optional[Callable[[AirbyteConnection], bool]]): A function that allows for filtering
            which Airbyte connection assets are created for.

    Returns:
        List[AssetSpec]: The set of assets representing the Airbyte content in the workspace.

    Examples:
        Loading the asset specs for a given Airbyte Cloud workspace:

        .. code-block:: python

            from dagster_airbyte import AirbyteCloudWorkspace, load_airbyte_cloud_asset_specs

            import dagster as dg

            airbyte_cloud_workspace = AirbyteCloudWorkspace(
                workspace_id=dg.EnvVar("AIRBYTE_CLOUD_WORKSPACE_ID"),
                client_id=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_ID"),
                client_secret=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_SECRET"),
            )

            airbyte_cloud_specs = load_airbyte_cloud_asset_specs(airbyte_cloud_workspace)
            dg.Definitions(assets=airbyte_cloud_specs)

        Filter connections by name:

        .. code-block:: python

            from dagster_airbyte import AirbyteCloudWorkspace, load_airbyte_cloud_asset_specs

            import dagster as dg

            airbyte_cloud_workspace = AirbyteCloudWorkspace(
                workspace_id=dg.EnvVar("AIRBYTE_CLOUD_WORKSPACE_ID"),
                client_id=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_ID"),
                client_secret=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_SECRET"),
            )

            airbyte_cloud_specs = load_airbyte_cloud_asset_specs(
                workspace=airbyte_cloud_workspace,
                connection_selector_fn=lambda connection: connection.name in ["connection1", "connection2"]
            )
            dg.Definitions(assets=airbyte_cloud_specs)
    """
    return load_airbyte_asset_specs(
        workspace=workspace,
        dagster_airbyte_translator=dagster_airbyte_translator,
        connection_selector_fn=connection_selector_fn,
    )


@record
class AirbyteWorkspaceDefsLoader(StateBackedDefinitionsLoader[AirbyteWorkspaceData]):
    workspace: Union[AirbyteWorkspace, AirbyteCloudWorkspace]
    translator: DagsterAirbyteTranslator
    connection_selector_fn: Optional[Callable[[AirbyteConnection], bool]]

    @property
    def defs_key(self) -> str:
        return f"{AIRBYTE_RECONSTRUCTION_METADATA_KEY_PREFIX}.{self.workspace.workspace_id}"

    def fetch_state(self) -> AirbyteWorkspaceData:
        return self.workspace.fetch_airbyte_workspace_data()

    def defs_from_state(self, state: AirbyteWorkspaceData) -> Definitions:
        all_asset_specs = [
            self.translator.get_asset_spec(props)
            for props in state.to_airbyte_connection_table_props_data()
            if not self.connection_selector_fn
            or self.connection_selector_fn(state.connections_by_id[props.connection_id])
        ]

        return Definitions(assets=all_asset_specs)
