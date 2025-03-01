# SLA definition stuff
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Union

from dagster._core.definitions.events import AssetKey
from dagster._record import record
from dagster._serdes import whitelist_for_serdes

if TYPE_CHECKING:
    from dagster._core.events import DagsterEventType


@whitelist_for_serdes
@record
class SlaViolating:
    sla_name: str
    asset_key: AssetKey
    # The timestamp at which the asset began violating its SLA.
    violating_since: float
    last_event_timestamp: float
    last_event_storage_id: int
    reason_md: str
    metadata: Mapping[str, Any]

    @classmethod
    def dagster_event_type(cls) -> "DagsterEventType":
        from dagster._core.events import DagsterEventType

        return DagsterEventType.SLA_VIOLATING


@whitelist_for_serdes
@record
class SlaPassing:
    sla_name: str
    asset_key: AssetKey
    # The associated event log entry ID which led to the asset passing its SLA.
    last_event_storage_id: int
    # Time at which the passing event occurred
    last_event_timestamp: float
    reason_md: str
    metadata: Mapping[str, Any]

    @classmethod
    def dagster_event_type(cls) -> "DagsterEventType":
        from dagster._core.events import DagsterEventType

        return DagsterEventType.SLA_PASSING


# If the asset is missing and therefore the SLA cannot be evaluated.
@whitelist_for_serdes
@record
class SlaUnknown:
    sla_name: str
    asset_key: AssetKey
    reason_md: str
    metadata: Mapping[str, Any]

    @classmethod
    def dagster_event_type(cls) -> "DagsterEventType":
        from dagster._core.events import DagsterEventType

        return DagsterEventType.SLA_UNKNOWN


SlaEvaluationResult = Union[SlaPassing, SlaViolating, SlaUnknown]
