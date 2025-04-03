import json
import logging
import os
import time
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from functools import partial
from typing import Any, Callable, Optional, Union
from urllib.parse import urljoin

import requests
from dagster import (
    AssetExecutionContext,
    AssetMaterialization,
    Definitions,
    Failure,
    InitResourceContext,
    MaterializeResult,
    MetadataValue,
    __version__,
    _check as check,
    get_dagster_logger,
    resource,
)
from dagster._annotations import beta, public, superseded
from dagster._config.pythonic_config import ConfigurableResource
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_load_context import StateBackedDefinitionsLoader
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from dagster._record import as_dict, record
from dagster._utils.cached_method import cached_method
from dagster._vendored.dateutil import parser
from pydantic import Field
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException

from dagster_fivetran.fivetran_event_iterator import FivetranEventIterator
from dagster_fivetran.translator import (
    ConnectorSelectorFn,
    DagsterFivetranTranslator,
    FivetranConnector,
    FivetranConnectorScheduleType,
    FivetranConnectorTableProps,
    FivetranDestination,
    FivetranMetadataSet,
    FivetranSchemaConfig,
    FivetranWorkspaceData,
)
from dagster_fivetran.types import FivetranOutput
from dagster_fivetran.utils import (
    DAGSTER_FIVETRAN_TRANSLATOR_METADATA_KEY,
    get_fivetran_connector_table_name,
    get_fivetran_connector_url,
    get_fivetran_logs_url,
    get_translator_from_fivetran_assets,
    metadata_for_table,
)

FIVETRAN_API_BASE = "https://api.fivetran.com"
FIVETRAN_API_VERSION = "v1"
FIVETRAN_CONNECTOR_ENDPOINT = "connectors"
FIVETRAN_API_VERSION_PATH = f"{FIVETRAN_API_VERSION}/"
FIVETRAN_CONNECTOR_PATH = f"{FIVETRAN_CONNECTOR_ENDPOINT}/"

# default polling interval (in seconds)
DEFAULT_POLL_INTERVAL = 10

FIVETRAN_RECONSTRUCTION_METADATA_KEY_PREFIX = "dagster-fivetran/reconstruction_metadata"


