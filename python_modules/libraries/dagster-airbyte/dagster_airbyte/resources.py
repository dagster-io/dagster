import hashlib
import json
import logging
import sys
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Mapping, Optional, cast

import requests
from dagster import (
    Failure,
    Field,
    StringSource,
    _check as check,
    get_dagster_logger,
    resource,
)
from dagster._config.field_utils import Permissive
from dagster._utils.merger import deep_merge_dicts
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


class AirbyteResource:
    """
    This class exposes methods on top of the Airbyte REST API.
    """

    def __init__(
        self,
        host: str,
        port: str,
        use_https: bool,
        request_max_retries: int = 3,
        request_retry_delay: float = 0.25,
        request_timeout: int = 15,
        request_additional_params: Optional[Mapping[str, Any]] = None,
        log: logging.Logger = get_dagster_logger(),
        forward_logs: bool = True,
        cancel_sync_on_run_termination: bool = True,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self._host = host
        self._port = port
        self._use_https = use_https
        self._request_max_retries = request_max_retries
        self._request_retry_delay = request_retry_delay
        self._request_timeout = request_timeout
        self._additional_request_params = request_additional_params or dict()

        self._log = log

        self._forward_logs = forward_logs
        self._request_cache: Dict[str, Optional[Mapping[str, object]]] = {}
        # Int in case we nest contexts
        self._cache_enabled = 0

        self._username = username
        self._password = password

        self._cancel_sync_on_run_termination = cancel_sync_on_run_termination

    @property
    def api_base_url(self) -> str:
        return (
            ("https://" if self._use_https else "http://")
            + (f"{self._host}:{self._port}" if self._port else self._host)
            + "/api/v1"
        )

    @contextmanager
    def cache_requests(self):
        """
        Context manager that enables caching certain requests to the Airbyte API,
        cleared when the context is exited.
        """
        self.clear_request_cache()
        self._cache_enabled += 1
        try:
            yield
        finally:
            self.clear_request_cache()
            self._cache_enabled -= 1

    def clear_request_cache(self):
        self._request_cache = {}

    def make_request_cached(self, endpoint: str, data: Optional[Mapping[str, object]]):
        if not self._cache_enabled > 0:
            return self.make_request(endpoint, data)
        data_json = json.dumps(data, sort_keys=True)
        sha = hashlib.sha1()
        sha.update(endpoint.encode("utf-8"))
        sha.update(data_json.encode("utf-8"))
        digest = sha.hexdigest()

        if digest not in self._request_cache:
            self._request_cache[digest] = self.make_request(endpoint, data)
        return self._request_cache[digest]

    def make_request(
        self, endpoint: str, data: Optional[Mapping[str, object]]
    ) -> Optional[Mapping[str, object]]:
        """
        Creates and sends a request to the desired Airbyte REST API endpoint.

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
                            timeout=self._request_timeout,
                            auth=(self._username, self._password)
                            if self._username and self._password
                            else None,
                        ),
                        self._additional_request_params,
                    ),
                )
                response.raise_for_status()
                if response.status_code == 204:
                    return None
                return response.json()
            except RequestException as e:
                self._log.error("Request to Airbyte API failed: %s", e)
                if num_retries == self._request_max_retries:
                    break
                num_retries += 1
                time.sleep(self._request_retry_delay)

        raise Failure(f"Max retries ({self._request_max_retries}) exceeded with url: {url}.")

    def cancel_job(self, job_id: int):
        self.make_request(endpoint="/jobs/cancel", data={"id": job_id})

    def get_default_workspace(self):
        workspaces = cast(
            List[Dict[str, Any]],
            check.not_none(self.make_request_cached(endpoint="/workspaces/list", data={})).get(
                "workspaces", []
            ),
        )
        return workspaces[0].get("workspaceId")

    def get_source_definition_by_name(self, name: str, workspace_id: str) -> Optional[str]:
        name_lower = name.lower()
        definitions = self.make_request_cached(
            endpoint="/source_definitions/list_for_workspace", data={"workspaceId": workspace_id}
        )

        return next(
            (
                definition["sourceDefinitionId"]
                for definition in definitions["sourceDefinitions"]
                if definition["name"].lower() == name_lower
            ),
            None,
        )

    def get_destination_definition_by_name(self, name: str, workspace_id: str):
        name_lower = name.lower()
        definitions = cast(
            Dict[str, List[Dict[str, str]]],
            check.not_none(
                self.make_request_cached(
                    endpoint="/destination_definitions/list_for_workspace",
                    data={"workspaceId": workspace_id},
                )
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
    ) -> Dict[str, Any]:
        return cast(
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

    def get_job_status(self, connection_id: str, job_id: int) -> Mapping[str, object]:
        if self._forward_logs:
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
        poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
        poll_timeout: Optional[float] = None,
    ) -> AirbyteOutput:
        """
        Initializes a sync operation for the given connector, and polls until it completes.

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
                time.sleep(poll_interval)
                job_details = self.get_job_status(connection_id, job_id)
                attempts = cast(List, job_details.get("attempts", []))
                cur_attempt = len(attempts)
                # spit out the available Airbyte log info
                if cur_attempt:
                    if self._forward_logs:
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
                and self._cancel_sync_on_run_termination
            ):
                self.cancel_job(job_id)

        return AirbyteOutput(job_details=job_details, connection_details=connection_details)


