from typing import List, NamedTuple, Optional

from dagster import check
from dagster.core.definitions.events import EventMetadataEntry
from dagster.serdes import whitelist_for_serdes
from dagster.utils.error import SerializableErrorInfo


@whitelist_for_serdes
class TypeCheckData(
    NamedTuple(
        "_TypeCheckData",
        [
            ("success", bool),
            ("label", str),
            ("description", Optional[str]),
            ("metadata_entries", List[EventMetadataEntry]),
        ],
    )
):
    def __new__(cls, success, label, description=None, metadata_entries=None):
        return super(TypeCheckData, cls).__new__(
            cls,
            success=check.bool_param(success, "success"),
            label=check.str_param(label, "label"),
            description=check.opt_str_param(description, "description"),
            metadata_entries=check.opt_list_param(
                metadata_entries, metadata_entries, of_type=EventMetadataEntry
            ),
        )


@whitelist_for_serdes
class UserFailureData(
    NamedTuple(
        "_UserFailureData",
        [
            ("label", str),
            ("description", Optional[str]),
            ("metadata_entries", List[EventMetadataEntry]),
        ],
    )
):
    def __new__(cls, label, description=None, metadata_entries=None):
        return super(UserFailureData, cls).__new__(
            cls,
            label=check.str_param(label, "label"),
            description=check.opt_str_param(description, "description"),
            metadata_entries=check.opt_list_param(
                metadata_entries, metadata_entries, of_type=EventMetadataEntry
            ),
        )


@whitelist_for_serdes
class StepFailureData(
    NamedTuple(
        "_StepFailureData",
        [("error", SerializableErrorInfo), ("user_failure_data", UserFailureData)],
    )
):
    def __new__(cls, error, user_failure_data):
        return super(StepFailureData, cls).__new__(
            cls,
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
            user_failure_data=check.opt_inst_param(
                user_failure_data, "user_failure_data", UserFailureData
            ),
        )


@whitelist_for_serdes
class StepRetryData(
    NamedTuple(
        "_StepRetryData", [("error", SerializableErrorInfo), ("seconds_to_wait", Optional[int])]
    )
):
    def __new__(cls, error, seconds_to_wait=None):
        return super(StepRetryData, cls).__new__(
            cls,
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
            seconds_to_wait=check.opt_int_param(seconds_to_wait, "seconds_to_wait"),
        )


@whitelist_for_serdes
class StepSuccessData(NamedTuple("_StepSuccessData", [("duration_ms", float)])):
    def __new__(cls, duration_ms):
        return super(StepSuccessData, cls).__new__(
            cls, duration_ms=check.float_param(duration_ms, "duration_ms")
        )
