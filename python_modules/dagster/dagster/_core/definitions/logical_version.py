from __future__ import annotations

from typing import Optional

from typing_extensions import Final

from dagster import _check as check
from dagster._core.events.log import EventLogEntry


class LogicalVersion:
    """Class that represents a logical version for an asset.

    Args:
        value (str): An arbitrary string representing a logical version.
    """

    def __init__(self, value: str):
        self.value = check.str_param(value, "value")

    def __eq__(self, other: LogicalVersion):
        return self.value == other.value


DEFAULT_LOGICAL_VERSION: Final[LogicalVersion] = LogicalVersion("INITIAL")


def extract_logical_version_from_event_log_entry(event: EventLogEntry) -> Optional[LogicalVersion]:
    from dagster._core.events import AssetObservationData, StepMaterializationData

    data = check.not_none(event.dagster_event).event_specific_data
    if isinstance(data, StepMaterializationData):
        event_data = data.materialization
    elif isinstance(data, AssetObservationData):
        event_data = data.asset_observation
    else:
        assert False, "Bad data"
    value = next(
        (
            entry.value.value
            for entry in event_data.metadata_entries
            if entry.label == "logical_version"
        ),
        None,
    )
    return LogicalVersion(value) if value is not None else None
