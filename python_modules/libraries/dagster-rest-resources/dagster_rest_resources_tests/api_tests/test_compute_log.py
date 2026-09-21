from unittest.mock import Mock

import pytest
from dagster_rest_resources.__generated__.get_captured_logs import (
    GetCapturedLogs,
    GetCapturedLogsCapturedLogs,
)
from dagster_rest_resources.__generated__.get_captured_logs_metadata import (
    GetCapturedLogsMetadata,
    GetCapturedLogsMetadataCapturedLogsMetadata,
)
from dagster_rest_resources.__generated__.get_logs_captured_events import (
    GetLogsCapturedEvents,
    GetLogsCapturedEventsLogsForRunEventConnection,
    GetLogsCapturedEventsLogsForRunEventConnectionEventsLogsCapturedEvent,
    GetLogsCapturedEventsLogsForRunPythonError,
    GetLogsCapturedEventsLogsForRunRunNotFoundError,
)
from dagster_rest_resources.api.compute_log import DgApiComputeLogApi
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.compute_log import (
    DgApiComputeLogLinkList,
    DgApiComputeLogList,
    DgApiStepComputeLog,
    DgApiStepComputeLogLink,
)
from dagster_rest_resources.schemas.exception import DagsterPlusGraphqlError

_RUN_ID = "b45fff8a-7def-43b8-805d-1cf5f435c997"


def _make_event_connection(
    events=None,
    cursor=None,
    has_more=False,
) -> GetLogsCapturedEventsLogsForRunEventConnection:
    return GetLogsCapturedEventsLogsForRunEventConnection(
        __typename="EventConnection",
        events=events or [],
        cursor=cursor or "",
        hasMore=has_more,
    )


def _make_captured_event(
    file_key: str,
    step_keys: list[str] | None = None,
    external_stdout_url: str | None = None,
    external_stderr_url: str | None = None,
) -> GetLogsCapturedEventsLogsForRunEventConnectionEventsLogsCapturedEvent:
    return GetLogsCapturedEventsLogsForRunEventConnectionEventsLogsCapturedEvent(
        __typename="LogsCapturedEvent",
        fileKey=file_key,
        stepKeys=step_keys,
        externalStdoutUrl=external_stdout_url,
        externalStderrUrl=external_stderr_url,
    )


