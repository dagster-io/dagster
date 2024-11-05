from enum import Enum
from typing import Any, Mapping, Sequence

from dagster import _check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._record import record
from dagster._serdes.serdes import whitelist_for_serdes


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


class DagsterFivetranTranslator:
    """Translator class which converts raw response data from the Fivetran API into AssetSpecs.
    Subclass this class to implement custom logic for each type of Fivetran content.
    """

    def __init__(self, context: FivetranWorkspaceData):
        self._context = context

    @property
    def workspace_data(self) -> FivetranWorkspaceData:
        return self._context

    def get_asset_key(self, data: FivetranContentData) -> AssetKey:
        if data.content_type == FivetranContentType.CONNECTOR:
            return self.get_connector_asset_key(data)
        else:
            check.assert_never(data.content_type)

    def get_asset_spec(self, data: FivetranContentData) -> AssetSpec:
        if data.content_type == FivetranContentType.CONNECTOR:
            return self.get_connector_spec(data)
        else:
            check.assert_never(data.content_type)

    def get_connector_asset_key(self, data: FivetranContentData) -> AssetKey:
        raise NotImplementedError()

    def get_connector_spec(self, data: FivetranContentData) -> AssetSpec:
        raise NotImplementedError()
