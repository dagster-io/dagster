import logging
import sys
import time
from typing import Dict, List, Optional, cast

import requests
from dagster_airbyte.types import AirbyteOutput
from requests.exceptions import RequestException

from dagster import Failure, Field, StringSource, __version__
from dagster import _check as check
from dagster import get_dagster_logger, resource

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
        log: logging.Logger = get_dagster_logger(),
    ):
        self._host = host
        self._port = port
        self._use_https = use_https
        self._request_max_retries = request_max_retries
        self._request_retry_delay = request_retry_delay

        self._log = log

    @property
    def api_base_url(self) -> str:
        return (
            ("https://" if self._use_https else "http://")
            + (f"{self._host}:{self._port}" if self._port else self._host)
            + "/api/v1"
        )

    def make_request(
        self, endpoint: str, data: Optional[Dict[str, object]]
    ) -> Optional[Dict[str, object]]:
        """
        Creates and sends a request to the desired Airbyte REST API endpoint.

        Args:
            endpoint (str): The Airbyte API endpoint to send this request to.
            data (Optional[str]): JSON-formatted data string to be included in the request.

        Returns:
            Optional[Dict[str, Any]]: Parsed json data from the response to this request
        """

        headers = {"accept": "application/json"}

        num_retries = 0
        while True:
            try:
                response = requests.request(
                    method="POST",
                    url=self.api_base_url + endpoint,
                    headers=headers,
                    json=data,
                    timeout=15,
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

        raise Failure("Exceeded max number of retries.")

    def cancel_job(self, job_id: int):
        self.make_request(endpoint="/jobs/cancel", data={"id": job_id})

    def get_job_status(self, job_id: int) -> dict:
        return check.not_none(self.make_request(endpoint="/jobs/get", data={"id": job_id}))

    def start_sync(self, connection_id: str) -> Dict[str, object]:
        return check.not_none(
            self.make_request(endpoint="/connections/sync", data={"connectionId": connection_id})
        )

    def get_connection_details(self, connection_id: str) -> Dict[str, object]:
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
                        f"Timeout: Airbyte job {job_id} is not ready after the timeout {poll_timeout} seconds"
                    )
                time.sleep(poll_interval)
                job_details = self.get_job_status(job_id)
                attempts = cast(List, job_details.get("attempts", []))
                cur_attempt = len(attempts)
                # spit out the available Airbyte log info
                if cur_attempt:
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
            if state not in (AirbyteState.SUCCEEDED, AirbyteState.ERROR, AirbyteState.CANCELLED):
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
            is_required=False,
            description="Port for the Airbyte Server.",
        ),
        "use_https": Field(
            bool,
            default_value=False,
            description="Use https to connect in Airbyte Server.",
        ),
        "request_max_retries": Field(
            int,
            default_value=3,
            description="The maximum number of times requests to the Airbyte API should be retried "
            "before failing.",
        ),
        "request_retry_delay": Field(
            float,
            default_value=0.25,
            description="Time (in seconds) to wait between each request retry.",
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
        log=context.log,
    )
