from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from typing_extensions import assert_never

from dagster_rest_resources.__generated__.get_run_events import (
    GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEvent,
    GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEventError,
    GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEventErrorCause,
    GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEventErrorCauseCause,
)
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import DagsterPlusGraphqlError
from dagster_rest_resources.schemas.run_event import (
    DgApiErrorInfo,
    DgApiRunEvent,
    DgApiRunEventList,
)

if TYPE_CHECKING:
    from dagster_rest_resources.__generated__.get_run_events import (
        GetRunEventsLogsForRunEventConnectionEventsAlertFailureEvent,
        GetRunEventsLogsForRunEventConnectionEventsAlertStartEvent,
        GetRunEventsLogsForRunEventConnectionEventsAlertSuccessEvent,
        GetRunEventsLogsForRunEventConnectionEventsAssetCheckEvaluationEvent,
        GetRunEventsLogsForRunEventConnectionEventsAssetCheckEvaluationPlannedEvent,
        GetRunEventsLogsForRunEventConnectionEventsAssetMaterializationPlannedEvent,
        GetRunEventsLogsForRunEventConnectionEventsEngineEvent,
        GetRunEventsLogsForRunEventConnectionEventsExecutionStepInputEvent,
        GetRunEventsLogsForRunEventConnectionEventsExecutionStepOutputEvent,
        GetRunEventsLogsForRunEventConnectionEventsExecutionStepRestartEvent,
        GetRunEventsLogsForRunEventConnectionEventsExecutionStepSkippedEvent,
        GetRunEventsLogsForRunEventConnectionEventsExecutionStepStartEvent,
        GetRunEventsLogsForRunEventConnectionEventsExecutionStepSuccessEvent,
        GetRunEventsLogsForRunEventConnectionEventsExecutionStepUpForRetryEvent,
        GetRunEventsLogsForRunEventConnectionEventsFailedToMaterializeEvent,
        GetRunEventsLogsForRunEventConnectionEventsHandledOutputEvent,
        GetRunEventsLogsForRunEventConnectionEventsHealthChangedEvent,
        GetRunEventsLogsForRunEventConnectionEventsHookCompletedEvent,
        GetRunEventsLogsForRunEventConnectionEventsHookErroredEvent,
        GetRunEventsLogsForRunEventConnectionEventsHookSkippedEvent,
        GetRunEventsLogsForRunEventConnectionEventsLoadedInputEvent,
        GetRunEventsLogsForRunEventConnectionEventsLogMessageEvent,
        GetRunEventsLogsForRunEventConnectionEventsLogsCapturedEvent,
        GetRunEventsLogsForRunEventConnectionEventsMaterializationEvent,
        GetRunEventsLogsForRunEventConnectionEventsObjectStoreOperationEvent,
        GetRunEventsLogsForRunEventConnectionEventsObservationEvent,
        GetRunEventsLogsForRunEventConnectionEventsResourceInitFailureEvent,
        GetRunEventsLogsForRunEventConnectionEventsResourceInitStartedEvent,
        GetRunEventsLogsForRunEventConnectionEventsResourceInitSuccessEvent,
        GetRunEventsLogsForRunEventConnectionEventsRunCanceledEvent,
        GetRunEventsLogsForRunEventConnectionEventsRunCancelingEvent,
        GetRunEventsLogsForRunEventConnectionEventsRunDequeuedEvent,
        GetRunEventsLogsForRunEventConnectionEventsRunEnqueuedEvent,
        GetRunEventsLogsForRunEventConnectionEventsRunFailureEvent,
        GetRunEventsLogsForRunEventConnectionEventsRunStartEvent,
        GetRunEventsLogsForRunEventConnectionEventsRunStartingEvent,
        GetRunEventsLogsForRunEventConnectionEventsRunSuccessEvent,
        GetRunEventsLogsForRunEventConnectionEventsStepExpectationResultEvent,
        GetRunEventsLogsForRunEventConnectionEventsStepWorkerStartedEvent,
        GetRunEventsLogsForRunEventConnectionEventsStepWorkerStartingEvent,
    )

_MAX_PAGES = 100

