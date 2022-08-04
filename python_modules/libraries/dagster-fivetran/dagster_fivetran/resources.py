import datetime
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from dagster_fivetran.types import FivetranOutput
from dagster_fivetran.utils import get_fivetran_connector_url, get_fivetran_logs_url
from dateutil import parser
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException

from dagster import Failure, Field, MetadataValue, StringSource, __version__
from dagster import _check as check
from dagster import get_dagster_logger, resource

FIVETRAN_API_BASE = "https://api.fivetran.com"
FIVETRAN_CONNECTOR_PATH = "v1/connectors/"

# default polling interval (in seconds)
DEFAULT_POLL_INTERVAL = 10


class FivetranResource:
    """
    This class exposes methods on top of the Fivetran REST API.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        disable_schedule_on_trigger: bool = True,
        request_max_retries: int = 3,
        request_retry_delay: float = 0.25,
        log: logging.Logger = get_dagster_logger(),
    ):
        self._auth = HTTPBasicAuth(api_key, api_secret)
        self._disable_schedule_on_trigger = disable_schedule_on_trigger

        self._request_max_retries = request_max_retries
        self._request_retry_delay = request_retry_delay

        self._log = log

    @property
    def api_base_url(self) -> str:
        return urljoin(FIVETRAN_API_BASE, FIVETRAN_CONNECTOR_PATH)

    def make_request(
        self, method: str, endpoint: str, data: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates and sends a request to the desired Fivetran Connector API endpoint.

        Args:
            method (str): The http method to use for this request (e.g. "POST", "GET", "PATCH").
            endpoint (str): The Fivetran API endpoint to send this request to.
            data (Optional[str]): JSON-formatted data string to be included in the request.

        Returns:
            Dict[str, Any]: Parsed json data from the response to this request
        """

        headers = {
            "User-Agent": f"dagster-fivetran/{__version__}",
            "Content-Type": "application/json;version=2",
        }

        num_retries = 0
        while True:
            try:
                response = requests.request(
                    method=method,
                    url=urljoin(self.api_base_url, endpoint),
                    headers=headers,
                    auth=self._auth,
                    data=data,
                )
                response.raise_for_status()
                resp_dict = response.json()
                return resp_dict["data"] if "data" in resp_dict else resp_dict
            except RequestException as e:
                self._log.error("Request to Fivetran API failed: %s", e)
                if num_retries == self._request_max_retries:
                    break
                num_retries += 1
                time.sleep(self._request_retry_delay)

        raise Failure("Exceeded max number of retries.")

    def get_connector_details(self, connector_id: str) -> Dict[str, Any]:
        """
        Gets details about a given connector from the Fivetran Connector API.

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.

        Returns:
            Dict[str, Any]: Parsed json data from the response to this request
        """
        return self.make_request(method="GET", endpoint=connector_id)

    def _assert_syncable_connector(self, connector_id: str):
        """
        Confirms that a given connector is eligible to sync. Will raise a Failure in the event that
        the connector is either paused or not fully setup.

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.
        """
        connector_details = self.get_connector_details(connector_id)
        if connector_details["paused"]:
            raise Failure(f"Connector '{connector_id}' cannot be synced as it is currently paused.")
        if connector_details["status"]["setup_state"] != "connected":
            raise Failure(f"Connector '{connector_id}' cannot be synced as it has not been setup")

    def get_connector_sync_status(self, connector_id: str) -> Tuple[datetime.datetime, bool, str]:
        """
        Gets details about the status of the most recent Fivetran sync operation for a given
        connector.

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.

        Returns:
            Tuple[datetime.datetime, bool, str]:
                Tuple representing the timestamp of the last completeded sync, if it succeeded, and
                the currently reported sync status.
        """
        connector_details = self.get_connector_details(connector_id)

        min_time_str = "0001-01-01 00:00:00+00"
        succeeded_at = parser.parse(connector_details["succeeded_at"] or min_time_str)
        failed_at = parser.parse(connector_details["failed_at"] or min_time_str)

        return (
            max(succeeded_at, failed_at),
            succeeded_at > failed_at,
            connector_details["status"]["sync_state"],
        )

    def update_connector(
        self, connector_id: str, properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Updates properties of a Fivetran Connector.

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.
            properties (Dict[str, Any]): The properties to be updated. For a comprehensive list of
                properties, see the [Fivetran docs](https://fivetran.com/docs/rest-api/connectors#modifyaconnector).

        Returns:
            Dict[str, Any]: Parsed json data representing the API response.
        """
        return self.make_request(method="PATCH", endpoint=connector_id, data=json.dumps(properties))

    def update_schedule_type(
        self, connector_id: str, schedule_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Updates the schedule type property of the connector to either "auto" or "manual".

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.
            schedule_type (Optional[str]): Either "auto" (to turn the schedule on) or "manual" (to
                turn it off).

        Returns:
            Dict[str, Any]: Parsed json data representing the API response.
        """
        if schedule_type not in ["auto", "manual"]:
            check.failed(f"schedule_type must be either 'auto' or 'manual': got '{schedule_type}'")
        return self.update_connector(connector_id, properties={"schedule_type": schedule_type})

    def get_connector_schema_config(self, connector_id: str) -> Dict[str, Any]:
        return self.make_request("GET", endpoint=f"{connector_id}/schemas")

    def start_sync(self, connector_id: str) -> Dict[str, Any]:
        """
        Initiates a sync of a Fivetran connector.

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.

        Returns:
            Dict[str, Any]: Parsed json data representing the connector details API response after
                the sync is started.
        """
        if self._disable_schedule_on_trigger:
            self._log.info("Disabling Fivetran sync schedule.")
            self.update_schedule_type(connector_id, "manual")
        self._assert_syncable_connector(connector_id)
        self.make_request(method="POST", endpoint=f"{connector_id}/force")
        connector_details = self.get_connector_details(connector_id)
        self._log.info(
            f"Sync initialized for connector_id={connector_id}. View this sync in the Fivetran UI: "
            + get_fivetran_connector_url(connector_details)
        )
        return connector_details

    def start_resync(
        self, connector_id: str, resync_parameters: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Initiates a historical sync of all data for multiple schema tables within a Fivetran connector.

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.
            resync_parameters (Dict[str, List[str]]): The resync parameters to send to the Fivetran API.
                An example payload can be found here: https://fivetran.com/docs/rest-api/connectors#request_6

        Returns:
            Dict[str, Any]: Parsed json data representing the connector details API response after
                the resync is started.
        """
        if self._disable_schedule_on_trigger:
            self._log.info("Disabling Fivetran sync schedule.")
            self.update_schedule_type(connector_id, "manual")
        self._assert_syncable_connector(connector_id)
        self.make_request(
            method="POST",
            endpoint=f"{connector_id}/schemas/tables/resync",
            data=json.dumps(resync_parameters),
        )
        connector_details = self.get_connector_details(connector_id)
        self._log.info(
            f"Sync initialized for connector_id={connector_id}. View this resync in the Fivetran UI: "
            + get_fivetran_connector_url(connector_details)
        )
        return connector_details

    def poll_sync(
        self,
        connector_id: str,
        initial_last_sync_completion: datetime.datetime,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        poll_timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Given a Fivetran connector and the timestamp at which the previous sync completed, poll
        until the next sync completes.

        The previous sync completion time is necessary because the only way to tell when a sync
        completes is when this value changes.

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.
            initial_last_sync_completion (datetime.datetime): The timestamp of the last completed sync
                (successful or otherwise) for this connector, prior to running this method.
            poll_interval (float): The time (in seconds) that will be waited between successive polls.
            poll_timeout (float): The maximum time that will waited before this operation is timed
                out. By default, this will never time out.

        Returns:
            Dict[str, Any]: Parsed json data representing the API response.
        """
        poll_start = datetime.datetime.now()
        while True:
            (
                curr_last_sync_completion,
                curr_last_sync_succeeded,
                curr_sync_state,
            ) = self.get_connector_sync_status(connector_id)
            self._log.info(f"Polled '{connector_id}'. Status: [{curr_sync_state}]")

            if curr_last_sync_completion > initial_last_sync_completion:
                break

            if poll_timeout and datetime.datetime.now() > poll_start + datetime.timedelta(
                seconds=poll_timeout
            ):
                raise Failure(
                    f"Sync for connector '{connector_id}' timed out after "
                    f"{datetime.datetime.now() - poll_start}."
                )

            # Sleep for the configured time interval before polling again.
            time.sleep(poll_interval)

        connector_details = self.get_connector_details(connector_id)
        if not curr_last_sync_succeeded:
            raise Failure(
                f"Sync for connector '{connector_id}' failed!",
                metadata={
                    "connector_details": MetadataValue.json(connector_details),
                    "log_url": MetadataValue.url(get_fivetran_logs_url(connector_details)),
                },
            )
        return connector_details

    def sync_and_poll(
        self,
        connector_id: str,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        poll_timeout: Optional[float] = None,
    ) -> FivetranOutput:
        """
        Initializes a sync operation for the given connector, and polls until it completes.

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.
            poll_interval (float): The time (in seconds) that will be waited between successive polls.
            poll_timeout (float): The maximum time that will waited before this operation is timed
                out. By default, this will never time out.

        Returns:
            :py:class:`~FivetranOutput`:
                Object containing details about the connector and the tables it updates
        """
        schema_config = self.get_connector_schema_config(connector_id)
        init_last_sync_timestamp, _, _ = self.get_connector_sync_status(connector_id)
        self.start_sync(connector_id)
        final_details = self.poll_sync(
            connector_id,
            init_last_sync_timestamp,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )
        return FivetranOutput(connector_details=final_details, schema_config=schema_config)

    def resync_and_poll(
        self,
        connector_id: str,
        resync_parameters: Dict[str, List[str]],
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        poll_timeout: Optional[float] = None,
    ) -> FivetranOutput:
        """
        Initializes a historical resync operation for the given connector, and polls until it completes.

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.
            resync_parameters (Dict[str, List[str]]): The payload to send to the Fivetran API.
                This should be a dictionary with schema names as the keys and a list of tables
                to resync as the values.
            poll_interval (float): The time (in seconds) that will be waited between successive polls.
            poll_timeout (float): The maximum time that will waited before this operation is timed
                out. By default, this will never time out.

        Returns:
            :py:class:`~FivetranOutput`:
                Object containing details about the connector and the tables it updates
        """
        schema_config = self.get_connector_schema_config(connector_id)
        init_last_sync_timestamp, _, _ = self.get_connector_sync_status(connector_id)
        self.start_resync(connector_id, resync_parameters)
        final_details = self.poll_sync(
            connector_id,
            init_last_sync_timestamp,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )
        return FivetranOutput(connector_details=final_details, schema_config=schema_config)


@resource(
    config_schema={
        "api_key": Field(
            StringSource,
            is_required=True,
            description="Fivetran API Key. You can find this value on the Fivetran settings page: "
            "https://fivetran.com/account/settings",
        ),
        "api_secret": Field(
            StringSource,
            is_required=True,
            description="Fivetran API Secret. You can find this value on the Fivetran settings page: "
            "https://fivetran.com/account/settings",
        ),
        "disable_schedule_on_trigger": Field(
            bool,
            default_value=True,
            description="Specifies if you would like any connector that is sync'd using this "
            "resource to be automatically taken off its Fivetran schedule.",
        ),
        "request_max_retries": Field(
            int,
            default_value=3,
            description="The maximum number of times requests to the Fivetran API should be retried "
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
def fivetran_resource(context) -> FivetranResource:
    """
    This resource allows users to programatically interface with the Fivetran REST API to launch
    syncs and monitor their progress. This currently implements only a subset of the functionality
    exposed by the API.

    For a complete set of documentation on the Fivetran REST API, including expected response JSON
    schemae, see the `Fivetran API Docs <https://fivetran.com/docs/rest-api/connectors>`_.

    To configure this resource, we recommend using the `configured
    <https://docs.dagster.io/concepts/configuration/configured>`_ method.

    **Examples:**

    .. code-block:: python

        from dagster import job
        from dagster_fivetran import fivetran_resource

        my_fivetran_resource = fivetran_resource.configured(
            {
                "api_key": {"env": "FIVETRAN_API_KEY"},
                "api_secret": {"env": "FIVETRAN_API_SECRET"},
            }
        )

        @job(resource_defs={"fivetran":my_fivetran_resource})
        def my_fivetran_job():
            ...

    """
    return FivetranResource(
        api_key=context.resource_config["api_key"],
        api_secret=context.resource_config["api_secret"],
        disable_schedule_on_trigger=context.resource_config["disable_schedule_on_trigger"],
        request_max_retries=context.resource_config["request_max_retries"],
        request_retry_delay=context.resource_config["request_retry_delay"],
        log=context.log,
    )
