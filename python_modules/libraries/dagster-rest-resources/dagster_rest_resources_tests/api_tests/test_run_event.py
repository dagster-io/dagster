from unittest.mock import Mock

import pytest
from dagster_rest_resources.__generated__.enums import DagsterEventType, LogLevel
from dagster_rest_resources.__generated__.get_run_events import (
    GetRunEvents,
    GetRunEventsLogsForRunEventConnection,
    GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEvent,
    GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEventError,
    GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEventErrorCause,
    GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEventErrorCauseCause,
    GetRunEventsLogsForRunEventConnectionEventsRunStartEvent,
    GetRunEventsLogsForRunPythonError,
    GetRunEventsLogsForRunRunNotFoundError,
)
from dagster_rest_resources.api.run_event import DgApiRunEventApi
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import DagsterPlusGraphqlError
from dagster_rest_resources.schemas.run_event import DgApiRunEventList

_RUN_ID = "a34cd75c-cfa9-4e99-8f0a-955492b89afd"


def _make_event_connection(
    events=None,
    cursor="",
    has_more=False,
) -> GetRunEventsLogsForRunEventConnection:
    return GetRunEventsLogsForRunEventConnection(
        __typename="EventConnection",
        events=events or [],
        cursor=cursor,
        hasMore=has_more,
    )


def _make_run_start_event(
    run_id: str = _RUN_ID,
    message: str = "Run started.",
    timestamp: str = "1000000000000",
    level: LogLevel = LogLevel.INFO,
    step_key: str | None = None,
    event_type: DagsterEventType | None = DagsterEventType.PIPELINE_START,
) -> GetRunEventsLogsForRunEventConnectionEventsRunStartEvent:
    return GetRunEventsLogsForRunEventConnectionEventsRunStartEvent(
        __typename="RunStartEvent",
        runId=run_id,
        message=message,
        timestamp=timestamp,
        level=level,
        stepKey=step_key,
        eventType=event_type,
    )


