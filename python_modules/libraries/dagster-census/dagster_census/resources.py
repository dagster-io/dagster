import datetime
import json
import logging
import time
from collections.abc import Mapping
from typing import Any, Optional

import pydantic
import requests
from dagster import ConfigurableResource, Failure, __version__, get_dagster_logger
from dagster_shared.utils.cached_method import cached_method
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException

from dagster_census.translator import CensusSync, CensusWorkspaceData
from dagster_census.types import CensusOutput

CENSUS_API_BASE = "app.getcensus.com/api"
CENSUS_VERSION = "v1"

DEFAULT_POLL_INTERVAL = 10

SYNC_RUN_STATUSES = {"completed", "failed", "queued", "skipped", "working"}


class CensusResource(ConfigurableResource):
    """This resource allows users to programatically interface with the Census REST API to launch
    syncs and monitor their progress. This currently implements only a subset of the functionality
    exposed by the API.

    **Examples:**

    .. code-block:: python

        import dagster as dg
        from dagster_census import CensusResource

        census_resource = CensusResource(
            api_key=dg.EnvVar("CENSUS_API_KEY")
        )

        @dg.asset
        def census_sync_asset(census: CensusResource):
            census.trigger_sync_and_poll(sync_id=123456)

        defs = dg.Definitions(
            assets=[census_sync_asset],
            resources={"census": census_resource}
        )
    """

    api_key: str = pydantic.Field(..., description="The Census API key")
    request_max_retries: int = pydantic.Field(
        default=3,
        description=(
            "The maximum number of times requests to the Census API should be retried "
            "before failing."
        ),
    )
    request_retry_delay: float = pydantic.Field(
        default=0.25,
        description="Time (in seconds) to wait between each request retry.",
    )
    request_timeout: int = pydantic.Field(
        default=15,
        description="Time (in seconds) after which the requests to Census are declared timed out.",
    )

    @property
    def api_base_url(self) -> str:
        return f"https://{CENSUS_API_BASE}/{CENSUS_VERSION}"

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @property
    @cached_method
    def _log(self) -> logging.Logger:
        return get_dagster_logger()

    def make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[str] = None,
        page_number: Optional[int] = None,
    ) -> Mapping[str, Any]:
        """Creates and sends a request to the desired Census API endpoint.

        Args:
            method (str): The http method to use for this request (e.g. "POST", "GET", "PATCH").
            endpoint (str): The Census API endpoint to send this request to.
            data (Optional[str]): JSON-formatted data string to be included in the request.

        Returns:
            Dict[str, Any]: JSON data from the response to this request
        """
        url = f"{self.api_base_url}/{endpoint}"
        headers = {
            "User-Agent": f"dagster-census/{__version__}",
            "Content-Type": "application/json;version=2",
        }

        if page_number is not None:
            params = {"page": page_number}
        else:
            params = {}

        num_retries = 0
        while True:
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    auth=HTTPBasicAuth("bearer", self.api_key),
                    data=data,
                    params=params,
                )
                response.raise_for_status()
                return response.json()
            except RequestException as e:
                self._log.error("Request to Census API failed: %s", e)
                if num_retries == self.request_max_retries:
                    break
                num_retries += 1
                time.sleep(self.request_retry_delay)

        raise Failure(f"Max retries ({self.request_max_retries}) exceeded with url: {url}.")

    def get_sync(self, sync_id: int) -> Mapping[str, Any]:
        """Gets details about a given sync from the Census API.

        Args:
            sync_id (int): The Census Sync ID.

        Returns:
            Dict[str, Any]: JSON data from the response to this request
        """
        return self.make_request(method="GET", endpoint=f"syncs/{sync_id}")

    def get_source(self, source_id: int) -> Mapping[str, Any]:
        """Gets details about a given source from the Census API.

        Args:
            source_id (int): The Census Source ID.

        Returns:
            Dict[str, Any]: JSON data from the response to this request
        """
        return self.make_request(method="GET", endpoint=f"sources/{source_id}")

    def get_destination(self, destination_id: int) -> Mapping[str, Any]:
        """Gets details about a given destination from the Census API.

        Args:
            destination_id (int): The Census Destination ID.

        Returns:
            Dict[str, Any]: JSON data from the response to this request
        """
        return self.make_request(method="GET", endpoint=f"destinations/{destination_id}")

    def get_sync_run(self, sync_run_id: int) -> Mapping[str, Any]:
        """Gets details about a specific sync run from the Census API.

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
    ) -> Mapping[str, Any]:
        """Given a Census sync run, poll until the run is complete.

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
                    f"Getting status of sync failed, please visit Census Logs at {log_url} to see"
                    " more."
                )

            sync_status = response_dict["data"]["status"]
            sync_id = response_dict["data"]["sync_id"]

            if sync_status not in SYNC_RUN_STATUSES:
                raise ValueError(
                    f"Unexpected response status '{sync_status}'; "
                    f"must be one of {','.join(sorted(SYNC_RUN_STATUSES))}. "
                    "See Management API docs for more information: "
                    "https://docs.getcensus.com/basics/developers/api/sync-runs"
                )

            if sync_status in {"queued", "working"}:
                self._log.debug(
                    f"Sync {sync_id} still running after {datetime.datetime.now() - poll_start}."
                )
                continue

            if poll_timeout and datetime.datetime.now() > poll_start + datetime.timedelta(
                seconds=poll_timeout
            ):
                raise Failure(
                    f"Sync for sync '{sync_id}' timed out after"
                    f" {datetime.datetime.now() - poll_start}."
                )

            break

        self._log.debug(
            f"Sync {sync_id} has finished running after {datetime.datetime.now() - poll_start}."
        )
        self._log.info(f"View sync details here: {log_url}.")

        return response_dict

    def trigger_sync(self, sync_id: int, force_full_sync: bool = False) -> Mapping[str, Any]:
        """Trigger an asynchronous run for a specific sync.

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
        """Trigger a run for a specific sync and poll until it has completed.

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

    @cached_method
    def fetch_census_workspace_data(self) -> CensusWorkspaceData:
        """Retrieves all Census syncs from the workspace and returns it as a CensusWorkspaceData object.

        Returns:
            CensusWorkspaceData: A snapshot of the Census workspace's syncs.
        """
        all_syncs = []
        page = self.make_request(method="GET", endpoint="syncs")

        last_page_number = page["pagination"]["last_page"]
        for sync in page["data"]:
            all_syncs.append(self._census_sync_struct_from_json(sync))

        for i in range(2, last_page_number + 1):
            page = self.make_request(method="GET", endpoint="syncs", page_number=i)
            for sync in page["data"]:
                all_syncs.append(self._census_sync_struct_from_json(sync))

        return CensusWorkspaceData(syncs=all_syncs)

    def _census_sync_struct_from_json(self, sync: dict[str, Any]) -> CensusSync:
        return CensusSync(
            id=sync["id"],
            name=sync["label"] or sync["resource_identifier"],
            source_id=sync["source_attributes"]["connection_id"],
            destination_id=sync["destination_attributes"]["connection_id"],
            mappings=sync["mappings"],
        )