class TestGetLogs:
    def test_returns_logs(self):
        client = Mock(spec=IGraphQLClient)
        client.get_logs_captured_events.return_value = GetLogsCapturedEvents(
            logsForRun=_make_event_connection(
                events=[_make_captured_event("test-step", step_keys=["test-step"])],
            )
        )
        client.get_captured_logs.return_value = GetCapturedLogs(
            capturedLogs=GetCapturedLogsCapturedLogs(stdout="test\n", stderr=None, cursor=None)
        )

        result = DgApiComputeLogApi(_client=client).get_logs(_RUN_ID)

        assert result == DgApiComputeLogList(
            run_id=_RUN_ID,
            items=[
                DgApiStepComputeLog(
                    file_key="test-step",
                    step_keys=["test-step"],
                    stdout="test\n",
                    stderr=None,
                    cursor=None,
                )
            ],
        )
        client.get_captured_logs.assert_called_once_with(
            log_key=[_RUN_ID, "compute_logs", "test-step"],
            cursor=None,
            limit=None,
        )

    def test_returns_empty(self):
        client = Mock(spec=IGraphQLClient)
        client.get_logs_captured_events.return_value = GetLogsCapturedEvents(
            logsForRun=_make_event_connection(events=[])
        )

        result = DgApiComputeLogApi(_client=client).get_logs(_RUN_ID)

        assert result == DgApiComputeLogList(run_id=_RUN_ID, items=[])
        client.get_captured_logs.assert_not_called()

    def test_step_key_filter(self):
        client = Mock(spec=IGraphQLClient)
        client.get_logs_captured_events.return_value = GetLogsCapturedEvents(
            logsForRun=_make_event_connection(
                events=[
                    _make_captured_event("step_a", step_keys=["step_a"]),
                    _make_captured_event("step_b", step_keys=["step_b"]),
                ],
            )
        )
        client.get_captured_logs.return_value = GetCapturedLogs(
            capturedLogs=GetCapturedLogsCapturedLogs(stdout=None, stderr=None, cursor=None)
        )

        result = DgApiComputeLogApi(_client=client).get_logs(_RUN_ID, step_key="step_a")

        assert len(result.items) == 1
        assert result.items[0].file_key == "step_a"

    def test_run_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_logs_captured_events.return_value = GetLogsCapturedEvents(
            logsForRun=GetLogsCapturedEventsLogsForRunRunNotFoundError(
                __typename="RunNotFoundError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching logs for run"):
            DgApiComputeLogApi(_client=client).get_logs(_RUN_ID)

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_logs_captured_events.return_value = GetLogsCapturedEvents(
            logsForRun=GetLogsCapturedEventsLogsForRunPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching logs for run"):
            DgApiComputeLogApi(_client=client).get_logs(_RUN_ID)

    def test_pagination(self):
        client = Mock(spec=IGraphQLClient)
        page1 = GetLogsCapturedEvents(
            logsForRun=_make_event_connection(
                events=[_make_captured_event("step_a", step_keys=["step_a"])],
                cursor="cursor-1",
                has_more=True,
            )
        )
        page2 = GetLogsCapturedEvents(
            logsForRun=_make_event_connection(
                events=[_make_captured_event("step_b", step_keys=["step_b"])],
                cursor="",
                has_more=False,
            )
        )
        client.get_logs_captured_events.side_effect = [page1, page2]
        client.get_captured_logs.return_value = GetCapturedLogs(
            capturedLogs=GetCapturedLogsCapturedLogs(stdout=None, stderr=None, cursor=None)
        )

        result = DgApiComputeLogApi(_client=client).get_logs(_RUN_ID)

        assert len(result.items) == 2
        assert client.get_logs_captured_events.call_count == 2


class TestGetLogLinks:
    def test_uses_external_urls_when_available(self):
        client = Mock(spec=IGraphQLClient)
        client.get_logs_captured_events.return_value = GetLogsCapturedEvents(
            logsForRun=_make_event_connection(
                events=[
                    _make_captured_event(
                        "test-step",
                        step_keys=["test-step"],
                        external_stdout_url="test.com/stdout",
                        external_stderr_url="test.com/stderr",
                    )
                ]
            )
        )

        result = DgApiComputeLogApi(_client=client).get_log_links(_RUN_ID)

        assert result == DgApiComputeLogLinkList(
            run_id=_RUN_ID,
            items=[
                DgApiStepComputeLogLink(
                    file_key="test-step",
                    step_keys=["test-step"],
                    stdout_download_url="test.com/stdout",
                    stderr_download_url="test.com/stderr",
                )
            ],
        )
        client.get_captured_logs_metadata.assert_not_called()

    def test_fetches_metadata_when_no_external_urls(self):
        client = Mock(spec=IGraphQLClient)
        client.get_logs_captured_events.return_value = GetLogsCapturedEvents(
            logsForRun=_make_event_connection(
                events=[_make_captured_event("test-step", step_keys=["test-step"])]
            )
        )
        client.get_captured_logs_metadata.return_value = GetCapturedLogsMetadata(
            capturedLogsMetadata=GetCapturedLogsMetadataCapturedLogsMetadata(
                stdoutDownloadUrl="storage.test.com/stdout",
                stderrDownloadUrl="storage.test.com/stderr",
            )
        )

        result = DgApiComputeLogApi(_client=client).get_log_links(_RUN_ID)

        assert result.items[0].stdout_download_url == "storage.test.com/stdout"
        assert result.items[0].stderr_download_url == "storage.test.com/stderr"
        client.get_captured_logs_metadata.assert_called_once_with(
            log_key=[_RUN_ID, "compute_logs", "test-step"]
        )

    def test_returns_empty(self):
        client = Mock(spec=IGraphQLClient)
        client.get_logs_captured_events.return_value = GetLogsCapturedEvents(
            logsForRun=_make_event_connection(events=[])
        )

        result = DgApiComputeLogApi(_client=client).get_log_links(_RUN_ID)

        assert result == DgApiComputeLogLinkList(run_id=_RUN_ID, items=[])