@resource(
    config_schema={
        "host": Field(
            StringSource,
            is_required=True,
            description="The Airbyte Server Address.",
        ),
        "port": Field(
            StringSource,
            is_required=True,
            description="Port for the Airbyte Server.",
        ),
        "username": Field(
            StringSource,
            description="Username if using basic auth.",
            is_required=False,
        ),
        "password": Field(
            StringSource,
            description="Password if using basic auth.",
            is_required=False,
        ),
        "use_https": Field(
            bool,
            default_value=False,
            description="Use https to connect in Airbyte Server.",
        ),
        "request_max_retries": Field(
            int,
            default_value=3,
            description=(
                "The maximum number of times requests to the Airbyte API should be retried "
                "before failing."
            ),
        ),
        "request_retry_delay": Field(
            float,
            default_value=0.25,
            description="Time (in seconds) to wait between each request retry.",
        ),
        "request_timeout": Field(
            int,
            default_value=15,
            description=(
                "Time (in seconds) after which the requests to Airbyte are declared timed out."
            ),
        ),
        "request_additional_params": Field(
            Permissive(),
            description=(
                "Any additional kwargs to pass to the requests library when making requests to"
                " Airbyte."
            ),
        ),
        "forward_logs": Field(
            bool,
            default_value=True,
            description=(
                "Whether to forward Airbyte logs to the compute log, can be expensive for"
                " long-running syncs."
            ),
        ),
        "cancel_sync_on_run_termination": Field(
            bool,
            default_value=True,
            description=(
                "Whether to cancel a sync in Airbyte if the Dagster runner is terminated. This may"
                " be useful to disable if using Airbyte sources that cannot be cancelled and"
                " resumed easily, or if your Dagster deployment may experience runner interruptions"
                " that do not impact your Airbyte deployment."
            ),
        ),
    },
    description="This resource helps manage Airbyte connectors",
)
def airbyte_resource(context) -> AirbyteResource:
    """
    This resource allows users to programatically interface with the Airbyte REST API to launch
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
    return AirbyteResource(
        host=context.resource_config["host"],
        port=context.resource_config["port"],
        use_https=context.resource_config["use_https"],
        request_max_retries=context.resource_config["request_max_retries"],
        request_retry_delay=context.resource_config["request_retry_delay"],
        request_timeout=context.resource_config["request_timeout"],
        request_additional_params=context.resource_config["request_additional_params"],
        log=context.log,
        forward_logs=context.resource_config["forward_logs"],
        cancel_sync_on_run_termination=context.resource_config["cancel_sync_on_run_termination"],
        username=context.resource_config.get("username"),
        password=context.resource_config.get("password"),
    )
