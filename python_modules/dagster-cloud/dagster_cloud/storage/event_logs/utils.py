import os

from dagster import DagsterEvent
from dagster._core.events import (
    EngineEventData,
    HookErroredData,
    JobCanceledData,
    JobFailureData,
    StepFailureData,
    StepRetryData,
)
from dagster._core.events.log import EventLogEntry
from dagster._utils.error import SerializableErrorInfo, truncate_serialized_error


def _get_error_character_size_limit() -> int:
    return int(os.getenv("DAGSTER_CLOUD_MAXIMUM_EVENT_ERROR_SIZE", "500000"))


def _get_maximum_event_message_characters() -> int:
    return int(os.getenv("DAGSTER_CLOUD_MAXIMUM_EVENT_MESSAGE_CHARACTERS", "50000"))


def _truncate_dagster_event_error(
    error_info: SerializableErrorInfo | None,
    truncations: list[str],
) -> SerializableErrorInfo | None:
    if not error_info:
        return error_info

    return truncate_serialized_error(
        error_info,
        _get_error_character_size_limit(),
        max_depth=5,
        truncations=truncations,
    )


def _truncate_dagster_event(
    dagster_event: DagsterEvent | None,
    truncations: list[str],
) -> DagsterEvent | None:
    if not dagster_event:
        return dagster_event
    event_specific_data = dagster_event.event_specific_data

    if isinstance(event_specific_data, JobFailureData):
        event_specific_data = event_specific_data._replace(
            error=_truncate_dagster_event_error(
                event_specific_data.error,
                truncations,
            ),
            first_step_failure_event=_truncate_dagster_event(
                event_specific_data.first_step_failure_event,
                truncations,
            ),
        )
    elif isinstance(
        event_specific_data,
        (JobCanceledData, EngineEventData, HookErroredData, StepFailureData, StepRetryData),
    ):
        event_specific_data = event_specific_data._replace(
            error=_truncate_dagster_event_error(  # ty: ignore[invalid-argument-type]
                event_specific_data.error,
                truncations,
            ),
        )

    return dagster_event._replace(event_specific_data=event_specific_data)


def truncate_event(
    event: EventLogEntry,
    maximum_length=None,
    truncations: list[str] | None = None,
) -> EventLogEntry:
    truncations = [] if truncations is None else truncations

    if event.dagster_event:
        event = event._replace(
            dagster_event=_truncate_dagster_event(
                event.dagster_event,
                truncations,
            )
        )

    maximum_length = (
        maximum_length if maximum_length is not None else _get_maximum_event_message_characters()
    )

    len_usr_msg = len(event.user_message)
    if len_usr_msg > maximum_length:
        truncations.append(f"user_message {len_usr_msg} to {maximum_length}")
        return event._replace(
            user_message=(
                f"[TRUNCATED from {len_usr_msg} characters to"
                f" {maximum_length}]"
                f" {event.user_message[:maximum_length]} [TRUNCATED]"
            ),
        )

    return event