class TestGetEventsSinglePage:
    def test_returns_events(self):
        client = Mock(spec=IGraphQLClient)
        client.get_run_events.return_value = GetRunEvents(
            logsForRun=_make_event_connection(events=[_make_run_start_event()])
        )

        result = DgApiRunEventApi(_client=client).get_events(_RUN_ID)

        assert len(result.items) == 1
        assert result.items[0].run_id == _RUN_ID
        assert not result.has_more
        assert not result.cursor

    def test_returns_cursor_and_has_more(self):
        client = Mock(spec=IGraphQLClient)
        client.get_run_events.return_value = GetRunEvents(
            logsForRun=_make_event_connection(
                events=[_make_run_start_event()],
                cursor="test-cursor",
                has_more=True,
            )
        )

        result = DgApiRunEventApi(_client=client).get_events(_RUN_ID)

        assert result.cursor == "test-cursor"
        assert result.has_more is True

    def test_returns_empty(self):
        client = Mock(spec=IGraphQLClient)
        client.get_run_events.return_value = GetRunEvents(
            logsForRun=_make_event_connection(events=[])
        )

        result = DgApiRunEventApi(_client=client).get_events(_RUN_ID)

        assert result == DgApiRunEventList(items=[], cursor=None, has_more=False)

    def test_empty_cursor_becomes_none(self):
        client = Mock(spec=IGraphQLClient)
        client.get_run_events.return_value = GetRunEvents(
            logsForRun=_make_event_connection(events=[], cursor="", has_more=False)
        )

        result = DgApiRunEventApi(_client=client).get_events(_RUN_ID)

        assert result.cursor is None

    def test_run_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_run_events.return_value = GetRunEvents(
            logsForRun=GetRunEventsLogsForRunRunNotFoundError(
                __typename="RunNotFoundError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching events"):
            DgApiRunEventApi(_client=client).get_events(_RUN_ID)

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_run_events.return_value = GetRunEvents(
            logsForRun=GetRunEventsLogsForRunPythonError(__typename="PythonError", message="")
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching events"):
            DgApiRunEventApi(_client=client).get_events(_RUN_ID)


class TestGetEventsFiltered:
    def test_event_type_filter(self):
        client = Mock(spec=IGraphQLClient)
        client.get_run_events.return_value = GetRunEvents(
            logsForRun=_make_event_connection(
                events=[
                    _make_run_start_event(event_type=DagsterEventType.PIPELINE_START),
                    _make_run_start_event(event_type=DagsterEventType.STEP_FAILURE),
                ]
            )
        )

        result = DgApiRunEventApi(_client=client).get_events(
            _RUN_ID, event_types=("PIPELINE_START",)
        )

        assert len(result.items) == 1
        assert result.items[0].event_type == "PIPELINE_START"

    def test_event_type_filter_run_to_pipeline_alias(self):
        client = Mock(spec=IGraphQLClient)
        client.get_run_events.return_value = GetRunEvents(
            logsForRun=_make_event_connection(
                events=[
                    _make_run_start_event(event_type=DagsterEventType.PIPELINE_START),
                    _make_run_start_event(event_type=DagsterEventType.STEP_FAILURE),
                ]
            )
        )

        result = DgApiRunEventApi(_client=client).get_events(_RUN_ID, event_types=("RUN_START",))

        assert len(result.items) == 1
        assert result.items[0].event_type == "PIPELINE_START"

    def test_level_filter(self):
        client = Mock(spec=IGraphQLClient)
        client.get_run_events.return_value = GetRunEvents(
            logsForRun=_make_event_connection(
                events=[
                    _make_run_start_event(level=LogLevel.INFO),
                    _make_run_start_event(level=LogLevel.DEBUG),
                ]
            )
        )

        result = DgApiRunEventApi(_client=client).get_events(_RUN_ID, levels=("INFO",))

        assert len(result.items) == 1
        assert result.items[0].level == LogLevel.INFO

    def test_step_key_filter(self):
        client = Mock(spec=IGraphQLClient)
        client.get_run_events.return_value = GetRunEvents(
            logsForRun=_make_event_connection(
                events=[
                    _make_run_start_event(step_key="test_step_abc"),
                    _make_run_start_event(step_key="other_step"),
                ]
            )
        )

        result = DgApiRunEventApi(_client=client).get_events(_RUN_ID, step_keys=("test_step",))

        assert len(result.items) == 1
        assert result.items[0].step_key == "test_step_abc"

    def test_filter_paginates_until_limit_then_truncates(self):
        client = Mock(spec=IGraphQLClient)
        page1 = GetRunEvents(
            logsForRun=_make_event_connection(
                events=[
                    _make_run_start_event(),
                    _make_run_start_event(),
                ],
                cursor="cur-1",
                has_more=True,
            )
        )
        page2 = GetRunEvents(
            logsForRun=_make_event_connection(
                events=[
                    _make_run_start_event(),
                    _make_run_start_event(),
                ],
                cursor="cur-2",
                has_more=True,
            )
        )

        client.get_run_events.side_effect = [page1, page2]

        result = DgApiRunEventApi(_client=client).get_events(_RUN_ID, levels=("INFO",), limit=3)

        assert len(result.items) == 3
        assert result.cursor == "cur-2"
        assert result.has_more is True
        assert client.get_run_events.call_count == 2

    def test_filters_paginates_until_no_more(self):
        client = Mock(spec=IGraphQLClient)
        page1 = GetRunEvents(
            logsForRun=_make_event_connection(
                events=[_make_run_start_event(message="message-1")],
                cursor="cur1",
                has_more=True,
            )
        )
        page2 = GetRunEvents(
            logsForRun=_make_event_connection(
                events=[_make_run_start_event(message="message-2")],
                cursor="",
                has_more=False,
            )
        )
        client.get_run_events.side_effect = [page1, page2]

        result = DgApiRunEventApi(_client=client).get_events(_RUN_ID, levels=("INFO",), limit=1000)

        assert client.get_run_events.call_count == 2

        assert len(result.items) == 2
        assert result.items[0].message == "message-1"
        assert result.items[1].message == "message-2"
        assert result.cursor is None
        assert result.has_more is False


class TestGetEventsErrorConversion:
    def test_converts_step_failure_error(self):
        client = Mock(spec=IGraphQLClient)
        client.get_run_events.return_value = GetRunEvents(
            logsForRun=_make_event_connection(
                events=[
                    GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEvent(
                        __typename="ExecutionStepFailureEvent",
                        runId=_RUN_ID,
                        message="test_message",
                        timestamp="1000000001000",
                        level=LogLevel.ERROR,
                        stepKey="test_step",
                        eventType=DagsterEventType.STEP_FAILURE,
                        error=GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEventError(
                            message="test_message_error",
                            className="TestClassName",
                            stack=["  File foo.py line 1\n"],
                            cause=None,
                        ),
                    )
                ]
            )
        )

        result = DgApiRunEventApi(_client=client).get_events(_RUN_ID)

        assert len(result.items) == 1
        event = result.items[0]
        assert event.error is not None
        assert event.error.message == "test_message_error"
        assert event.error.className == "TestClassName"
        assert event.error.stack == ["  File foo.py line 1\n"]

    def test_converts_step_failure_error_nested(self):
        client = Mock(spec=IGraphQLClient)
        failure = GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEvent(
            __typename="ExecutionStepFailureEvent",
            runId=_RUN_ID,
            message="failed",
            timestamp="1000000001000",
            level=LogLevel.ERROR,
            stepKey="step",
            eventType=DagsterEventType.STEP_FAILURE,
            error=GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEventError(
                message="error",
                className="Error",
                stack=["  line 1\n"],
                cause=GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEventErrorCause(
                    message="deeper error",
                    className="DeeperError",
                    stack=["  line 2\n"],
                    cause=GetRunEventsLogsForRunEventConnectionEventsExecutionStepFailureEventErrorCauseCause(
                        message="deepest error",
                        className="DeepestError",
                        stack=["  line 3\n"],
                    ),
                ),
            ),
        )
        client.get_run_events.return_value = GetRunEvents(
            logsForRun=_make_event_connection(events=[failure])
        )

        result = DgApiRunEventApi(_client=client).get_events(_RUN_ID)

        error = result.items[0].error
        assert error is not None
        assert error.message == "error"

        assert error.cause is not None
        assert error.cause.message == "deeper error"

        assert error.cause.cause is not None
        assert error.cause.cause.message == "deepest error"

        assert error.cause.cause.cause is None

    def test_non_failure_event_has_no_error(self):
        client = Mock(spec=IGraphQLClient)
        client.get_run_events.return_value = GetRunEvents(
            logsForRun=_make_event_connection(events=[_make_run_start_event()])
        )

        result = DgApiRunEventApi(_client=client).get_events(_RUN_ID)

        assert result.items[0].error is None
