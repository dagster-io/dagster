from __future__ import annotations

from hashlib import sha256
from typing import TYPE_CHECKING, Optional, Sequence, Union

from typing_extensions import Final

from dagster import _check as check

if TYPE_CHECKING:
    from dagster._core.definitions.events import AssetKey, Materialization
    from dagster._core.events.log import EventLogEntry

LOGICAL_VERSION_TAG_KEY: Final[str] = "dagster/logical_version"
CODE_VERSION_TAG_KEY: Final[str] = "dagster/code_version"
INPUT_LOGICAL_VERSION_TAG_KEY_PREFIX: Final[str] = "dagster/input_logical_version"
INPUT_EVENT_POINTER_TAG_KEY_PREFIX: Final[str] = "dagster/input_event_pointer"


def get_input_logical_version_tag_key(input_key: AssetKey) -> str:
    return f"f{INPUT_LOGICAL_VERSION_TAG_KEY_PREFIX}/{input_key.to_user_string()}"


def get_input_event_pointer_tag_key(input_key: AssetKey) -> str:
    return f"{INPUT_EVENT_POINTER_TAG_KEY_PREFIX}/{input_key.to_user_string()}"

class LogicalVersion:
    """Class that represents a logical version for an asset.

    Args:
        value (str): An arbitrary string representing a logical version.
    """

    def __init__(self, value: str):
        self.value = check.str_param(value, "value")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LogicalVersion):
            return False
        return self.value == other.value

    def __hash__(self) -> str:
        return self.value

UNKNOWN_LOGICAL_VERSION: Final[LogicalVersion] = LogicalVersion("UNKNOWN")

DEFAULT_LOGICAL_VERSION: Final[LogicalVersion] = LogicalVersion("INITIAL")

def compute_logical_version(code_version: str, input_logical_versions: Sequence[LogicalVersion]):
    """Compute a logical version from inputs.

    Args:
        code_version (LogicalVersion): The code version of the computation.
        input_logical_versions (Sequence[LogicalVersion]): The logical versions of the inputs.

    Returns:
        LogicalVersion: The computed logical version.
    """
    check.inst_param(code_version, "code_version", LogicalVersion)
    check.sequence_param(input_logical_versions, "input_versions", of_type=LogicalVersion)

    if UNKNOWN_LOGICAL_VERSION in input_logical_versions:
        return UNKNOWN_LOGICAL_VERSION

    all_inputs = [code_version, *(v.value for v in input_logical_versions)]

    hash_sig = sha256()
    hash_sig.update(bytearray("".join(all_inputs), "utf8"))
    return LogicalVersion(hash_sig.hexdigest())


    return f"{code_version}/{','.join(sorted(input_versions.items()))}"

def extract_logical_version_from_event_log_entry(event: EventLogEntry) -> Optional[LogicalVersion]:
    from dagster._core.definitions.events import AssetMaterialization, AssetObservation
    from dagster._core.events import AssetObservationData, StepMaterializationData

    data = check.not_none(event.dagster_event).event_specific_data
    event_data: Union[Materialization, AssetMaterialization, AssetObservation]
    if isinstance(data, StepMaterializationData):
        event_data = data.materialization
    elif isinstance(data, AssetObservationData):
        event_data = data.asset_observation
    else:
        assert False, "Bad data"
    assert isinstance(event_data, (AssetMaterialization, AssetObservation))
    tags = event_data.tags or {}
    value = tags.get(LOGICAL_VERSION_TAG_KEY)
    return LogicalVersion(value) if value is not None else None
