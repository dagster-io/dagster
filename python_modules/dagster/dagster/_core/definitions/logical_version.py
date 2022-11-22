from __future__ import annotations

import warnings
from hashlib import sha256
from typing import TYPE_CHECKING, Mapping, NamedTuple, Optional, Union

from typing_extensions import Final

from dagster import _check as check
from dagster._annotations import experimental
from dagster._utils.backcompat import ExperimentalWarning

if TYPE_CHECKING:
    from dagster._core.definitions.events import (
        AssetKey,
        AssetMaterialization,
        AssetObservation,
        Materialization,
    )
    from dagster._core.events.log import EventLogEntry
    from dagster._core.instance import DagsterInstance


class UnknownValue:
    pass


UNKNOWN_VALUE: Final[UnknownValue] = UnknownValue()


@experimental
class LogicalVersion(
    NamedTuple(
        "_LogicalVersion",
        [("value", str)],
    )
):
    """Represents a logical version for an asset.

    Args:
        value (str): An arbitrary string representing a logical version.
    """

    def __new__(
        cls,
        value: str,
    ):
        return super(LogicalVersion, cls).__new__(
            cls,
            value=check.str_param(value, "value"),
        )


with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=ExperimentalWarning)
    UNKNOWN_LOGICAL_VERSION: Final[LogicalVersion] = LogicalVersion("UNKNOWN")
    DEFAULT_LOGICAL_VERSION: Final[LogicalVersion] = LogicalVersion("INITIAL")


class LogicalVersionProvenance(
    NamedTuple(
        "_LogicalVersionProvenance",
        [
            ("code_version", str),
            ("input_logical_versions", Mapping["AssetKey", LogicalVersion]),
        ],
    )
):
    def __new__(
        cls,
        code_version: str,
        input_logical_versions: Mapping["AssetKey", LogicalVersion],
    ):
        from dagster._core.definitions.events import AssetKey

        return super(LogicalVersionProvenance, cls).__new__(
            cls,
            code_version=check.str_param(code_version, "code_version"),
            input_logical_versions=check.mapping_param(
                input_logical_versions,
                "input_logical_versions",
                key_type=AssetKey,
                value_type=LogicalVersion,
            ),
        )

    @staticmethod
    def from_tags(tags: Mapping[str, str]) -> Optional[LogicalVersionProvenance]:
        from dagster._core.definitions.events import AssetKey

        code_version = tags.get(CODE_VERSION_TAG_KEY)
        if code_version is None:
            return None
        start_index = len(INPUT_LOGICAL_VERSION_TAG_KEY_PREFIX) + 1
        input_logical_versions = {
            AssetKey.from_user_string(k[start_index:]): LogicalVersion(tags[k])
            for k, v in tags.items()
            if k.startswith(INPUT_LOGICAL_VERSION_TAG_KEY_PREFIX)
        }
        return LogicalVersionProvenance(code_version, input_logical_versions)


# ########################
# ##### TAG KEYS
# ########################

LOGICAL_VERSION_TAG_KEY: Final[str] = "dagster/logical_version"
CODE_VERSION_TAG_KEY: Final[str] = "dagster/code_version"
INPUT_LOGICAL_VERSION_TAG_KEY_PREFIX: Final[str] = "dagster/input_logical_version"
INPUT_EVENT_POINTER_TAG_KEY_PREFIX: Final[str] = "dagster/input_event_pointer"


def get_input_logical_version_tag_key(input_key: "AssetKey") -> str:
    return f"{INPUT_LOGICAL_VERSION_TAG_KEY_PREFIX}/{input_key.to_user_string()}"


def get_input_event_pointer_tag_key(input_key: "AssetKey") -> str:
    return f"{INPUT_EVENT_POINTER_TAG_KEY_PREFIX}/{input_key.to_user_string()}"


# ########################
# ##### COMPUTE / EXTRACT
# ########################


def compute_logical_version(
    code_version: Union[str, UnknownValue],
    input_logical_versions: Mapping["AssetKey", LogicalVersion],
) -> LogicalVersion:
    """Compute a logical version from inputs.

    Args:
        code_version (LogicalVersion): The code version of the computation.
        input_logical_versions (Mapping[AssetKey, LogicalVersion]): The logical versions of the inputs.

    Returns:
        LogicalVersion: The computed logical version.
    """
    from dagster._core.definitions.events import AssetKey

    check.inst_param(code_version, "code_version", (str, UnknownValue))
    check.mapping_param(
        input_logical_versions, "input_versions", key_type=AssetKey, value_type=LogicalVersion
    )

    if (
        isinstance(code_version, UnknownValue)
        or UNKNOWN_LOGICAL_VERSION in input_logical_versions.values()
    ):
        return UNKNOWN_LOGICAL_VERSION

    ordered_input_versions = [
        input_logical_versions[k] for k in sorted(input_logical_versions.keys(), key=str)
    ]
    all_inputs = (code_version, *(v.value for v in ordered_input_versions))

    hash_sig = sha256()
    hash_sig.update(bytearray("".join(all_inputs), "utf8"))
    return LogicalVersion(hash_sig.hexdigest())


def extract_logical_version_from_entry(
    entry: EventLogEntry,
) -> Optional[LogicalVersion]:
    event_data = _extract_event_data_from_entry(entry)
    tags = event_data.tags or {}
    value = tags.get(LOGICAL_VERSION_TAG_KEY)
    return None if value is None else LogicalVersion(value)


def extract_logical_version_provenance_from_entry(
    entry: EventLogEntry,
) -> Optional[LogicalVersionProvenance]:
    event_data = _extract_event_data_from_entry(entry)
    tags = event_data.tags or {}
    return LogicalVersionProvenance.from_tags(tags)


def _extract_event_data_from_entry(
    entry: EventLogEntry,
) -> Union["AssetMaterialization", "AssetObservation"]:
    from dagster._core.definitions.events import AssetMaterialization, AssetObservation
    from dagster._core.events import AssetObservationData, StepMaterializationData

    data = check.not_none(entry.dagster_event).event_specific_data
    event_data: Union[Materialization, AssetMaterialization, AssetObservation]
    if isinstance(data, StepMaterializationData):
        event_data = data.materialization
    elif isinstance(data, AssetObservationData):
        event_data = data.asset_observation
    else:
        check.failed(f"Unexpected event type {type(data)}")

    assert isinstance(event_data, (AssetMaterialization, AssetObservation))
    return event_data
