import logging
import time
import json
from typing import Optional

import requests
from dagster import (
    get_dagster_logger, 
    __version__,
    resource,
    StringSource,
    Failure,
    Field
)
from requests.exceptions import RequestException
class AirbyteResource:
    """
    This class exposes methods on top of the Airbyte REST API.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: str = "8000",
        request_max_retries: int = 3,
        request_retry_delay: float = 0.25,
        log: logging.Logger = get_dagster_logger(),
    ):
        self._host = host
        self._port = port
        self._request_max_retries = request_max_retries
        self._request_retry_delay = request_retry_delay

        self._log = log

    @property
    def api_base_url(self) -> str:
        return f"http://{self._host}:{self._port}/api/v1"
    
    def make_request(self, endpoint: str, data: Optional[str]):
        """
        Creates and sends a request to the desired Airbyte REST API endpoint.

        Args:
            endpoint (str): The Fivetran API endpoint to send this request to.
            data (Optional[str]): JSON-formatted data string to be included in the request.

        Returns:
            Dict[str, Any]: Parsed json data from the response to this request
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
                )
                response.raise_for_status()
                return response.json()
            except RequestException as e:
                self._log.error("Request to Airbyte API failed: %s", e)
                if num_retries == self._request_max_retries:
                    break
                num_retries += 1
                time.sleep(self._request_retry_delay)

        raise Failure("Exceeded max number of retries.")

    def start_sync(self, connection_id: str) -> dict:
        return self.make_request(
            endpoint="/connections/sync",
            data={"connectionId": connection_id}
        )
    
    def get_job_status(self, job_id: int) -> dict:
        return self.make_request(
            endpoint="/jobs/get",
            data={"id": job_id}
        )

    def sync_and_poll(
        self,
        connection_id: str,
    ):
        """
        Initializes a sync operation for the given connector, and polls until it completes.

        Args:
            connection_id (str): The Airbyte Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.
            poll_interval (float): The time (in seconds) that will be waited between successive polls.
            poll_timeout (float): The maximum time that will waited before this operation is timed
                out. By default, this will never time out.

        Returns:
            :py:class:`~DbtCloudOutput`:
                Object containing details about the connector and the tables it updates
        """
        job_id = self.start_sync(connection_id)
        self._log.info(
            f"Job {job_id} initialized for connection_id={connection_id}.
        )
        job_response = self.get_job_status(job_id)
        job_status = job_response.get("job").get("status")

        while job_status == "running":
            job_response = self.get_job_status(job_id)
            job_status = job_response.get("job").get("status")
            time.sleep(3)
            
        return AirbyteOutput(job_details=job_response.get("job"))


@resource(
    config_schema={
        "host": Field(
            StringSource,
            is_required=True,
            description="The Airbyte Server Address",
        ),
        "port": Field(
            StringSource,
            is_required=False,
            description="Port for the Airbyte Server",
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
    <https://docs.dagster.io/overview/configuration#configured>`_ method.

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
        request_max_retries=context.resource_config["request_max_retries"],
        request_retry_delay=context.resource_config["request_retry_delay"],
        log=context.log,
    )
