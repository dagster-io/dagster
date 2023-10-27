import hashlib
import json
import logging
import sys
import time
from abc import abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, List, Mapping, Optional, cast

import requests
from dagster import (
    ConfigurableResource,
    Failure,
    _check as check,
    get_dagster_logger,
    resource,
)
from dagster._config.pythonic_config import infer_schema_from_config_class
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from dagster._utils.cached_method import cached_method
from dagster._utils.merger import deep_merge_dicts
from pydantic import Field
from requests.exceptions import RequestException

from dagster_airbyte.types import AirbyteOutput

DEFAULT_POLL_INTERVAL_SECONDS = 10


class AirbyteState:
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    CANCELLED = "cancelled"
    PENDING = "pending"
    FAILED = "failed"
    ERROR = "error"
    INCOMPLETE = "incomplete"


class AirbyteResourceState:
    def __init__(self) -> None:
        self.request_cache: Dict[str, Optional[Mapping[str, object]]] = {}
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
        self, endpoint: str, data: Optional[Mapping[str, object]] = None, method: str = "POST"
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
                request_args: Dict[str, Any] = dict(
                    method=method,
                    url=url,
                    headers=headers,
                    timeout=self.request_timeout,
                )
                if data:
                    request_args["json"] = data

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
        job_info = cast(Dict[str, object], job_details.get("job", {}))
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
                attempts = cast(List, job_details.get("attempts", []))
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

                job_info = cast(Dict[str, object], job_details.get("job", {}))
                state = job_info.get("status")

                if state in (AirbyteState.RUNNING, AirbyteState.PENDING, AirbyteState.INCOMPLETE):
                    continue
                elif state == AirbyteState.SUCCEEDED:
                    break
                elif state == AirbyteState.ERROR:
                    raise Failure(f"Job failed: {job_id}")
                elif state == AirbyteState.CANCELLED:
                    raise Failure(f"Job was cancelled: {job_id}")
                else:
                    raise Failure(f"Encountered unexpected state `{state}` for job_id {job_id}")
        finally:
            # if Airbyte sync has not completed, make sure to cancel it so that it doesn't outlive
            # the python process
            if (
                state not in (AirbyteState.SUCCEEDED, AirbyteState.ERROR, AirbyteState.CANCELLED)
                and self.cancel_sync_on_run_termination
            ):
                self.cancel_job(job_id)

        return AirbyteOutput(job_details=job_details, connection_details=connection_details)


class AirbyteCloudResource(BaseAirbyteResource):
    """This resource allows users to programatically interface with the Airbyte Cloud API to launch
    syncs and monitor their progress.

    **Examples:**

    .. code-block:: python

        from dagster import job, EnvVar
        from dagster_airbyte import AirbyteResource

        my_airbyte_resource = AirbyteCloudResource(
            api_key=EnvVar("AIRBYTE_API_KEY"),
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

    api_key: str = Field(..., description="The Airbyte Cloud API key.")

    @property
    def api_base_url(self) -> str:
        return "https://api.airbyte.com/v1"

    @property
    def all_additional_request_params(self) -> Mapping[str, Any]:
        return {"headers": {"Authorization": f"Bearer {self.api_key}", "User-Agent": "dagster"}}

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

    def make_request(
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
            List[Dict[str, Any]],
            check.not_none(self.make_request_cached(endpoint="/workspaces/list", data={})).get(
                "workspaces", []
            ),
        )
        return workspaces[0]["workspaceId"]

    def get_source_definition_by_name(self, name: str) -> Optional[str]:
        name_lower = name.lower()
        definitions = self.make_request_cached(endpoint="/source_definitions/list", data={})

        return next(
            (
                definition["sourceDefinitionId"]
                for definition in definitions["sourceDefinitions"]
                if definition["name"].lower() == name_lower
            ),
            None,
        )

    def get_destination_definition_by_name(self, name: str):
        name_lower = name.lower()
        definitions = cast(
            Dict[str, List[Dict[str, str]]],
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
            Dict[str, Any],
            check.not_none(
                self.make_request(endpoint="/sources/discover_schema", data={"sourceId": source_id})
            ),
        )
        return result["catalogId"]

    def get_source_schema(self, source_id: str) -> Mapping[str, Any]:
        return cast(
            Dict[str, Any],
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
            Dict[str, Any],
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
                Dict[str, Any],
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
            job = next((job for job in cast(List, out["jobs"]) if job["job"]["id"] == job_id), None)

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
        job_info = cast(Dict[str, object], job_details.get("job", {}))
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
                attempts = cast(List, job_details.get("attempts", []))
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

                job_info = cast(Dict[str, object], job_details.get("job", {}))
                state = job_info.get("status")

                if state in (AirbyteState.RUNNING, AirbyteState.PENDING, AirbyteState.INCOMPLETE):
                    continue
                elif state == AirbyteState.SUCCEEDED:
                    break
                elif state == AirbyteState.ERROR:
                    raise Failure(f"Job failed: {job_id}")
                elif state == AirbyteState.CANCELLED:
                    raise Failure(f"Job was cancelled: {job_id}")
                else:
                    raise Failure(f"Encountered unexpected state `{state}` for job_id {job_id}")
        finally:
            # if Airbyte sync has not completed, make sure to cancel it so that it doesn't outlive
            # the python process
            if (
                state not in (AirbyteState.SUCCEEDED, AirbyteState.ERROR, AirbyteState.CANCELLED)
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
    <https://docs.dagster.io/concepts/configuration/configured>`_ method.

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


@dagster_maintained_resource
@resource(config_schema=infer_schema_from_config_class(AirbyteCloudResource))
def airbyte_cloud_resource(context) -> AirbyteCloudResource:
    """This resource allows users to programatically interface with the Airbyte Cloud REST API to launch
    syncs and monitor their progress. Currently, this resource may only be used with the more basic
    `dagster-airbyte` APIs, including the ops and assets.

    """
    return AirbyteCloudResource.from_resource_context(context)