@superseded(additional_warn_text="Use `FivetranWorkspace` instead.")
class FivetranResource(ConfigurableResource):
    """This class exposes methods on top of the Fivetran REST API."""

    api_key: str = Field(description="The Fivetran API key to use for this resource.")
    api_secret: str = Field(description="The Fivetran API secret to use for this resource.")
    disable_schedule_on_trigger: bool = Field(
        default=True,
        description=(
            "Specifies if you would like any connector that is sync'd using this "
            "resource to be automatically taken off its Fivetran schedule."
        ),
    )
    request_max_retries: int = Field(
        default=3,
        description=(
            "The maximum number of times requests to the Fivetran API should be retried "
            "before failing."
        ),
    )
    request_retry_delay: float = Field(
        default=0.25,
        description="Time (in seconds) to wait between each request retry.",
    )

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @property
    def _auth(self) -> HTTPBasicAuth:
        return HTTPBasicAuth(self.api_key, self.api_secret)

    @property
    @cached_method
    def _log(self) -> logging.Logger:
        return get_dagster_logger()

    @property
    def api_base_url(self) -> str:
        return urljoin(FIVETRAN_API_BASE, FIVETRAN_API_VERSION_PATH)

    @property
    def api_connector_url(self) -> str:
        return urljoin(self.api_base_url, FIVETRAN_CONNECTOR_PATH)

    def make_connector_request(
        self, method: str, endpoint: str, data: Optional[str] = None
    ) -> Mapping[str, Any]:
        return self.make_request(method, urljoin(FIVETRAN_CONNECTOR_PATH, endpoint), data)

    def make_request(
        self, method: str, endpoint: str, data: Optional[str] = None
    ) -> Mapping[str, Any]:
        """Creates and sends a request to the desired Fivetran Connector API endpoint.

        Args:
            method (str): The http method to use for this request (e.g. "POST", "GET", "PATCH").
            endpoint (str): The Fivetran API endpoint to send this request to.
            data (Optional[str]): JSON-formatted data string to be included in the request.

        Returns:
            Dict[str, Any]: Parsed json data from the response to this request
        """
        url = urljoin(self.api_base_url, endpoint)
        headers = {
            "User-Agent": f"dagster-fivetran/{__version__}",
            "Content-Type": "application/json;version=2",
        }

        num_retries = 0
        while True:
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    auth=self._auth,
                    data=data,
                    timeout=int(os.getenv("DAGSTER_FIVETRAN_CONNECTOR_REQUEST_TIMEOUT", "60")),
                )
                response.raise_for_status()
                resp_dict = response.json()
                return resp_dict["data"] if "data" in resp_dict else resp_dict
            except RequestException as e:
                self._log.error("Request to Fivetran API failed: %s", e)
                if num_retries == self.request_max_retries:
                    break
                num_retries += 1
                time.sleep(self.request_retry_delay)

        raise Failure(f"Max retries ({self.request_max_retries}) exceeded with url: {url}.")

    def get_connector_details(self, connector_id: str) -> Mapping[str, Any]:
        """Gets details about a given connector from the Fivetran Connector API.

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.

        Returns:
            Dict[str, Any]: Parsed json data from the response to this request
        """
        return self.make_connector_request(method="GET", endpoint=connector_id)

    def _assert_syncable_connector(self, connector_id: str):
        """Confirms that a given connector is eligible to sync. Will raise a Failure in the event that
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

    def get_connector_sync_status(self, connector_id: str) -> tuple[datetime, bool, str]:
        """Gets details about the status of the most recent Fivetran sync operation for a given
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
            max(succeeded_at, failed_at),  # pyright: ignore[reportReturnType]
            succeeded_at > failed_at,  # pyright: ignore[reportOperatorIssue]
            connector_details["status"]["sync_state"],
        )

    def update_connector(
        self, connector_id: str, properties: Optional[Mapping[str, Any]] = None
    ) -> Mapping[str, Any]:
        """Updates properties of a Fivetran Connector.

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.
            properties (Dict[str, Any]): The properties to be updated. For a comprehensive list of
                properties, see the [Fivetran docs](https://fivetran.com/docs/rest-api/connectors#modifyaconnector).

        Returns:
            Dict[str, Any]: Parsed json data representing the API response.
        """
        return self.make_connector_request(
            method="PATCH", endpoint=connector_id, data=json.dumps(properties)
        )

    def update_schedule_type(
        self, connector_id: str, schedule_type: Optional[str] = None
    ) -> Mapping[str, Any]:
        """Updates the schedule type property of the connector to either "auto" or "manual".

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

    def get_connector_schema_config(self, connector_id: str) -> Mapping[str, Any]:
        return self.make_connector_request("GET", endpoint=f"{connector_id}/schemas")

    def start_sync(self, connector_id: str) -> Mapping[str, Any]:
        """Initiates a sync of a Fivetran connector.

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.

        Returns:
            Dict[str, Any]: Parsed json data representing the connector details API response after
                the sync is started.
        """
        if self.disable_schedule_on_trigger:
            self._log.info("Disabling Fivetran sync schedule.")
            self.update_schedule_type(connector_id, "manual")
        self._assert_syncable_connector(connector_id)
        self.make_connector_request(method="POST", endpoint=f"{connector_id}/force")
        connector_details = self.get_connector_details(connector_id)
        self._log.info(
            f"Sync initialized for connector_id={connector_id}. View this sync in the Fivetran UI: "
            + get_fivetran_connector_url(connector_details)
        )
        return connector_details

    def start_resync(
        self, connector_id: str, resync_parameters: Optional[Mapping[str, Sequence[str]]] = None
    ) -> Mapping[str, Any]:
        """Initiates a historical sync of all data for multiple schema tables within a Fivetran connector.

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.
            resync_parameters (Optional[Dict[str, List[str]]]): Optional resync parameters to send to the Fivetran API.
                An example payload can be found here: https://fivetran.com/docs/rest-api/connectors#request_7

        Returns:
            Dict[str, Any]: Parsed json data representing the connector details API response after
                the resync is started.
        """
        if self.disable_schedule_on_trigger:
            self._log.info("Disabling Fivetran sync schedule.")
            self.update_schedule_type(connector_id, "manual")
        self._assert_syncable_connector(connector_id)
        self.make_connector_request(
            method="POST",
            endpoint=(
                f"{connector_id}/schemas/tables/resync"
                if resync_parameters is not None
                else f"{connector_id}/resync"
            ),
            data=json.dumps(resync_parameters) if resync_parameters is not None else None,
        )
        connector_details = self.get_connector_details(connector_id)
        self._log.info(
            f"Sync initialized for connector_id={connector_id}. View this resync in the Fivetran"
            " UI: " + get_fivetran_connector_url(connector_details)
        )
        return connector_details

    def poll_sync(
        self,
        connector_id: str,
        initial_last_sync_completion: datetime,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        poll_timeout: Optional[float] = None,
    ) -> Mapping[str, Any]:
        """Given a Fivetran connector and the timestamp at which the previous sync completed, poll
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
        poll_start = datetime.now()
        while True:
            (
                curr_last_sync_completion,
                curr_last_sync_succeeded,
                curr_sync_state,
            ) = self.get_connector_sync_status(connector_id)
            self._log.info(f"Polled '{connector_id}'. Status: [{curr_sync_state}]")

            if curr_last_sync_completion > initial_last_sync_completion:
                break

            if poll_timeout and datetime.now() > poll_start + timedelta(seconds=poll_timeout):
                raise Failure(
                    f"Sync for connector '{connector_id}' timed out after "
                    f"{datetime.now() - poll_start}."
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
        """Initializes a sync operation for the given connector, and polls until it completes.

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
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        poll_timeout: Optional[float] = None,
        resync_parameters: Optional[Mapping[str, Sequence[str]]] = None,
    ) -> FivetranOutput:
        """Initializes a historical resync operation for the given connector, and polls until it completes.

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

    def get_destination_details(self, destination_id: str) -> Mapping[str, Any]:
        """Fetches details about a given destination from the Fivetran API."""
        return self.make_request("GET", f"destinations/{destination_id}")


@superseded(additional_warn_text="Use `FivetranWorkspace` instead.")
@dagster_maintained_resource
@resource(config_schema=FivetranResource.to_config_schema())
def fivetran_resource(context: InitResourceContext) -> FivetranResource:
    """This resource allows users to programatically interface with the Fivetran REST API to launch
    syncs and monitor their progress. This currently implements only a subset of the functionality
    exposed by the API.

    For a complete set of documentation on the Fivetran REST API, including expected response JSON
    schemae, see the `Fivetran API Docs <https://fivetran.com/docs/rest-api/connectors>`_.

    To configure this resource, we recommend using the `configured
    <https://legacy-docs.dagster.io/concepts/configuration/configured>`_ method.

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
    return FivetranResource.from_resource_context(context)


# ------------------
# Reworked resources
# ------------------


@beta
class FivetranClient:
    """This class exposes methods on top of the Fivetran REST API."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        request_max_retries: int,
        request_retry_delay: float,
        disable_schedule_on_trigger: bool,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.request_max_retries = request_max_retries
        self.request_retry_delay = request_retry_delay
        self.disable_schedule_on_trigger = disable_schedule_on_trigger

    @property
    def _auth(self) -> HTTPBasicAuth:
        return HTTPBasicAuth(self.api_key, self.api_secret)

    @property
    @cached_method
    def _log(self) -> logging.Logger:
        return get_dagster_logger()

    @property
    def api_base_url(self) -> str:
        return f"{FIVETRAN_API_BASE}/{FIVETRAN_API_VERSION}"

    @property
    def api_connector_url(self) -> str:
        return f"{self.api_base_url}/{FIVETRAN_CONNECTOR_ENDPOINT}"

    def _make_connector_request(
        self, method: str, endpoint: str, data: Optional[str] = None
    ) -> Mapping[str, Any]:
        return self._make_request(method, f"{FIVETRAN_CONNECTOR_ENDPOINT}/{endpoint}", data)

    def _make_request(
        self, method: str, endpoint: str, data: Optional[str] = None
    ) -> Mapping[str, Any]:
        """Creates and sends a request to the desired Fivetran API endpoint.

        Args:
            method (str): The http method to use for this request (e.g. "POST", "GET", "PATCH").
            endpoint (str): The Fivetran API endpoint to send this request to.
            data (Optional[str]): JSON-formatted data string to be included in the request.

        Returns:
            Dict[str, Any]: Parsed json data from the response to this request.
        """
        url = f"{self.api_base_url}/{endpoint}"
        headers = {
            "User-Agent": f"dagster-fivetran/{__version__}",
            "Content-Type": "application/json;version=2",
        }

        num_retries = 0
        while True:
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    auth=self._auth,
                    data=data,
                    timeout=int(os.getenv("DAGSTER_FIVETRAN_API_REQUEST_TIMEOUT", "60")),
                )
                response.raise_for_status()
                resp_dict = response.json()
                return resp_dict["data"] if "data" in resp_dict else resp_dict
            except RequestException as e:
                self._log.error("Request to Fivetran API failed: %s", e)
                if num_retries == self.request_max_retries:
                    break
                num_retries += 1
                time.sleep(self.request_retry_delay)

        raise Failure(f"Max retries ({self.request_max_retries}) exceeded with url: {url}.")

    def get_connector_details(self, connector_id: str) -> Mapping[str, Any]:
        """Gets details about a given connector from the Fivetran API.

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.

        Returns:
            Dict[str, Any]: Parsed json data from the response to this request.
        """
        return self._make_connector_request(method="GET", endpoint=connector_id)

    def get_connectors_for_group(self, group_id: str) -> Mapping[str, Any]:
        """Fetches all connectors for a given group from the Fivetran API.

        Args:
            group_id (str): The Fivetran Group ID.

        Returns:
            Dict[str, Any]: Parsed json data from the response to this request.
        """
        return self._make_request("GET", f"groups/{group_id}/connectors")

    def get_schema_config_for_connector(self, connector_id: str) -> Mapping[str, Any]:
        """Fetches the connector schema config for a given connector from the Fivetran API.

        Args:
            connector_id (str): The Fivetran Connector ID.

        Returns:
            Dict[str, Any]: Parsed json data from the response to this request.
        """
        return self._make_request("GET", f"connectors/{connector_id}/schemas")

    def get_destination_details(self, destination_id: str) -> Mapping[str, Any]:
        """Fetches details about a given destination from the Fivetran API.

        Args:
            destination_id (str): The Fivetran Destination ID.

        Returns:
            Dict[str, Any]: Parsed json data from the response to this request.
        """
        return self._make_request("GET", f"destinations/{destination_id}")

    def get_groups(self) -> Mapping[str, Any]:
        """Fetches all groups from the Fivetran API.

        Returns:
            Dict[str, Any]: Parsed json data from the response to this request.
        """
        return self._make_request("GET", "groups")

    def update_schedule_type_for_connector(
        self, connector_id: str, schedule_type: str
    ) -> Mapping[str, Any]:
        """Updates the schedule type property of the connector to either "auto" or "manual".

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.
            schedule_type (str): Either "auto" (to turn the schedule on) or "manual" (to
                turn it off).

        Returns:
            Dict[str, Any]: Parsed json data representing the API response.
        """
        schedule_types = {s for s in FivetranConnectorScheduleType}
        if schedule_type not in schedule_types:
            check.failed(
                f"The schedule_type for connector {connector_id} must be in {schedule_types}: "
                f"got '{schedule_type}'"
            )
        return self._make_connector_request(
            method="PATCH", endpoint=connector_id, data=json.dumps({"schedule_type": schedule_type})
        )

    def get_columns_config_for_table(
        self, connector_id: str, schema_name: str, table_name: str
    ) -> Mapping[str, Any]:
        """Fetches the source table columns config for a given table from the Fivetran API.

        Args:
            connector_id (str): The Fivetran Connector ID.
            schema_name (str): The Fivetran Schema name.
            table_name (str): The Fivetran Table name.

        Returns:
            Dict[str, Any]: Parsed json data from the response to this request.
        """
        return self._make_connector_request(
            method="GET",
            endpoint=f"{connector_id}/schemas/{schema_name}/tables/{table_name}/columns",
        )

    def start_sync(self, connector_id: str) -> None:
        """Initiates a sync of a Fivetran connector.

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.

        """
        request_fn = partial(
            self._make_connector_request, method="POST", endpoint=f"{connector_id}/force"
        )
        self._start_sync(request_fn=request_fn, connector_id=connector_id)

    def start_resync(
        self, connector_id: str, resync_parameters: Optional[Mapping[str, Sequence[str]]] = None
    ) -> None:
        """Initiates a historical sync of all data for multiple schema tables within a Fivetran connector.

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.
            resync_parameters (Optional[Dict[str, List[str]]]): Optional resync parameters to send to the Fivetran API.
                An example payload can be found here: https://fivetran.com/docs/rest-api/connectors#request_7
        """
        request_fn = partial(
            self._make_connector_request,
            method="POST",
            endpoint=(
                f"{connector_id}/schemas/tables/resync"
                if resync_parameters is not None
                else f"{connector_id}/resync"
            ),
            data=json.dumps(resync_parameters) if resync_parameters is not None else None,
        )
        self._start_sync(request_fn=request_fn, connector_id=connector_id)

    def _start_sync(self, request_fn: Callable[[], Mapping[str, Any]], connector_id: str) -> None:
        connector = FivetranConnector.from_connector_details(
            connector_details=self.get_connector_details(connector_id)
        )
        connector.validate_syncable()
        if self.disable_schedule_on_trigger:
            self._log.info(f"Disabling Fivetran sync schedule for connector {connector_id}.")
            self.update_schedule_type_for_connector(connector_id, "manual")
        request_fn()
        self._log.info(
            f"Sync initialized for connector {connector_id}. View this sync in the Fivetran"
            " UI: " + connector.url
        )

    def poll_sync(
        self,
        connector_id: str,
        previous_sync_completed_at: datetime,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        poll_timeout: Optional[float] = None,
    ) -> Mapping[str, Any]:
        """Given a Fivetran connector and the timestamp at which the previous sync completed, poll
        until the next sync completes.

        The previous sync completion time is necessary because the only way to tell when a sync
        completes is when this value changes.

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.
            previous_sync_completed_at (datetime.datetime): The datetime of the previous completed sync
                (successful or otherwise) for this connector, prior to running this method.
            poll_interval (float): The time (in seconds) that will be waited between successive polls.
            poll_timeout (float): The maximum time that will wait before this operation is timed
                out. By default, this will never time out.

        Returns:
            Dict[str, Any]: Parsed json data representing the API response.
        """
        poll_start = datetime.now()
        while True:
            connector_details = self.get_connector_details(connector_id)
            connector = FivetranConnector.from_connector_details(
                connector_details=connector_details
            )
            self._log.info(f"Polled '{connector_id}'. Status: [{connector.sync_state}]")

            if connector.last_sync_completed_at > previous_sync_completed_at:
                break

            if poll_timeout and datetime.now() > poll_start + timedelta(seconds=poll_timeout):
                raise Failure(
                    f"Sync for connector '{connector_id}' timed out after "
                    f"{datetime.now() - poll_start}."
                )

            # Sleep for the configured time interval before polling again.
            time.sleep(poll_interval)

        if not connector.is_last_sync_successful:
            raise Failure(
                f"Sync for connector '{connector_id}' failed!",
                metadata={
                    "connector_details": MetadataValue.json(connector_details),
                    "log_url": MetadataValue.url(connector.url),
                },
            )
        return connector_details

    def sync_and_poll(
        self,
        connector_id: str,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        poll_timeout: Optional[float] = None,
    ) -> FivetranOutput:
        """Initializes a sync operation for the given connector, and polls until it completes.

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.
            poll_interval (float): The time (in seconds) that will be waited between successive polls.
            poll_timeout (float): The maximum time that will wait before this operation is timed
                out. By default, this will never time out.

        Returns:
            :py:class:`~FivetranOutput`:
                Object containing details about the connector and the tables it updates
        """
        return self._sync_and_poll(
            sync_fn=self.start_sync,
            connector_id=connector_id,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )

    def resync_and_poll(
        self,
        connector_id: str,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        poll_timeout: Optional[float] = None,
        resync_parameters: Optional[Mapping[str, Sequence[str]]] = None,
    ) -> FivetranOutput:
        """Initializes a historical resync operation for the given connector, and polls until it completes.

        Args:
            connector_id (str): The Fivetran Connector ID. You can retrieve this value from the
                "Setup" tab of a given connector in the Fivetran UI.
            resync_parameters (Dict[str, List[str]]): The payload to send to the Fivetran API.
                This should be a dictionary with schema names as the keys and a list of tables
                to resync as the values.
            poll_interval (float): The time (in seconds) that will be waited between successive polls.
            poll_timeout (float): The maximum time that will wait before this operation is timed
                out. By default, this will never time out.

        Returns:
            :py:class:`~FivetranOutput`:
                Object containing details about the connector and the tables it updates
        """
        return self._sync_and_poll(
            sync_fn=partial(self.start_resync, resync_parameters=resync_parameters),
            connector_id=connector_id,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )

    def _sync_and_poll(
        self,
        sync_fn: Callable,
        connector_id: str,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        poll_timeout: Optional[float] = None,
    ) -> FivetranOutput:
        schema_config_details = self.get_schema_config_for_connector(connector_id)
        connector = FivetranConnector.from_connector_details(
            connector_details=self.get_connector_details(connector_id)
        )
        sync_fn(connector_id=connector_id)
        final_details = self.poll_sync(
            connector_id=connector_id,
            previous_sync_completed_at=connector.last_sync_completed_at,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )
        return FivetranOutput(connector_details=final_details, schema_config=schema_config_details)


