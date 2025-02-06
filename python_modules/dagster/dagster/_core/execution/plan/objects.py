from collections.abc import Mapping
from enum import Enum
from typing import TYPE_CHECKING, NamedTuple, Optional

import dagster._check as check
from dagster._core.definitions.metadata import (
    MetadataFieldSerializer,
    MetadataValue,
    normalize_metadata,
)
from dagster._serdes import whitelist_for_serdes
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info
from dagster._utils.types import ExcInfo

if TYPE_CHECKING:
    from dagster._core.execution.context.system import StepExecutionContext


@whitelist_for_serdes(
    storage_field_names={"metadata": "metadata_entries"},
    field_serializers={"metadata": MetadataFieldSerializer},
)
class TypeCheckData(
    NamedTuple(
        "_TypeCheckData",
        [
            ("success", bool),
            ("label", str),
            ("description", Optional[str]),
            ("metadata", Mapping[str, MetadataValue]),
        ],
    )
):
    def __new__(cls, success, label, description=None, metadata=None):
        return super().__new__(
            cls,
            success=check.bool_param(success, "success"),
            label=check.str_param(label, "label"),
            description=check.opt_str_param(description, "description"),
            metadata=normalize_metadata(
                check.opt_mapping_param(metadata, "metadata", key_type=str)
            ),
        )


@whitelist_for_serdes(
    storage_field_names={"metadata": "metadata_entries"},
    field_serializers={"metadata": MetadataFieldSerializer},
)
class UserFailureData(
    NamedTuple(
        "_UserFailureData",
        [
            ("label", str),
            ("description", Optional[str]),
            ("metadata", Mapping[str, MetadataValue]),
        ],
    )
):
    def __new__(cls, label, description=None, metadata=None):
        return super().__new__(
            cls,
            label=check.str_param(label, "label"),
            description=check.opt_str_param(description, "description"),
            metadata=normalize_metadata(
                check.opt_mapping_param(metadata, "metadata", key_type=str)
            ),
        )


@whitelist_for_serdes
class ErrorSource(Enum):
    # An error that occurs while executing framework code
    FRAMEWORK_ERROR = "FRAMEWORK_ERROR"
    # An error that occurs while executing user code
    USER_CODE_ERROR = "USER_CODE_ERROR"
    # An error occurred at an unexpected time
    UNEXPECTED_ERROR = "UNEXPECTED_ERROR"
    # Execution was interrupted
    INTERRUPT = "INTERRUPT"


@whitelist_for_serdes
class StepFailureData(
    NamedTuple(
        "_StepFailureData",
        [
            ("error", Optional[SerializableErrorInfo]),
            ("user_failure_data", Optional[UserFailureData]),
            ("error_source", ErrorSource),
        ],
    )
):
    def __new__(cls, error, user_failure_data, error_source=None):
        return super().__new__(
            cls,
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
            user_failure_data=check.opt_inst_param(
                user_failure_data, "user_failure_data", UserFailureData
            ),
            error_source=check.opt_inst_param(
                error_source, "error_source", ErrorSource, default=ErrorSource.FRAMEWORK_ERROR
            ),
        )

    @property
    def error_display_string(self) -> str:
        """Creates a display string that hides framework frames if the error arose in user code."""
        from dagster._core.errors import DagsterRedactedUserCodeError

        if not self.error:
            return ""
        if self.error_source == ErrorSource.USER_CODE_ERROR:
            # For a redacted error, just return the redacted message without any
            # internal user code error.
            if self.error.cls_name == DagsterRedactedUserCodeError.__name__:
                return self.error.to_string()

            user_code_error = self.error.cause
            check.invariant(
                user_code_error,
                "User code error is missing cause. User code errors are expected to have a"
                " causes, which are the errors thrown from user code.",
            )
            return self.error.message.strip() + ":\n\n" + user_code_error.to_string()
        else:
            return self.error.to_string()


def step_failure_event_from_exc_info(
    step_context: "StepExecutionContext",
    exc_info: ExcInfo,
    user_failure_data: Optional[UserFailureData] = None,
    error_source: Optional[ErrorSource] = None,
):
    from dagster._core.events import DagsterEvent

    return DagsterEvent.step_failure_event(
        step_context=step_context,
        step_failure_data=StepFailureData(
            error=serializable_error_info_from_exc_info(exc_info),
            user_failure_data=user_failure_data,
            error_source=error_source,
        ),
    )


@whitelist_for_serdes
class StepRetryData(
    NamedTuple(
        "_StepRetryData",
        [("error", SerializableErrorInfo), ("seconds_to_wait", Optional[check.Numeric])],
    )
):
    def __new__(cls, error, seconds_to_wait=None):
        return super().__new__(
            cls,
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
            seconds_to_wait=check.opt_numeric_param(seconds_to_wait, "seconds_to_wait"),
        )


@whitelist_for_serdes
class StepSuccessData(NamedTuple("_StepSuccessData", [("duration_ms", float)])):
    def __new__(cls, duration_ms):
        return super().__new__(cls, duration_ms=check.float_param(duration_ms, "duration_ms"))
