import hashlib
import json
import logging
import sys
import time
from abc import abstractmethod
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Optional, cast

import requests
from dagster import (
    AssetExecutionContext,
    AssetMaterialization,
    ConfigurableResource,
    Definitions,
    Failure,
    InitResourceContext,
    MaterializeResult,
    _check as check,
    get_dagster_logger,
    resource,
)
from dagster._annotations import beta, public, superseded
from dagster._config.pythonic_config import infer_schema_from_config_class
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_load_context import StateBackedDefinitionsLoader
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from dagster._record import record
from dagster._utils.cached_method import cached_method
from dagster._utils.merger import deep_merge_dicts
from dagster_shared.dagster_model import DagsterModel
from pydantic import Field, PrivateAttr
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

AIRBYTE_REST_API_BASE = "https://api.airbyte.com"
AIRBYTE_REST_API_VERSION = "v1"

AIRBYTE_CONFIGURATION_API_BASE = "https://cloud.airbyte.com/api"
AIRBYTE_CONFIGURATION_API_VERSION = "v1"

DEFAULT_POLL_INTERVAL_SECONDS = 10

# The access token expire every 3 minutes in Airbyte Cloud.
# Refresh is needed after 2.5 minutes to avoid the "token expired" error message.
AIRBYTE_CLOUD_REFRESH_TIMEDELTA_SECONDS = 150

AIRBYTE_RECONSTRUCTION_METADATA_KEY_PREFIX = "dagster-airbyte/reconstruction_metadata"


class AirbyteResourceState:
    def __init__(self) -> None:
        self.request_cache: dict[str, Optional[Mapping[str, object]]] = {}
        # Int in case we nest contexts
        self.cache_enabled = 0