# Alias mapping for user-friendly RUN_* names to GraphQL PIPELINE_* values
_EVENT_TYPE_ALIASES: dict[str, str] = {
    "RUN_ENQUEUED": "PIPELINE_ENQUEUED",
    "RUN_DEQUEUED": "PIPELINE_DEQUEUED",
    "RUN_STARTING": "PIPELINE_STARTING",
    "RUN_START": "PIPELINE_START",
    "RUN_SUCCESS": "PIPELINE_SUCCESS",
    "RUN_FAILURE": "PIPELINE_FAILURE",
    "RUN_CANCELING": "PIPELINE_CANCELING",
    "RUN_CANCELED": "PIPELINE_CANCELED",
}


@dataclass(frozen=True)
class DgApiRunEventApi:
    _client: IGraphQLClient

    def get_events(
        self,
        run_id: str,
        event_types: tuple[str, ...] = (),
        step_keys: tuple[str, ...] = (),
        levels: tuple[str, ...] = (),
        limit: int = 100,
        after_cursor: str | None = None,
    ) -> DgApiRunEventList:
        has_client_filters = bool(event_types or levels or step_keys)

        if not has_client_filters:
            return self._fetch_single_page(run_id, limit=limit, after_cursor=after_cursor)

        return self._fetch_with_filters(
            run_id,
            event_types=event_types,
            step_keys=step_keys,
            levels=levels,
            limit=limit,
            after_cursor=after_cursor,
        )

    def _fetch_single_page(
        self,
        run_id: str,
        limit: int,
        after_cursor: str | None,
    ) -> DgApiRunEventList:
        result = self._client.get_run_events(
            run_id=run_id, limit=limit, after_cursor=after_cursor
        ).logs_for_run

        match result.typename__:
            case "EventConnection":
                events = [self._convert_event(e) for e in result.events]  # ty: ignore[unresolved-attribute]
                return DgApiRunEventList(
                    items=events,
                    cursor=result.cursor or None,  # ty: ignore[unresolved-attribute]
                    has_more=result.has_more,  # ty: ignore[unresolved-attribute]
                )
            case "RunNotFoundError":
                raise DagsterPlusGraphqlError(f"Error fetching events: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error fetching events: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def _fetch_with_filters(
        self,
        run_id: str,
        event_types: Sequence[str],
        step_keys: Sequence[str],
        levels: Sequence[str],
        limit: int,
        after_cursor: str | None,
    ) -> DgApiRunEventList:
        type_filter = self._build_type_filter(event_types) if event_types else None
        level_filter = {lv.upper() for lv in levels} if levels else None
        step_key_filter = [sk.lower() for sk in step_keys] if step_keys else None

        events: list[DgApiRunEvent] = []
        cursor = after_cursor
        has_more = True

        for _ in range(_MAX_PAGES):
            page = self._fetch_single_page(run_id=run_id, limit=limit, after_cursor=cursor)

            for e in page.items:
                if (
                    (not type_filter or (e.event_type or "").upper() in type_filter)
                    and (not level_filter or e.level.upper() in level_filter)
                    and (
                        not step_key_filter
                        or any(sk in (e.step_key or "").lower() for sk in step_key_filter)
                    )
                ):
                    events.append(e)
            cursor = page.cursor or None
            has_more = page.has_more

            if len(events) >= limit:
                events = events[:limit]
                break
            if not has_more:
                break

        return DgApiRunEventList(
            items=events,
            cursor=cursor,
            has_more=has_more,
        )

    def _convert_event(
        self,
        event: """GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEvent
        | GetRunEventsLogsForRunEventConnectionEventsExecutionStepInputEvent
        | GetRunEventsLogsForRunEventConnectionEventsExecutionStepOutputEvent
        | GetRunEventsLogsForRunEventConnectionEventsExecutionStepSkippedEvent
        | GetRunEventsLogsForRunEventConnectionEventsExecutionStepStartEvent
        | GetRunEventsLogsForRunEventConnectionEventsExecutionStepSuccessEvent
        | GetRunEventsLogsForRunEventConnectionEventsExecutionStepUpForRetryEvent
        | GetRunEventsLogsForRunEventConnectionEventsExecutionStepRestartEvent
        | GetRunEventsLogsForRunEventConnectionEventsHealthChangedEvent
        | GetRunEventsLogsForRunEventConnectionEventsLogMessageEvent
        | GetRunEventsLogsForRunEventConnectionEventsResourceInitFailureEvent
        | GetRunEventsLogsForRunEventConnectionEventsResourceInitStartedEvent
        | GetRunEventsLogsForRunEventConnectionEventsResourceInitSuccessEvent
        | GetRunEventsLogsForRunEventConnectionEventsRunFailureEvent
        | GetRunEventsLogsForRunEventConnectionEventsRunStartEvent
        | GetRunEventsLogsForRunEventConnectionEventsRunEnqueuedEvent
        | GetRunEventsLogsForRunEventConnectionEventsRunDequeuedEvent
        | GetRunEventsLogsForRunEventConnectionEventsRunStartingEvent
        | GetRunEventsLogsForRunEventConnectionEventsRunCancelingEvent
        | GetRunEventsLogsForRunEventConnectionEventsRunCanceledEvent
        | GetRunEventsLogsForRunEventConnectionEventsRunSuccessEvent
        | GetRunEventsLogsForRunEventConnectionEventsStepWorkerStartedEvent
        | GetRunEventsLogsForRunEventConnectionEventsStepWorkerStartingEvent
        | GetRunEventsLogsForRunEventConnectionEventsHandledOutputEvent
        | GetRunEventsLogsForRunEventConnectionEventsLoadedInputEvent
        | GetRunEventsLogsForRunEventConnectionEventsLogsCapturedEvent
        | GetRunEventsLogsForRunEventConnectionEventsObjectStoreOperationEvent
        | GetRunEventsLogsForRunEventConnectionEventsStepExpectationResultEvent
        | GetRunEventsLogsForRunEventConnectionEventsMaterializationEvent
        | GetRunEventsLogsForRunEventConnectionEventsObservationEvent
        | GetRunEventsLogsForRunEventConnectionEventsFailedToMaterializeEvent
        | GetRunEventsLogsForRunEventConnectionEventsEngineEvent
        | GetRunEventsLogsForRunEventConnectionEventsHookCompletedEvent
        | GetRunEventsLogsForRunEventConnectionEventsHookSkippedEvent
        | GetRunEventsLogsForRunEventConnectionEventsHookErroredEvent
        | GetRunEventsLogsForRunEventConnectionEventsAlertStartEvent
        | GetRunEventsLogsForRunEventConnectionEventsAlertSuccessEvent
        | GetRunEventsLogsForRunEventConnectionEventsAlertFailureEvent
        | GetRunEventsLogsForRunEventConnectionEventsAssetMaterializationPlannedEvent
        | GetRunEventsLogsForRunEventConnectionEventsAssetCheckEvaluationPlannedEvent
        | GetRunEventsLogsForRunEventConnectionEventsAssetCheckEvaluationEvent""",
    ) -> DgApiRunEvent:
        error = None
        if (
            isinstance(event, GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEvent)
            and event.error is not None
        ):
            error = self._convert_error(event.error)

        return DgApiRunEvent(
            run_id=event.run_id,
            message=event.message,
            timestamp=event.timestamp,
            level=event.level,
            step_key=event.step_key,
            event_type=event.event_type,
            error=error,
        )

    def _convert_error(
        self,
        error: (
            GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEventError
            | GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEventErrorCause
            | GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEventErrorCauseCause
        ),
    ) -> DgApiErrorInfo:
        cause = None
        if (
            isinstance(
                error,
                (
                    GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEventError,
                    GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEventErrorCause,
                ),
            )
            and error.cause is not None
        ):
            cause = self._convert_error(error.cause)
        return DgApiErrorInfo(
            message=error.message,
            className=error.class_name,
            stack=list(error.stack),
            cause=cause,
        )

    def _build_type_filter(self, event_types: Sequence[str]) -> set[str]:
        types: set[str] = set()
        for t in event_types:
            t_upper = t.upper()
            types.add(t_upper)
            # add the alias so both RUN_START and PIPELINE_START work
            if t_upper in _EVENT_TYPE_ALIASES:
                types.add(_EVENT_TYPE_ALIASES[t_upper])

        return types