@beta
class FivetranWorkspace(ConfigurableResource):
    """This class represents a Fivetran workspace and provides utilities
    to interact with Fivetran APIs.
    """

    account_id: str = Field(description="The Fivetran account ID.")
    api_key: str = Field(description="The Fivetran API key to use for this resource.")
    api_secret: str = Field(description="The Fivetran API secret to use for this resource.")
    request_max_retries: int = Field(
        default=3,
        description=(
            "The maximum number of times requests to the Fivetran API should be retried "
            "before failing."
        ),
    )
    request_retry_delay: float = Field(
        default=0.25,
        description="Time (in seconds) to wait between each request retry.",
    )
    disable_schedule_on_trigger: bool = Field(
        default=True,
        description=(
            "Whether to disable the schedule of a connector when it is synchronized using this resource."
            "Defaults to True."
        ),
    )

    @property
    @cached_method
    def _log(self) -> logging.Logger:
        return get_dagster_logger()

    @cached_method
    def get_client(self) -> FivetranClient:
        return FivetranClient(
            api_key=self.api_key,
            api_secret=self.api_secret,
            request_max_retries=self.request_max_retries,
            request_retry_delay=self.request_retry_delay,
            disable_schedule_on_trigger=self.disable_schedule_on_trigger,
        )

    def fetch_fivetran_workspace_data(
        self,
    ) -> FivetranWorkspaceData:
        """Retrieves all Fivetran content from the workspace and returns it as a FivetranWorkspaceData object.

        Returns:
            FivetranWorkspaceData: A snapshot of the Fivetran workspace's content.
        """
        connectors_by_id = {}
        destinations_by_id = {}
        schema_configs_by_connector_id = {}

        client = self.get_client()
        groups = client.get_groups()["items"]

        for group in groups:
            group_id = group["id"]

            destination_details = client.get_destination_details(destination_id=group_id)
            destination = FivetranDestination.from_destination_details(
                destination_details=destination_details
            )

            destinations_by_id[destination.id] = destination

            connectors_details = client.get_connectors_for_group(group_id=group_id)["items"]
            for connector_details in connectors_details:
                connector = FivetranConnector.from_connector_details(
                    connector_details=connector_details,
                )
                if not connector.is_connected:
                    self._log.warning(
                        f"Ignoring incomplete or broken connector `{connector.name}`. "
                        f"Dagster requires a connector to be connected before fetching its data."
                    )
                    continue

                schema_config_details = client.get_schema_config_for_connector(
                    connector_id=connector.id
                )
                schema_config = FivetranSchemaConfig.from_schema_config_details(
                    schema_config_details=schema_config_details
                )

                # A connector that has not been synced yet has no `schemas` field in its schema config.
                # Schemas are required for creating the asset definitions,
                # so connectors for which the schemas are missing are discarded.
                if not schema_config.has_schemas:
                    self._log.warning(
                        f"Ignoring connector `{connector.name}`. "
                        f"Dagster requires connector schema information to represent this connector, "
                        f"which is not available until this connector has been run for the first time."
                    )
                    continue

                connectors_by_id[connector.id] = connector
                schema_configs_by_connector_id[connector.id] = schema_config

        return FivetranWorkspaceData(
            connectors_by_id=connectors_by_id,
            destinations_by_id=destinations_by_id,
            schema_configs_by_connector_id=schema_configs_by_connector_id,
        )

    @cached_method
    def load_asset_specs(
        self,
        dagster_fivetran_translator: Optional[DagsterFivetranTranslator] = None,
        connector_selector_fn: Optional[ConnectorSelectorFn] = None,
    ) -> Sequence[AssetSpec]:
        """Returns a list of AssetSpecs representing the Fivetran content in the workspace.

        Args:
            dagster_fivetran_translator (Optional[DagsterFivetranTranslator], optional): The translator to use
                to convert Fivetran content into :py:class:`dagster.AssetSpec`.
                Defaults to :py:class:`DagsterFivetranTranslator`.
            connector_selector_fn (Optional[ConnectorSelectorFn]):
                A function that allows for filtering which Fivetran connector assets are created for.

        Returns:
            List[AssetSpec]: The set of assets representing the Fivetran content in the workspace.

        Examples:
            Loading the asset specs for a given Fivetran workspace:

            .. code-block:: python
                from dagster_fivetran import FivetranWorkspace, load_fivetran_asset_specs

                import dagster as dg

                fivetran_workspace = FivetranWorkspace(
                    account_id=dg.EnvVar("FIVETRAN_ACCOUNT_ID"),
                    api_key=dg.EnvVar("FIVETRAN_API_KEY"),
                    api_secret=dg.EnvVar("FIVETRAN_API_SECRET"),
                )

                fivetran_specs = fivetran_workspace.load_asset_specs()
                defs = dg.Definitions(assets=[*fivetran_specs], resources={"fivetran": fivetran_workspace}
        """
        return load_fivetran_asset_specs(
            workspace=self,
            dagster_fivetran_translator=dagster_fivetran_translator or DagsterFivetranTranslator(),
            connector_selector_fn=connector_selector_fn,
        )

    def _generate_materialization(
        self,
        fivetran_output: FivetranOutput,
        dagster_fivetran_translator: DagsterFivetranTranslator,
    ):
        connector = FivetranConnector.from_connector_details(
            connector_details=fivetran_output.connector_details
        )
        schema_config = FivetranSchemaConfig.from_schema_config_details(
            schema_config_details=fivetran_output.schema_config
        )

        for schema in schema_config.schemas.values():
            if not schema.enabled:
                continue

            for table in schema.tables.values():
                if not table.enabled:
                    continue

                asset_key = dagster_fivetran_translator.get_asset_spec(
                    props=FivetranConnectorTableProps(
                        table=get_fivetran_connector_table_name(
                            schema_name=schema.name_in_destination,
                            table_name=table.name_in_destination,
                        ),
                        connector_id=connector.id,
                        name=connector.name,
                        connector_url=connector.url,
                        schema_config=schema_config,
                        database=None,
                        service=None,
                    )
                ).key

                yield AssetMaterialization(
                    asset_key=asset_key,
                    description=(
                        f"Table generated via Fivetran sync: {schema.name_in_destination}.{table.name_in_destination}"
                    ),
                    metadata={
                        **metadata_for_table(
                            as_dict(table),
                            get_fivetran_connector_url(fivetran_output.connector_details),
                            include_column_info=True,
                            database=None,
                            schema=schema.name_in_destination,
                            table=table.name_in_destination,
                        ),
                        **FivetranMetadataSet(
                            connector_id=connector.id,
                            destination_schema_name=schema.name_in_destination,
                            destination_table_name=table.name_in_destination,
                        ),
                    },
                )

    @public
    @beta
    def sync_and_poll(
        self, context: AssetExecutionContext
    ) -> FivetranEventIterator[Union[AssetMaterialization, MaterializeResult]]:
        """Executes a sync and poll process to materialize Fivetran assets.
            This method can only be used in the context of an asset execution.

        Args:
            context (AssetExecutionContext): The execution context
                from within `@fivetran_assets`.

        Returns:
            Iterator[Union[AssetMaterialization, MaterializeResult]]: An iterator of MaterializeResult
                or AssetMaterialization.
        """
        return FivetranEventIterator(
            events=self._sync_and_poll(context=context), fivetran_workspace=self, context=context
        )

    def _sync_and_poll(self, context: AssetExecutionContext):
        assets_def = context.assets_def
        dagster_fivetran_translator = get_translator_from_fivetran_assets(assets_def)
        connector_id = next(
            check.not_none(FivetranMetadataSet.extract(spec.metadata).connector_id)
            for spec in assets_def.specs
        )

        client = self.get_client()
        fivetran_output = client.sync_and_poll(
            connector_id=connector_id,
        )

        materialized_asset_keys = set()
        for materialization in self._generate_materialization(
            fivetran_output=fivetran_output, dagster_fivetran_translator=dagster_fivetran_translator
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
def load_fivetran_asset_specs(
    workspace: FivetranWorkspace,
    dagster_fivetran_translator: Optional[DagsterFivetranTranslator] = None,
    connector_selector_fn: Optional[ConnectorSelectorFn] = None,
) -> Sequence[AssetSpec]:
    """Returns a list of AssetSpecs representing the Fivetran content in the workspace.

    Args:
        workspace (FivetranWorkspace): The Fivetran workspace to fetch assets from.
        dagster_fivetran_translator (Optional[DagsterFivetranTranslator], optional): The translator to use
            to convert Fivetran content into :py:class:`dagster.AssetSpec`.
            Defaults to :py:class:`DagsterFivetranTranslator`.
        connector_selector_fn (Optional[ConnectorSelectorFn]):
                A function that allows for filtering which Fivetran connector assets are created for.

    Returns:
        List[AssetSpec]: The set of assets representing the Fivetran content in the workspace.

    Examples:
        Loading the asset specs for a given Fivetran workspace:

        .. code-block:: python

            from dagster_fivetran import FivetranWorkspace, load_fivetran_asset_specs

            import dagster as dg

            fivetran_workspace = FivetranWorkspace(
                account_id=dg.EnvVar("FIVETRAN_ACCOUNT_ID"),
                api_key=dg.EnvVar("FIVETRAN_API_KEY"),
                api_secret=dg.EnvVar("FIVETRAN_API_SECRET"),
            )

            fivetran_specs = load_fivetran_asset_specs(fivetran_workspace)
            defs = dg.Definitions(assets=[*fivetran_specs], resources={"fivetran": fivetran_workspace}
    """
    dagster_fivetran_translator = dagster_fivetran_translator or DagsterFivetranTranslator()

    with workspace.process_config_and_initialize_cm() as initialized_workspace:
        return [
            spec.merge_attributes(
                metadata={DAGSTER_FIVETRAN_TRANSLATOR_METADATA_KEY: dagster_fivetran_translator}
            )
            for spec in check.is_list(
                FivetranWorkspaceDefsLoader(
                    workspace=initialized_workspace,
                    translator=dagster_fivetran_translator,
                    connector_selector_fn=connector_selector_fn,
                )
                .build_defs()
                .assets,
                AssetSpec,
            )
        ]


@record
class FivetranWorkspaceDefsLoader(StateBackedDefinitionsLoader[Mapping[str, Any]]):
    workspace: FivetranWorkspace
    translator: DagsterFivetranTranslator
    connector_selector_fn: Optional[ConnectorSelectorFn] = None

    @property
    def defs_key(self) -> str:
        return f"{FIVETRAN_RECONSTRUCTION_METADATA_KEY_PREFIX}/{self.workspace.account_id}"

    def fetch_state(self) -> FivetranWorkspaceData:  # pyright: ignore[reportIncompatibleMethodOverride]
        return self.workspace.fetch_fivetran_workspace_data()

    def defs_from_state(self, state: FivetranWorkspaceData) -> Definitions:  # pyright: ignore[reportIncompatibleMethodOverride]
        all_asset_specs = [
            self.translator.get_asset_spec(props)
            for props in state.to_workspace_data_selection(
                connector_selector_fn=self.connector_selector_fn
            ).to_fivetran_connector_table_props_data()
        ]

        return Definitions(assets=all_asset_specs)
