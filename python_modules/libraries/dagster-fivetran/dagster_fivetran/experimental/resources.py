import logging
import os
import time
from typing import Any, Mapping, Optional

import requests
from dagster import Failure, __version__, get_dagster_logger
from dagster._annotations import experimental
from dagster._config.pythonic_config import ConfigurableResource
from dagster._utils.cached_method import cached_method
from pydantic import Field, PrivateAttr
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException

from dagster_fivetran.experimental.translator import FivetranWorkspaceData

FIVETRAN_API_BASE = "https://api.fivetran.com"
FIVETRAN_API_VERSION = "v1"
FIVETRAN_CONNECTOR_ENDPOINT = "connectors"


@experimental
class FivetranClient:
    """This class exposes methods on top of the Fivetran REST API."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        request_max_retries: int,
        request_retry_delay: float,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.request_max_retries = request_max_retries
        self.request_retry_delay = request_retry_delay

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


class FivetranWorkspace(ConfigurableResource):
    """This class represents a Fivetran workspace and provides utilities
    to interact with Fivetran APIs.
    """

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

    _client: FivetranClient = PrivateAttr(default=None)

    def get_client(self) -> FivetranClient:
        return FivetranClient(
            api_key=self.api_key,
            api_secret=self.api_secret,
            request_max_retries=self.request_max_retries,
            request_retry_delay=self.request_retry_delay,
        )

    def fetch_fivetran_workspace_data(
        self,
    ) -> FivetranWorkspaceData:
        """Retrieves all Fivetran content from the workspace and returns it as a FivetranWorkspaceData object.
        Future work will cache this data to avoid repeated calls to the Fivetran API.

        Returns:
            FivetranWorkspaceData: A snapshot of the Fivetran workspace's content.
        """
        raise NotImplementedError()
