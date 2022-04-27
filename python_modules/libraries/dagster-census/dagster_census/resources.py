import datetime
import json
import logging
import time
from typing import Any, Dict, Optional

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException

from dagster import Failure, Field, StringSource, __version__, get_dagster_logger, resource

from .types import CensusOutput

CENSUS_API_BASE = "app.getcensus.com/api"
CENSUS_VERSION = "v1"

DEFAULT_POLL_INTERVAL = 10


class CensusResource:
    """
    This class exposes methods on top of the Census REST API.
    """

    def __init__(
        self,
        api_key: str,
        request_max_retries: int = 3,
        request_retry_delay: float = 0.25,
        log: logging.Logger = get_dagster_logger(),
    ):
        self.api_key = api_key

        self._request_max_retries = request_max_retries
        self._request_retry_delay = request_retry_delay

        self._log = log

    @property
    def _api_key(self):
        if self.api_key.startswith("secret-token:"):
            return self.api_key
        return "secret-token:" + self.api_key

    @property
    def api_base_url(self) -> str:
        return f"https://{CENSUS_API_BASE}/{CENSUS_VERSION}"

    def make_request(self, method: str, endpoint: str, data: str = None) -> Dict[str, Any]:
        """
        Creates and sends a request to the desired Census API endpoint.

        Args:
            method (str): The http method to use for this request (e.g. "POST", "GET", "PATCH").
            endpoint (str): The Census API endpoint to send this request to.
            data (Optional[str]): JSON-formatted data string to be included in the request.

        Returns:
            Dict[str, Any]: JSON data from the response to this request
        """
        headers = {
            "User-Agent": f"dagster-census/{__version__}",
            "Content-Type": "application/json;version=2",
        }

        num_retries = 0
        while True:
            try:
                response = requests.request(
                    method=method,
                    url=f"{self.api_base_url}/{endpoint}",
                    headers=headers,
                    auth=HTTPBasicAuth("bearer", self._api_key),
                    data=data,
                )
                response.raise_for_status()
                return response.json()
            except RequestException as e:
                self._log.error("Request to Census API failed: %s", e)
                if num_retries == self._request_max_retries:
                    break
                num_retries += 1
                time.sleep(self._request_retry_delay)

        raise Failure("Exceeded max number of retries.")

    def get_sync(self, sync_id: int) -> Dict[str, Any]:
        """
        Gets details about a given sync from the Census API.

        Args:
            sync_id (int): The Census Sync ID.

        Returns:
            Dict[str, Any]: JSON data from the response to this request
        """
        return self.make_request(method="GET", endpoint=f"syncs/{sync_id}")

    def get_source(self, source_id: int) -> Dict[str, Any]:
        """
        Gets details about a given source from the Census API.

        Args:
            source_id (int): The Census Source ID.

        Returns:
            Dict[str, Any]: JSON data from the response to this request
        """
        return self.make_request(method="GET", endpoint=f"sources/{source_id}")

    def get_destination(self, destination_id: int) -> Dict[str, Any]:
        """
        Gets details about a given destination from the Census API.

        Args:
            destination_id (int): The Census Destination ID.

        Returns:
            Dict[str, Any]: JSON data from the response to this request
        """
        return self.make_request(method="GET", endpoint=f"destinations/{destination_id}")

    def get_sync_run(self, sync_run_id: int) -> Dict[str, Any]:
        """
        Gets details about a specific sync run from the Census API.

        Args:
            sync_run_id (int): The Census Sync Run ID.

        Returns:
            Dict[str, Any]: JSON data from the response to this request
        """
        return self.make_request(method="GET", endpoint=f"sync_runs/{sync_run_id}")

    def poll_sync_run(
        self,
        sync_run_id: int,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        poll_timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Given a Census sync run, poll until the run is complete

        Args:
            sync_id (int): The Census Sync Run ID.
            poll_interval (float): The time (in seconds) that will be waited between successive polls.
            poll_timeout (float): The maximum time that will waited before this operation is timed
                out. By default, this will never time out.

        Returns:
            Dict[str, Any]: JSON data from the response to this request
        """
        log_url = f"https://app.getcensus.com/syncs_runs/{sync_run_id}"
        poll_start = datetime.datetime.now()

        while True:
            time.sleep(poll_interval)
            response_dict = self.get_sync_run(sync_run_id)
            if "data" not in response_dict.keys():
                raise ValueError(
                    f"Getting status of sync failed, please visit Census Logs at {log_url} to see more."
                )

            sync_id = response_dict["data"]["sync_id"]

            if response_dict["status"] == "working":
                self._log.debug(
                    f"Sync {sync_id} still running after {datetime.datetime.now() - poll_start}."
                )
                continue

            if poll_timeout and datetime.datetime.now() > poll_start + datetime.timedelta(
                seconds=poll_timeout
            ):
                raise Failure(
                    f"Sync for sync '{sync_id}' timed out after {datetime.datetime.now() - poll_start}."
                )

            break

        self._log.debug(
            f"Sync {sync_id} has finished running after {datetime.datetime.now() - poll_start}."
        )
        self._log.info(f"View sync details here: {log_url}.")

        return response_dict

    def trigger_sync(self, sync_id: int, force_full_sync: bool = False) -> Dict[str, Any]:
        """
        Trigger an asynchronous run for a specific sync.

        Args:
            sync_id (int): The Census Sync Run ID.
            force_full_sync (bool): If the Sync should perform a full sync

        Returns:
            Dict[str, Any]: JSON data from the response to this request
        """
        data = {"force_full_sync": force_full_sync}
        return self.make_request(
            method="POST", endpoint=f"syncs/{sync_id}/trigger", data=json.dumps(data)
        )

    def trigger_sync_and_poll(
        self,
        sync_id: int,
        force_full_sync: bool = False,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        poll_timeout: Optional[float] = None,
    ) -> CensusOutput:
        """
        Trigger a run for a specific sync and poll until it has completed

        Args:
            sync_id (int): The Census Sync Run ID.
            force_full_sync (bool): If the Sync should perform a full sync
            poll_interval (float): The time (in seconds) that will be waited between successive polls.
            poll_timeout (float): The maximum time that will waited before this operation is timed
                out. By default, this will never time out.

        Returns:
            :py:class:`~CensusOutput`:
                Object containing details about the sync run and the sync details
        """
        sync_details = self.get_sync(sync_id=sync_id)
        source_details = self.get_source(
            source_id=sync_details["data"]["source_attributes"]["connection_id"]
        )["data"]
        destination_details = self.get_destination(
            destination_id=sync_details["data"]["destination_attributes"]["connection_id"]
        )["data"]

        trigger_sync_resp = self.trigger_sync(sync_id=sync_id, force_full_sync=force_full_sync)
        sync_run_details = self.poll_sync_run(
            sync_run_id=trigger_sync_resp["data"]["sync_run_id"],
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )["data"]
        return CensusOutput(
            sync_run=sync_run_details,
            source=source_details,
            destination=destination_details,
        )


@resource(
    config_schema={
        "api_key": Field(
            StringSource,
            is_required=True,
            description="Census API Key.",
        ),
        "request_max_retries": Field(
            int,
            default_value=3,
            description="The maximum number of times requests to the Census API should be retried "
            "before failing.",
        ),
        "request_retry_delay": Field(
            float,
            default_value=0.25,
            description="Time (in seconds) to wait between each request retry.",
        ),
    },
    description="This resource helps manage Census connectors",
)
def census_resource(context) -> CensusResource:
    """
    This resource allows users to programatically interface with the Census REST API to launch
    syncs and monitor their progress. This currently implements only a subset of the functionality
    exposed by the API.

    **Examples:**

    .. code-block:: python

        from dagster import job
        from dagster_census import census_resource

        my_census_resource = census_resource.configured(
            {
                "api_key": {"env": "CENSUS_API_KEY"},
            }
        )

        @job(resource_defs={"census":my_census_resource})
        def my_census_job():
            ...

    """
    return CensusResource(
        api_key=context.resource_config["api_key"],
        request_max_retries=context.resource_config["request_max_retries"],
        request_retry_delay=context.resource_config["request_retry_delay"],
        log=context.log,
    )