class BaseAirbyteResource(ConfigurableResource):
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
    cancel_sync_on_run_termination: bool = Field(
        default=True,
        description=(
            "Whether to cancel a sync in Airbyte if the Dagster runner is terminated. This may"
            " be useful to disable if using Airbyte sources that cannot be cancelled and"
            " resumed easily, or if your Dagster deployment may experience runner interruptions"
            " that do not impact your Airbyte deployment."
        ),
    )
    poll_interval: float = Field(
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        description="Time (in seconds) to wait between checking a sync's status.",
    )

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @property
    @cached_method
    def _log(self) -> logging.Logger:
        return get_dagster_logger()

    @property
    @abstractmethod
    def api_base_url(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def all_additional_request_params(self) -> Mapping[str, Any]:
        raise NotImplementedError()

    def make_request(
        self,
        endpoint: str,
        data: Optional[Mapping[str, object]] = None,
        method: str = "POST",
        include_additional_request_params: bool = True,
    ) -> Optional[Mapping[str, object]]:
        """Creates and sends a request to the desired Airbyte REST API endpoint.

        Args:
            endpoint (str): The Airbyte API endpoint to send this request to.
            data (Optional[str]): JSON-formatted data string to be included in the request.

        Returns:
            Optional[Dict[str, Any]]: Parsed json data from the response to this request
        """
        url = self.api_base_url + endpoint
        headers = {"accept": "application/json"}

        num_retries = 0
        while True:
            try:
                request_args: dict[str, Any] = dict(
                    method=method,
                    url=url,
                    headers=headers,
                    timeout=self.request_timeout,
                )
                if data:
                    request_args["json"] = data

                if include_additional_request_params:
                    request_args = deep_merge_dicts(
                        request_args,
                        self.all_additional_request_params,
                    )

                response = requests.request(
                    **request_args,
                )
                response.raise_for_status()
                if response.status_code == 204:
                    return None
                return response.json()
            except RequestException as e:
                self._log.error("Request to Airbyte API failed: %s", e)
                if num_retries == self.request_max_retries:
                    break
                num_retries += 1
                time.sleep(self.request_retry_delay)

        raise Failure(f"Max retries ({self.request_max_retries}) exceeded with url: {url}.")

    @abstractmethod
    def start_sync(self, connection_id: str) -> Mapping[str, object]:
        raise NotImplementedError()

    @abstractmethod
    def get_connection_details(self, connection_id: str) -> Mapping[str, object]:
        raise NotImplementedError()

    @abstractmethod
    def get_job_status(self, connection_id: str, job_id: int) -> Mapping[str, object]:
        raise NotImplementedError()

    @abstractmethod
    def cancel_job(self, job_id: int):
        raise NotImplementedError()

    @property
    @abstractmethod
    def _should_forward_logs(self) -> bool:
        raise NotImplementedError()

    def sync_and_poll(
        self,
        connection_id: str,
        poll_interval: Optional[float] = None,
        poll_timeout: Optional[float] = None,
    ) -> AirbyteOutput:
        """Initializes a sync operation for the given connector, and polls until it completes.

        Args:
            connection_id (str): The Airbyte Connector ID. You can retrieve this value from the
                "Connection" tab of a given connection in the Arbyte UI.
            poll_interval (float): The time (in seconds) that will be waited between successive polls.
            poll_timeout (float): The maximum time that will waited before this operation is timed
                out. By default, this will never time out.

        Returns:
            :py:class:`~AirbyteOutput`:
                Details of the sync job.
        """
        connection_details = self.get_connection_details(connection_id)
        job_details = self.start_sync(connection_id)
        job_info = cast(dict[str, object], job_details.get("job", {}))
        job_id = cast(int, job_info.get("id"))

        self._log.info(f"Job {job_id} initialized for connection_id={connection_id}.")
        start = time.monotonic()
        logged_attempts = 0
        logged_lines = 0
        state = None

        try:
            while True:
                if poll_timeout and start + poll_timeout < time.monotonic():
                    raise Failure(
                        f"Timeout: Airbyte job {job_id} is not ready after the timeout"
                        f" {poll_timeout} seconds"
                    )
                time.sleep(poll_interval or self.poll_interval)
                job_details = self.get_job_status(connection_id, job_id)
                attempts = cast(list, job_details.get("attempts", []))
                cur_attempt = len(attempts)
                # spit out the available Airbyte log info
                if cur_attempt:
                    if self._should_forward_logs:
                        log_lines = attempts[logged_attempts].get("logs", {}).get("logLines", [])

                        for line in log_lines[logged_lines:]:
                            sys.stdout.write(line + "\n")
                            sys.stdout.flush()
                        logged_lines = len(log_lines)

                    # if there's a next attempt, this one will have no more log messages
                    if logged_attempts < cur_attempt - 1:
                        logged_lines = 0
                        logged_attempts += 1

                job_info = cast(dict[str, object], job_details.get("job", {}))
                state = job_info.get("status")

                if state in (
                    AirbyteJobStatusType.RUNNING,
                    AirbyteJobStatusType.PENDING,
                    AirbyteJobStatusType.INCOMPLETE,
                ):
                    continue
                elif state == AirbyteJobStatusType.SUCCEEDED:
                    break
                elif state == AirbyteJobStatusType.ERROR:
                    raise Failure(f"Job failed: {job_id}")
                elif state == AirbyteJobStatusType.CANCELLED:
                    raise Failure(f"Job was cancelled: {job_id}")
                else:
                    raise Failure(f"Encountered unexpected state `{state}` for job_id {job_id}")
        finally:
            # if Airbyte sync has not completed, make sure to cancel it so that it doesn't outlive
            # the python process
            if (
                state
                not in (
                    AirbyteJobStatusType.SUCCEEDED,
                    AirbyteJobStatusType.ERROR,
                    AirbyteJobStatusType.CANCELLED,
                )
                and self.cancel_sync_on_run_termination
            ):
                self.cancel_job(job_id)

        return AirbyteOutput(job_details=job_details, connection_details=connection_details)


@superseded(
    additional_warn_text=(
        "Using `AirbyteCloudResource` with `build_airbyte_assets`is no longer best practice. "
        "Use `AirbyteCloudWorkspace` with `build_airbyte_assets_definitions` instead."
    )
)
class AirbyteCloudResource(BaseAirbyteResource):
    """This resource allows users to programmatically interface with the Airbyte Cloud API to launch
    syncs and monitor their progress.

    **Examples:**

    .. code-block:: python

        from dagster import job, EnvVar
        from dagster_airbyte import AirbyteResource

        my_airbyte_resource = AirbyteCloudResource(
            client_id=EnvVar("AIRBYTE_CLIENT_ID"),
            client_secret=EnvVar("AIRBYTE_CLIENT_SECRET"),
        )

        airbyte_assets = build_airbyte_assets(
            connection_id="87b7fe85-a22c-420e-8d74-b30e7ede77df",
            destination_tables=["releases", "tags", "teams"],
        )

        defs = Definitions(
            assets=[airbyte_assets],
            resources={"airbyte": my_airbyte_resource},
        )
    """

    client_id: str = Field(..., description="The Airbyte Cloud client ID.")
    client_secret: str = Field(..., description="The Airbyte Cloud client secret.")

    _access_token_value: Optional[str] = PrivateAttr(default=None)
    _access_token_timestamp: Optional[float] = PrivateAttr(default=None)

    def setup_for_execution(self, context: InitResourceContext) -> None:
        # Refresh access token when the resource is initialized
        self._refresh_access_token()

    @property
    def api_base_url(self) -> str:
        return "https://api.airbyte.com/v1"

    @property
    def all_additional_request_params(self) -> Mapping[str, Any]:
        # Make sure the access token is refreshed before using it when calling the API.
        if self._needs_refreshed_access_token():
            self._refresh_access_token()
        return {
            "headers": {
                "Authorization": f"Bearer {self._access_token_value}",
                "User-Agent": "dagster",
            }
        }

    def make_request(
        self,
        endpoint: str,
        data: Optional[Mapping[str, object]] = None,
        method: str = "POST",
        include_additional_request_params: bool = True,
    ) -> Optional[Mapping[str, object]]:
        # Make sure the access token is refreshed before using it when calling the API.
        if include_additional_request_params and self._needs_refreshed_access_token():
            self._refresh_access_token()
        return super().make_request(
            endpoint=endpoint,
            data=data,
            method=method,
            include_additional_request_params=include_additional_request_params,
        )

    def start_sync(self, connection_id: str) -> Mapping[str, object]:
        job_sync = check.not_none(
            self.make_request(
                endpoint="/jobs",
                data={
                    "connectionId": connection_id,
                    "jobType": "sync",
                },
            )
        )
        return {"job": {"id": job_sync["jobId"], "status": job_sync["status"]}}

    def get_connection_details(self, connection_id: str) -> Mapping[str, object]:
        return {}

    def get_job_status(self, connection_id: str, job_id: int) -> Mapping[str, object]:
        job_status = check.not_none(self.make_request(endpoint=f"/jobs/{job_id}", method="GET"))
        return {"job": {"id": job_status["jobId"], "status": job_status["status"]}}

    def cancel_job(self, job_id: int):
        self.make_request(endpoint=f"/jobs/{job_id}", method="DELETE")

    @property
    def _should_forward_logs(self) -> bool:
        # Airbyte Cloud does not support streaming logs yet
        return False

    def _refresh_access_token(self) -> None:
        response = check.not_none(
            self.make_request(
                endpoint="/applications/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                # Must not pass the bearer access token when refreshing it.
                include_additional_request_params=False,
            )
        )
        self._access_token_value = str(response["access_token"])
        self._access_token_timestamp = datetime.now().timestamp()

    def _needs_refreshed_access_token(self) -> bool:
        return (
            not self._access_token_value
            or not self._access_token_timestamp
            or self._access_token_timestamp
            <= datetime.timestamp(
                datetime.now() - timedelta(seconds=AIRBYTE_CLOUD_REFRESH_TIMEDELTA_SECONDS)
            )
        )


class AirbyteResource(BaseAirbyteResource):
    """This resource allows users to programatically interface with the Airbyte REST API to launch
    syncs and monitor their progress.

    **Examples:**

    .. code-block:: python

        from dagster import job, EnvVar
        from dagster_airbyte import AirbyteResource

        my_airbyte_resource = AirbyteResource(
            host=EnvVar("AIRBYTE_HOST"),
            port=EnvVar("AIRBYTE_PORT"),
            # If using basic auth
            username=EnvVar("AIRBYTE_USERNAME"),
            password=EnvVar("AIRBYTE_PASSWORD"),
        )

        airbyte_assets = build_airbyte_assets(
            connection_id="87b7fe85-a22c-420e-8d74-b30e7ede77df",
            destination_tables=["releases", "tags", "teams"],
        )

        defs = Definitions(
            assets=[airbyte_assets],
            resources={"airbyte": my_airbyte_resource},
        )
    """

    host: str = Field(description="The Airbyte server address.")
    port: str = Field(description="Port used for the Airbyte server.")
    username: Optional[str] = Field(default=None, description="Username if using basic auth.")
    password: Optional[str] = Field(default=None, description="Password if using basic auth.")
    use_https: bool = Field(
        default=False, description="Whether to use HTTPS to connect to the Airbyte server."
    )
    forward_logs: bool = Field(
        default=True,
        description=(
            "Whether to forward Airbyte logs to the compute log, can be expensive for"
            " long-running syncs."
        ),
    )
    request_additional_params: Mapping[str, Any] = Field(
        default=dict(),
        description=(
            "Any additional kwargs to pass to the requests library when making requests to Airbyte."
        ),
    )

    @property
    @cached_method
    def _state(self) -> AirbyteResourceState:
        return AirbyteResourceState()

    @property
    @cached_method
    def _log(self) -> logging.Logger:
        return get_dagster_logger()

    @property
    def api_base_url(self) -> str:
        return (
            ("https://" if self.use_https else "http://")
            + (f"{self.host}:{self.port}" if self.port else self.host)
            + "/api/v1"
        )

    @property
    def _should_forward_logs(self) -> bool:
        return self.forward_logs

    @contextmanager
    def cache_requests(self):
        """Context manager that enables caching certain requests to the Airbyte API,
        cleared when the context is exited.
        """
        self.clear_request_cache()
        self._state.cache_enabled += 1
        try:
            yield
        finally:
            self.clear_request_cache()
            self._state.cache_enabled -= 1

    def clear_request_cache(self) -> None:
        self._state.request_cache = {}

    def make_request_cached(self, endpoint: str, data: Optional[Mapping[str, object]]):
        if not self._state.cache_enabled > 0:
            return self.make_request(endpoint, data)
        data_json = json.dumps(data, sort_keys=True)
        sha = hashlib.sha1()
        sha.update(endpoint.encode("utf-8"))
        sha.update(data_json.encode("utf-8"))
        digest = sha.hexdigest()

        if digest not in self._state.request_cache:
            self._state.request_cache[digest] = self.make_request(endpoint, data)
        return self._state.request_cache[digest]

    @property
    def all_additional_request_params(self) -> Mapping[str, Any]:
        auth_param = (
            {"auth": (self.username, self.password)} if self.username and self.password else {}
        )
        return {**auth_param, **self.request_additional_params}

    def make_request(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, endpoint: str, data: Optional[Mapping[str, object]]
    ) -> Optional[Mapping[str, object]]:
        """Creates and sends a request to the desired Airbyte REST API endpoint.

        Args:
            endpoint (str): The Airbyte API endpoint to send this request to.
            data (Optional[str]): JSON-formatted data string to be included in the request.

        Returns:
            Optional[Dict[str, Any]]: Parsed json data from the response to this request
        """
        url = self.api_base_url + endpoint
        headers = {"accept": "application/json"}

        num_retries = 0
        while True:
            try:
                response = requests.request(
                    **deep_merge_dicts(  # type: ignore
                        dict(
                            method="POST",
                            url=url,
                            headers=headers,
                            json=data,
                            timeout=self.request_timeout,
                            auth=(
                                (self.username, self.password)
                                if self.username and self.password
                                else None
                            ),
                        ),
                        self.request_additional_params,
                    ),
                )
                response.raise_for_status()
                if response.status_code == 204:
                    return None
                return response.json()
            except RequestException as e:
                self._log.error("Request to Airbyte API failed: %s", e)
                if num_retries == self.request_max_retries:
                    break
                num_retries += 1
                time.sleep(self.request_retry_delay)

        raise Failure(f"Max retries ({self.request_max_retries}) exceeded with url: {url}.")

    def cancel_job(self, job_id: int):
        self.make_request(endpoint="/jobs/cancel", data={"id": job_id})

    def get_default_workspace(self) -> str:
        workspaces = cast(
            list[dict[str, Any]],
            check.not_none(self.make_request_cached(endpoint="/workspaces/list", data={})).get(
                "workspaces", []
            ),
        )
        return workspaces[0]["workspaceId"]

    def get_source_definition_by_name(self, name: str) -> Optional[str]:
        name_lower = name.lower()
        definitions = check.not_none(
            self.make_request_cached(endpoint="/source_definitions/list", data={})
        )
        source_definitions = cast(list[dict[str, Any]], definitions["sourceDefinitions"])

        return next(
            (
                definition["sourceDefinitionId"]
                for definition in source_definitions
                if definition["name"].lower() == name_lower
            ),
            None,
        )

    def get_destination_definition_by_name(self, name: str):
        name_lower = name.lower()
        definitions = cast(
            dict[str, list[dict[str, str]]],
            check.not_none(
                self.make_request_cached(endpoint="/destination_definitions/list", data={})
            ),
        )
        return next(
            (
                definition["destinationDefinitionId"]
                for definition in definitions["destinationDefinitions"]
                if definition["name"].lower() == name_lower
            ),
            None,
        )

    def get_source_catalog_id(self, source_id: str):
        result = cast(
            dict[str, Any],
            check.not_none(
                self.make_request(endpoint="/sources/discover_schema", data={"sourceId": source_id})
            ),
        )
        return result["catalogId"]

    def get_source_schema(self, source_id: str) -> Mapping[str, Any]:
        return cast(
            dict[str, Any],
            check.not_none(
                self.make_request(endpoint="/sources/discover_schema", data={"sourceId": source_id})
            ),
        )

    def does_dest_support_normalization(
        self, destination_definition_id: str, workspace_id: str
    ) -> bool:
        # Airbyte API changed source of truth for normalization in PR
        # https://github.com/airbytehq/airbyte/pull/21005
        norm_dest_def_spec: bool = cast(
            dict[str, Any],
            check.not_none(
                self.make_request_cached(
                    endpoint="/destination_definition_specifications/get",
                    data={
                        "destinationDefinitionId": destination_definition_id,
                        "workspaceId": workspace_id,
                    },
                )
            ),
        ).get("supportsNormalization", False)

        norm_dest_def: bool = (
            cast(
                dict[str, Any],
                check.not_none(
                    self.make_request_cached(
                        endpoint="/destination_definitions/get",
                        data={
                            "destinationDefinitionId": destination_definition_id,
                        },
                    )
                ),
            )
            .get("normalizationConfig", {})
            .get("supported", False)
        )

        return any([norm_dest_def_spec, norm_dest_def])

    def get_job_status(self, connection_id: str, job_id: int) -> Mapping[str, object]:
        if self.forward_logs:
            return check.not_none(self.make_request(endpoint="/jobs/get", data={"id": job_id}))
        else:
            # the "list all jobs" endpoint doesn't return logs, which actually makes it much more
            # lightweight for long-running syncs with many logs
            out = check.not_none(
                self.make_request(
                    endpoint="/jobs/list",
                    data={
                        "configTypes": ["sync"],
                        "configId": connection_id,
                        # sync should be the most recent, so pageSize 5 is sufficient
                        "pagination": {"pageSize": 5},
                    },
                )
            )
            job = next((job for job in cast(list, out["jobs"]) if job["job"]["id"] == job_id), None)

            return check.not_none(job)

    def start_sync(self, connection_id: str) -> Mapping[str, object]:
        return check.not_none(
            self.make_request(endpoint="/connections/sync", data={"connectionId": connection_id})
        )

    def get_connection_details(self, connection_id: str) -> Mapping[str, object]:
        return check.not_none(
            self.make_request(endpoint="/connections/get", data={"connectionId": connection_id})
        )

    def sync_and_poll(
        self,
        connection_id: str,
        poll_interval: Optional[float] = None,
        poll_timeout: Optional[float] = None,
    ) -> AirbyteOutput:
        """Initializes a sync operation for the given connector, and polls until it completes.

        Args:
            connection_id (str): The Airbyte Connector ID. You can retrieve this value from the
                "Connection" tab of a given connection in the Arbyte UI.
            poll_interval (float): The time (in seconds) that will be waited between successive polls.
            poll_timeout (float): The maximum time that will waited before this operation is timed
                out. By default, this will never time out.

        Returns:
            :py:class:`~AirbyteOutput`:
                Details of the sync job.
        """
        connection_details = self.get_connection_details(connection_id)
        job_details = self.start_sync(connection_id)
        job_info = cast(dict[str, object], job_details.get("job", {}))
        job_id = cast(int, job_info.get("id"))

        self._log.info(f"Job {job_id} initialized for connection_id={connection_id}.")
        start = time.monotonic()
        logged_attempts = 0
        logged_lines = 0
        state = None

        try:
            while True:
                if poll_timeout and start + poll_timeout < time.monotonic():
                    raise Failure(
                        f"Timeout: Airbyte job {job_id} is not ready after the timeout"
                        f" {poll_timeout} seconds"
                    )
                time.sleep(poll_interval or self.poll_interval)
                job_details = self.get_job_status(connection_id, job_id)
                attempts = cast(list, job_details.get("attempts", []))
                cur_attempt = len(attempts)
                # spit out the available Airbyte log info
                if cur_attempt:
                    if self.forward_logs:
                        log_lines = attempts[logged_attempts].get("logs", {}).get("logLines", [])

                        for line in log_lines[logged_lines:]:
                            sys.stdout.write(line + "\n")
                            sys.stdout.flush()
                        logged_lines = len(log_lines)

                    # if there's a next attempt, this one will have no more log messages
                    if logged_attempts < cur_attempt - 1:
                        logged_lines = 0
                        logged_attempts += 1

                job_info = cast(dict[str, object], job_details.get("job", {}))
                state = job_info.get("status")

                if state in (
                    AirbyteJobStatusType.RUNNING,
                    AirbyteJobStatusType.PENDING,
                    AirbyteJobStatusType.INCOMPLETE,
                ):
                    continue
                elif state == AirbyteJobStatusType.SUCCEEDED:
                    break
                elif state == AirbyteJobStatusType.ERROR:
                    raise Failure(f"Job failed: {job_id}")
                elif state == AirbyteJobStatusType.CANCELLED:
                    raise Failure(f"Job was cancelled: {job_id}")
                else:
                    raise Failure(f"Encountered unexpected state `{state}` for job_id {job_id}")
        finally:
            # if Airbyte sync has not completed, make sure to cancel it so that it doesn't outlive
            # the python process
            if (
                state
                not in (
                    AirbyteJobStatusType.SUCCEEDED,
                    AirbyteJobStatusType.ERROR,
                    AirbyteJobStatusType.CANCELLED,
                )
                and self.cancel_sync_on_run_termination
            ):
                self.cancel_job(job_id)

        return AirbyteOutput(job_details=job_details, connection_details=connection_details)


@dagster_maintained_resource
@resource(config_schema=AirbyteResource.to_config_schema())
def airbyte_resource(context) -> AirbyteResource:
    """This resource allows users to programatically interface with the Airbyte REST API to launch
    syncs and monitor their progress. This currently implements only a subset of the functionality
    exposed by the API.

    For a complete set of documentation on the Airbyte REST API, including expected response JSON
    schema, see the `Airbyte API Docs <https://airbyte-public-api-docs.s3.us-east-2.amazonaws.com/rapidoc-api-docs.html#overview>`_.

    To configure this resource, we recommend using the `configured
    <https://legacy-docs.dagster.io/concepts/configuration/configured>`_ method.

    **Examples:**

    .. code-block:: python

        from dagster import job
        from dagster_airbyte import airbyte_resource

        my_airbyte_resource = airbyte_resource.configured(
            {
                "host": {"env": "AIRBYTE_HOST"},
                "port": {"env": "AIRBYTE_PORT"},
                # If using basic auth
                "username": {"env": "AIRBYTE_USERNAME"},
                "password": {"env": "AIRBYTE_PASSWORD"},
            }
        )

        @job(resource_defs={"airbyte":my_airbyte_resource})
        def my_airbyte_job():
            ...

    """
    return AirbyteResource.from_resource_context(context)


@superseded(additional_warn_text=("Use `AirbyteCloudWorkspace` instead."))
@dagster_maintained_resource
@resource(config_schema=infer_schema_from_config_class(AirbyteCloudResource))
def airbyte_cloud_resource(context) -> AirbyteCloudResource:
    """This resource allows users to programatically interface with the Airbyte Cloud REST API to launch
    syncs and monitor their progress. Currently, this resource may only be used with the more basic
    `dagster-airbyte` APIs, including the ops and assets.

    """
    return AirbyteCloudResource.from_resource_context(context)


# -------------
# Resources v2
# -------------


@beta
class AirbyteCloudClient(DagsterModel):
    """This class exposes methods on top of the Airbyte APIs for Airbyte Cloud."""

    workspace_id: str = Field(..., description="The Airbyte workspace ID")
    client_id: str = Field(..., description="The Airbyte client ID.")
    client_secret: str = Field(..., description="The Airbyte client secret.")
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

    _access_token_value: Optional[str] = PrivateAttr(default=None)
    _access_token_timestamp: Optional[float] = PrivateAttr(default=None)

    @property
    @cached_method
    def _log(self) -> logging.Logger:
        return get_dagster_logger()

    @property
    def rest_api_base_url(self) -> str:
        return f"{AIRBYTE_REST_API_BASE}/{AIRBYTE_REST_API_VERSION}"

    @property
    def configuration_api_base_url(self) -> str:
        return f"{AIRBYTE_CONFIGURATION_API_BASE}/{AIRBYTE_CONFIGURATION_API_VERSION}"

    @property
    def all_additional_request_params(self) -> Mapping[str, Any]:
        return {**self.authorization_request_params, **self.user_agent_request_params}

    @property
    def authorization_request_params(self) -> Mapping[str, Any]:
        # Make sure the access token is refreshed before using it when calling the API.
        if self._needs_refreshed_access_token():
            self._refresh_access_token()
        return {
            "Authorization": f"Bearer {self._access_token_value}",
        }

    @property
    def user_agent_request_params(self) -> Mapping[str, Any]:
        return {
            "User-Agent": "dagster",
        }

    def _refresh_access_token(self) -> None:
        response = check.not_none(
            self._make_request(
                method="POST",
                endpoint="applications/token",
                base_url=self.rest_api_base_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                # Must not pass the bearer access token when refreshing it.
                include_additional_request_params=False,
            )
        )
        self._access_token_value = str(response["access_token"])
        self._access_token_timestamp = datetime.now().timestamp()

    def _needs_refreshed_access_token(self) -> bool:
        return (
            not self._access_token_value
            or not self._access_token_timestamp
            or self._access_token_timestamp
            <= (
                datetime.now() - timedelta(seconds=AIRBYTE_CLOUD_REFRESH_TIMEDELTA_SECONDS)
            ).timestamp()
        )

    def _get_session(self, include_additional_request_params: bool) -> requests.Session:
        headers = {"accept": "application/json"}
        if include_additional_request_params:
            headers = {
                **headers,
                **self.all_additional_request_params,
            }
        session = requests.Session()
        session.headers.update(headers)
        return session

    def _make_request(
        self,
        method: str,
        endpoint: str,
        base_url: str,
        data: Optional[Mapping[str, Any]] = None,
        params: Optional[Mapping[str, Any]] = None,
        include_additional_request_params: bool = True,
    ) -> Mapping[str, Any]:
        """Creates and sends a request to the desired Airbyte REST API endpoint.

        Args:
            method (str): The http method to use for this request (e.g. "POST", "GET", "PATCH").
            endpoint (str): The Airbyte API endpoint to send this request to.
            base_url (str): The base url to the Airbyte API to use.
            data (Optional[Dict[str, Any]]): JSON-formatted data string to be included in the request.
            params (Optional[Dict[str, Any]]): JSON-formatted query params to be included in the request.
            include_additional_request_params (bool): Whether to include authorization and user-agent headers
            to the request parameters. Defaults to True.

        Returns:
            Dict[str, Any]: Parsed json data from the response to this request
        """
        url = f"{base_url}/{endpoint}"

        num_retries = 0
        while True:
            try:
                session = self._get_session(
                    include_additional_request_params=include_additional_request_params
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

    def get_connections(self) -> Mapping[str, Any]:
        """Fetches all connections of an Airbyte workspace from the Airbyte REST API."""
        return self._make_request(
            method="GET",
            endpoint="connections",
            base_url=self.rest_api_base_url,
            params={"workspaceIds": self.workspace_id},
        )

    def get_connection_details(self, connection_id) -> Mapping[str, Any]:
        """Fetches details about a given connection from the Airbyte Configuration API.
        The Airbyte Configuration API is an internal and may change in the future.
        """
        # Using the Airbyte Configuration API to get the connection details, including streams and their configs.
        # https://airbyte-public-api-docs.s3.us-east-2.amazonaws.com/rapidoc-api-docs.html#post-/v1/connections/get
        # https://github.com/airbytehq/airbyte-platform/blob/v1.0.0/airbyte-api/server-api/src/main/openapi/config.yaml
        return self._make_request(
            method="POST",
            endpoint="connections/get",
            base_url=self.configuration_api_base_url,
            data={"connectionId": connection_id},
        )

    def get_destination_details(self, destination_id: str) -> Mapping[str, Any]:
        """Fetches details about a given destination from the Airbyte REST API."""
        return self._make_request(
            method="GET",
            endpoint=f"destinations/{destination_id}",
            base_url=self.rest_api_base_url,
        )

    def start_sync_job(self, connection_id: str) -> Mapping[str, Any]:
        return self._make_request(
            method="POST",
            endpoint="jobs",
            base_url=self.rest_api_base_url,
            data={
                "connectionId": connection_id,
                "jobType": "sync",
            },
        )

    def get_job_details(self, job_id: int) -> Mapping[str, Any]:
        return self._make_request(
            method="GET", endpoint=f"jobs/{job_id}", base_url=self.rest_api_base_url
        )

    def cancel_job(self, job_id: int) -> Mapping[str, Any]:
        return self._make_request(
            method="DELETE", endpoint=f"jobs/{job_id}", base_url=self.rest_api_base_url
        )

    def sync_and_poll(
        self,
        connection_id: str,
        poll_interval: Optional[float] = None,
        poll_timeout: Optional[float] = None,
        cancel_on_termination: bool = True,
    ) -> AirbyteOutput:
        """Initializes a sync operation for the given connection, and polls until it completes.

        Args:
            connection_id (str): The Airbyte Connection ID. You can retrieve this value from the
                "Connection" tab of a given connection in the Airbyte UI.
            poll_interval (float): The time (in seconds) that will be waited between successive polls.
            poll_timeout (float): The maximum time that will wait before this operation is timed
                out. By default, this will never time out.
            cancel_on_termination (bool): Whether to cancel a sync in Airbyte if the Dagster runner is terminated.
                This may be useful to disable if using Airbyte sources that cannot be cancelled and
                resumed easily, or if your Dagster deployment may experience runner interruptions
                that do not impact your Airbyte deployment.

        Returns:
            :py:class:`~AirbyteOutput`:
                Details of the sync job.
        """
        connection_details = self.get_connection_details(connection_id)
        start_job_details = self.start_sync_job(connection_id)
        job = AirbyteJob.from_job_details(job_details=start_job_details)

        self._log.info(f"Job {job.id} initialized for connection_id={connection_id}.")
        poll_start = datetime.now()
        poll_interval = (
            poll_interval if poll_interval is not None else DEFAULT_POLL_INTERVAL_SECONDS
        )
        try:
            while True:
                if poll_timeout and datetime.now() > poll_start + timedelta(seconds=poll_timeout):
                    raise Failure(
                        f"Timeout: Airbyte job {job.id} is not ready after the timeout"
                        f" {poll_timeout} seconds"
                    )

                time.sleep(poll_interval)
                # We return these job details in the AirbyteOutput when the job succeeds
                poll_job_details = self.get_job_details(job.id)
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
            if cancel_on_termination and job.status not in (
                AirbyteJobStatusType.SUCCEEDED,
                AirbyteJobStatusType.ERROR,
                AirbyteJobStatusType.CANCELLED,
                AirbyteJobStatusType.FAILED,
            ):
                self.cancel_job(job.id)

        return AirbyteOutput(job_details=poll_job_details, connection_details=connection_details)


@beta
class AirbyteCloudWorkspace(ConfigurableResource):
    """This class represents a Airbyte Cloud workspace and provides utilities
    to interact with Airbyte APIs.
    """

    workspace_id: str = Field(..., description="The Airbyte Cloud workspace ID")
    client_id: str = Field(..., description="The Airbyte Cloud client ID.")
    client_secret: str = Field(..., description="The Airbyte Cloud client secret.")
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

    _client: AirbyteCloudClient = PrivateAttr(default=None)  # type: ignore

    @cached_method
    def get_client(self) -> AirbyteCloudClient:
        return AirbyteCloudClient(
            workspace_id=self.workspace_id,
            client_id=self.client_id,
            client_secret=self.client_secret,
            request_max_retries=self.request_max_retries,
            request_retry_delay=self.request_retry_delay,
            request_timeout=self.request_timeout,
        )

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
        connections = client.get_connections()["data"]

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
    ) -> Sequence[AssetSpec]:
        """Returns a list of AssetSpecs representing the Airbyte content in the workspace.

        Args:
            dagster_airbyte_translator (Optional[DagsterAirbyteTranslator], optional): The translator to use
                to convert Airbyte content into :py:class:`dagster.AssetSpec`.
                Defaults to :py:class:`DagsterAirbyteTranslator`.

        Returns:
            List[AssetSpec]: The set of assets representing the Airbyte content in the workspace.

        Examples:
            Loading the asset specs for a given Airbyte workspace:
            .. code-block:: python

                from dagster_airbyte import AirbyteCloudWorkspace

                import dagster as dg

                airbyte_workspace = AirbyteCloudWorkspace(
                    workspace_id=dg.EnvVar("AIRBYTE_CLOUD_WORKSPACE_ID"),
                    client_id=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_ID"),
                    client_secret=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_SECRET"),
                )

                airbyte_specs = airbyte_workspace.load_asset_specs()
                defs = dg.Definitions(assets=airbyte_specs, resources={"airbyte": airbyte_workspace}
        """
        dagster_airbyte_translator = dagster_airbyte_translator or DagsterAirbyteTranslator()

        return load_airbyte_cloud_asset_specs(
            workspace=self, dagster_airbyte_translator=dagster_airbyte_translator
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
                        f"Table generated via Airbyte Cloud sync "
                        f"for connection {connection.name}: {connection_table_name}"
                    ),
                    metadata=stream_asset_spec.metadata,
                )

    @public
    @beta
    def sync_and_poll(self, context: AssetExecutionContext):
        """Executes a sync and poll process to materialize Airbyte Cloud assets.
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


@beta
def load_airbyte_cloud_asset_specs(
    workspace: AirbyteCloudWorkspace,
    dagster_airbyte_translator: Optional[DagsterAirbyteTranslator] = None,
) -> Sequence[AssetSpec]:
    """Returns a list of AssetSpecs representing the Airbyte content in the workspace.

    Args:
        workspace (AirbyteCloudWorkspace): The Airbyte Cloud workspace to fetch assets from.
        dagster_airbyte_translator (Optional[DagsterAirbyteTranslator], optional): The translator to use
            to convert Airbyte content into :py:class:`dagster.AssetSpec`.
            Defaults to :py:class:`DagsterAirbyteTranslator`.

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
            defs = dg.Definitions(assets=airbyte_cloud_specs)
    """
    dagster_airbyte_translator = dagster_airbyte_translator or DagsterAirbyteTranslator()

    with workspace.process_config_and_initialize_cm() as initialized_workspace:
        return [
            spec.merge_attributes(
                metadata={DAGSTER_AIRBYTE_TRANSLATOR_METADATA_KEY: dagster_airbyte_translator}
            )
            for spec in check.is_list(
                AirbyteCloudWorkspaceDefsLoader(
                    workspace=initialized_workspace,
                    translator=dagster_airbyte_translator,
                )
                .build_defs()
                .assets,
                AssetSpec,
            )
        ]


@record
class AirbyteCloudWorkspaceDefsLoader(StateBackedDefinitionsLoader[Mapping[str, Any]]):
    workspace: AirbyteCloudWorkspace
    translator: DagsterAirbyteTranslator

    @property
    def defs_key(self) -> str:
        return f"{AIRBYTE_RECONSTRUCTION_METADATA_KEY_PREFIX}/{self.workspace.workspace_id}"

    def fetch_state(self) -> AirbyteWorkspaceData:  # pyright: ignore[reportIncompatibleMethodOverride]
        return self.workspace.fetch_airbyte_workspace_data()

    def defs_from_state(self, state: AirbyteWorkspaceData) -> Definitions:  # pyright: ignore[reportIncompatibleMethodOverride]
        all_asset_specs = [
            self.translator.get_asset_spec(props)
            for props in state.to_airbyte_connection_table_props_data()
        ]

        return Definitions(assets=all_asset_specs)
