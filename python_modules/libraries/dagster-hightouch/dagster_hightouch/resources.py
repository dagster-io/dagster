import datetime
import logging
import time
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from dagster import ConfigurableResource, Failure, Field, StringSource, get_dagster_logger, resource

import dagster_hightouch
from dagster_hightouch import utils
from dagster_hightouch.types import HightouchOutput

HIGHTOUCH_API_BASE = "https://api.hightouch.io/api/v1/"
DEFAULT_POLL_INTERVAL = 3
TERMINAL_STATUSES = ["cancelled", "failed", "success", "warning", "interrupted"]
PENDING_STATUSES = [
    "queued",
    "querying",
    "processing",
    "reporting",
    "pending",
]
SUCCESS = "success"
WARNING = "warning"


class HightouchResource:
    """Client for the Hightouch REST API.

    This class provides methods to interface with Hightouch endpoints,
    primarily for triggering syncs and polling for their status.

    Note: For modern Dagster pipelines, use :class:`ConfigurableHightouchResource`.
    """

    def __init__(
        self,
        api_key: str,
        log: logging.Logger = get_dagster_logger(),
        request_max_retries: int = 3,
        request_retry_delay: float = 0.25,
    ):
        self._log = log
        self._api_key = api_key
        self._request_max_retries = request_max_retries
        self._request_retry_delay = request_retry_delay

    @property
    def api_base_url(self) -> str:
        return HIGHTOUCH_API_BASE

    def make_request(self, method: str, endpoint: str, params: dict[str, Any] | None = None):
        """Creates and sends a request to the desired Hightouch API endpoint.

        Args:
            method (str): The http method use for this request (e.g. "GET", "POST").
            endpoint (str): The Hightouch API endpoint to send this request to.
            params (Optional(dict): Query parameters to pass to the API endpoint

        Returns:
            Dict[str, Any]: Parsed json data from the response to this request
        """
        user_agent = f"HightouchDagsterOp/{dagster_hightouch.__version__}"
        headers = {"Authorization": f"Bearer {self._api_key}", "User-Agent": user_agent}

        num_retries = 0
        while True:
            try:
                response = requests.request(
                    method=method,
                    url=urljoin(self.api_base_url, endpoint),
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
                resp_dict = response.json()
                return resp_dict["data"] if "data" in resp_dict else resp_dict
            except requests.RequestException as e:
                self._log.error("Request to Hightouch API failed: %s", e)
                if num_retries == self._request_max_retries:
                    break
                num_retries += 1
                time.sleep(self._request_retry_delay)

        raise Failure("Exceeded max number of retries.")

    def get_sync_run_details(self, sync_id: str, sync_request_id: str) -> list[dict[str, Any]]:
        """Get details about a given sync run from the Hightouch API.

        Args:
            sync_id (str): The Hightouch Sync ID.
            sync_request_id (str): The Hightouch Sync Request ID.

        Returns:
            Dict[str, Any]: Parsed json data from the response
        """
        params = {"runId": sync_request_id}
        return self.make_request(method="GET", endpoint=f"syncs/{sync_id}/runs", params=params)

    def get_destination_details(self, destination_id: str) -> dict[str, Any]:
        """Get details about a destination from the Hightouch API.

        Args:
            destination_id (str): The Hightouch Destination ID

        Returns:
            Dict[str, Any]: Parsed json data from the response
        """
        return self.make_request(method="GET", endpoint=f"destinations/{destination_id}")

    def get_sync_details(self, sync_id: str) -> dict[str, Any]:
        """Get details about a given sync from the Hightouch API.

        Args:
            sync_id (str): The Hightouch Sync ID.

        Returns:
            Dict[str, Any]: Parsed json data from the response
        """
        return self.make_request(method="GET", endpoint=f"syncs/{sync_id}")

    def start_sync(self, sync_id: str) -> str:
        """Trigger a sync and initiate a sync run.

        Args:
            sync_id (str): The Hightouch Sync ID.

        Returns:
            str: The sync request ID created by the Hightouch API.
        """
        return self.make_request(method="POST", endpoint=f"syncs/{sync_id}/trigger")["id"]

    def poll_sync(
        self,
        sync_id: str,
        sync_request_id: str,
        fail_on_warning: bool = False,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        poll_timeout: float | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        """Poll for the completion of a sync.

        Args:
            sync_id (str): The Hightouch Sync ID
            sync_request_id (str): The Hightouch Sync Request ID to poll against.
            fail_on_warning (bool): Whether a warning is considered a failure for this sync.
            poll_interval (float): The time in seconds that will be waited between succcessive polls
            poll_timeout (float): The maximum time that will be waited before this operation
                times out.

        Returns:
            Dict[str, Any]: Parsed json output from the API
        """
        poll_start = datetime.datetime.now()
        while True:
            sync_run_details = self.get_sync_run_details(sync_id, sync_request_id)[0]

            self._log.debug(sync_run_details)
            run = utils.parse_sync_run_details(sync_run_details)
            self._log.info(
                f"Polling Hightouch Sync {sync_id}. Current status: {run.status}. "
                f"{100 * run.completion_ratio}% completed."
            )

            if run.status in TERMINAL_STATUSES:
                self._log.info(f"Sync request status: {run.status}. Polling complete")
                if run.error:
                    self._log.info("Sync Request Error: %s", run.error)

                if run.status == SUCCESS:
                    break
                if run.status == WARNING and not fail_on_warning:
                    break
                raise Failure(
                    f"Sync {sync_id} for request: {sync_request_id} failed with status: "
                    f"{run.status} and error:  {run.error}"
                )
            if run.status not in PENDING_STATUSES:
                self._log.warning(
                    "Unexpected status: %s returned for sync %s and request %s. Will try "
                    "again, but if you see this error, please let someone at Hightouch know.",
                    run.status,
                    sync_id,
                    sync_request_id,
                )
            if poll_timeout and datetime.datetime.now() > poll_start + datetime.timedelta(
                seconds=poll_timeout
            ):
                raise Failure(
                    f"Sync {sync_id} for request: {sync_request_id}' time out after "
                    f"{datetime.datetime.now() - poll_start}. Last status was {run.status}."
                )

            time.sleep(poll_interval)
        sync_details = self.get_sync_details(sync_id)
        destination_details = self.get_destination_details(sync_details["destinationId"])

        return (sync_details, sync_run_details, destination_details)

    def sync_and_poll(
        self,
        sync_id: str,
        fail_on_warning: bool = False,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        poll_timeout: float | None = None,
    ) -> HightouchOutput:
        """Initialize a sync run for the given sync id, and polls until it completes.

        Args:
            sync_id (str): The Hightouch Sync ID
            sync_request_id (str): The Hightouch Sync Request ID to poll against.
            fail_on_warning (bool): Whether a warning is considered a failure for this sync.
            poll_interval (float): The time in seconds that will be waited between succcessive polls
            poll_timeout (float): The maximum time that will be waited before this operation
                times out.

        Returns:
            :py:class:`~HightouchOutput`:
                Object containing details about the Hightouch sync run
        """
        sync_request_id = self.start_sync(sync_id)
        sync_details, sync_run_details, destination_details = self.poll_sync(
            sync_id,
            sync_request_id,
            fail_on_warning=fail_on_warning,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )

        return HightouchOutput(sync_details, sync_run_details, destination_details)


@resource(
    config_schema={
        "api_key": Field(
            StringSource,
            is_required=True,
            description="Hightouch API Key. You can find this on the Hightouch settings page",
        ),
        "request_max_retries": Field(
            int,
            default_value=3,
            description="The maximum times requests to Hightouch the API should be retried "
            "before failing.",
        ),
        "request_retry_delay": Field(
            float,
            default_value=0.25,
            description="Time (in seconds) to wait between each request retry.",
        ),
    },
    description="This resource helps manage Fivetran connectors",
)
def ht_resource(context) -> HightouchResource:
    """This resource allows users to programatically interface with the Hightouch REST API to triggers
    syncs and monitor their progress.
    """
    return HightouchResource(
        api_key=context.resource_config["api_key"],
        log=context.log,
        request_max_retries=context.resource_config["request_max_retries"],
        request_retry_delay=context.resource_config["request_retry_delay"],
    )


class ConfigurableHightouchResource(ConfigurableResource):
    """A resource for connecting to the Hightouch API using pythonic configuration.

    This resource is the recommended way to manage Hightouch connections in
    modern Dagster (1.0+).

    Attributes:
        api_key (str): Your Hightouch API key.
        request_max_retries (int): Maximum number of retries for API requests. Defaults to 3.
        request_retry_delay (float): Delay between retries in seconds. Defaults to 0.25.
    """

    api_key: str
    request_max_retries: int = 3
    request_retry_delay: float = 0.25
    fail_on_warning: bool = False
    poll_interval: float = DEFAULT_POLL_INTERVAL
    poll_timeout: Optional[float] = None

    def sync_and_poll(
        self,
        sync_id: str,
        fail_on_warning: Optional[bool] = None,
        poll_interval: Optional[float] = None,
        poll_timeout: Optional[float] = None,
    ) -> HightouchOutput:
        inner_resource = HightouchResource(
            api_key=self.api_key,
            request_max_retries=self.request_max_retries,
            request_retry_delay=self.request_retry_delay,
        )
        return inner_resource.sync_and_poll(
            sync_id=sync_id,
            fail_on_warning=fail_on_warning
            if fail_on_warning is not None
            else self.fail_on_warning,
            poll_interval=poll_interval if poll_interval is not None else self.poll_interval,
            poll_timeout=poll_timeout if poll_timeout is not None else self.poll_timeout,
        )
