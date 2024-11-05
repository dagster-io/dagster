import logging
from enum import Enum
from typing import Any, Mapping, Optional, Sequence

from dagster import get_dagster_logger
from dagster._annotations import experimental
from dagster._config.pythonic_config import ConfigurableResource
from dagster._record import record
from dagster._serdes.serdes import whitelist_for_serdes
from dagster._utils.cached_method import cached_method
from pydantic import Field, PrivateAttr
from requests.auth import HTTPBasicAuth


class FivetranContentType(Enum):
    """Enum representing each object in Fivetran's ontology."""

    CONNECTOR = "connector"
    DESTINATION = "destination"


@whitelist_for_serdes
@record
class FivetranContentData:
    """A record representing a piece of content in a Fivetran workspace.
    Includes the object's type and data as returned from the API.
    """

    content_type: FivetranContentType
    properties: Mapping[str, Any]


@record
class FivetranWorkspaceData:
    """A record representing all content in a Fivetran workspace.
    Provided as context for the translator so that it can resolve dependencies between content.
    """

    connectors_by_id: Mapping[str, FivetranContentData]
    destinations_by_id: Mapping[str, FivetranContentData]

    @classmethod
    def from_content_data(
        cls, content_data: Sequence[FivetranContentData]
    ) -> "FivetranWorkspaceData":
        raise NotImplementedError()


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
        raise NotImplementedError()

    @property
    @cached_method
    def _log(self) -> logging.Logger:
        return get_dagster_logger()

    @property
    def api_base_url(self) -> str:
        raise NotImplementedError()

    @property
    def api_connector_url(self) -> str:
        raise NotImplementedError()

    def make_connector_request(
        self, method: str, endpoint: str, data: Optional[str] = None
    ) -> Mapping[str, Any]:
        raise NotImplementedError()

    def make_request(
        self, method: str, endpoint: str, data: Optional[str] = None
    ) -> Mapping[str, Any]:
        raise NotImplementedError()

    def get_connector_details(self, connector_id: str) -> Mapping[str, Any]:
        """Fetches details about a given connector from the Fivetran API."""
        raise NotImplementedError()

    def get_connectors_for_group(self, group_id: str) -> Mapping[str, Any]:
        """Fetches all connectors for a given group from the Fivetran API."""
        raise NotImplementedError()

    def get_destination_details(self, destination_id: str) -> Mapping[str, Any]:
        """Fetches details about a given destination from the Fivetran API."""
        raise NotImplementedError()

    def get_groups(self) -> Mapping[str, Any]:
        """Fetches all groups from the Fivetran API."""
        raise NotImplementedError()


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
