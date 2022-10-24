from __future__ import annotations

from hashlib import sha256
from typing import TYPE_CHECKING, AbstractSet, Mapping, Optional

from typing_extensions import Final

from dagster import _check as check

if TYPE_CHECKING:
    from dagster._core.definitions.events import AssetKey
    from dagster._core.events.log import EventLogEntry
    from dagster._core.instance import DagsterInstance


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


def get_logical_version_from_inputs(
    dependency_keys: AbstractSet[AssetKey],
    op_version: str,
    key_to_is_source_map: Mapping[AssetKey, bool],
    instance: DagsterInstance,
    logical_version_overrides: Optional[Mapping[AssetKey, LogicalVersion]] = None,
) -> LogicalVersion:
    logical_version_overrides = check.opt_mapping_param(
        logical_version_overrides, "logical_version_overrides"
    )
    ordered_dependency_keys = sorted(dependency_keys, key=str)
    dependency_logical_versions = [
        logical_version_overrides[k]
        if k in logical_version_overrides
        else get_most_recent_logical_version(k, key_to_is_source_map[k], instance)
        for k in ordered_dependency_keys
    ]
    all_inputs = [op_version, *(v.value for v in dependency_logical_versions)]
    hash_sig = sha256()
    hash_sig.update(bytearray("".join(all_inputs), "utf8"))
    return LogicalVersion(hash_sig.hexdigest())


def get_most_recent_logical_version(
    key: AssetKey, is_source: bool, instance: DagsterInstance
) -> LogicalVersion:
    from dagster._core.event_api import EventRecordsFilter
    from dagster._core.events import DagsterEventType

    if is_source:
        observations = instance.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_OBSERVATION,
                asset_key=key,
            ),
            limit=1,
        )
        event_record = next(iter(observations), None)
        event = event_record.event_log_entry if event_record else None
    else:
        event = instance.get_latest_materialization_events([key]).get(key)

    return DEFAULT_LOGICAL_VERSION if event is None else _extract_logical_version_from_event(event)


def _extract_logical_version_from_event(event: EventLogEntry) -> LogicalVersion:
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
    return LogicalVersion(value) if value is not None else DEFAULT_LOGICAL_VERSION
