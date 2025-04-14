import logging
import threading
from unittest import mock

import kubernetes
import pytest
from dagster_k8s.pipes import PipesK8sPodLogsMessageReader, _is_kube_timestamp


def _noop(*args, **kwargs):
    pass


LOG_LINES = [
    b'2025-04-09T18:30:45.741881210Z 2025-04-09 18:30:45 +0000 - dagster - DEBUG - run_etl_pipeline - fad927cf-0409-401b-9400-ffea6f709620 - 260 - enriched_data.concat_chunk_list - LOADED_INPUT - Loaded input "chunks" using input manager "io_manager", from output "result" of step "enriched_data.process_chunk[5]"',
    b"2025-04-09T18:30:45.741884005Z 2025-04-09 18:30:45 +0000 - dagster - DEBUG - run_etl_pipeline - fad927cf-0409-401b-9400-ffea6f709620 - enriched_data.concat_chunk_list - Loading file from: /opt/dagster/dagster_home/storage/fad927cf-0409-401b-9400-ffea6f709620/enriched_data.process_chunk[6]/result using PickledObjectFilesystemIOManager...",
    b"2025-04-09T18:30:47.741884005Z HELLO",
]


def flaky_log_stream():
    yield LOG_LINES[0]
    yield LOG_LINES[1]
    raise Exception(  # this will prevent the previous line from being fully processed too since it waits to detect a new line
        "transient network error"
    )


def working_log_stream():
    yield from LOG_LINES


def test_stream_retry_and_succeed():
    reader = PipesK8sPodLogsMessageReader()

    with mock.patch("dagster._core.pipes.utils.extract_message_or_forward_to_file") as mock_extract:
        mock_flaky_core_api = mock.MagicMock()
        mock_flaky_core_api.read_namespaced_pod_log.side_effect = [
            flaky_log_stream(),
            working_log_stream(),
        ]

        with reader.read_messages(handler=mock.MagicMock()):
            reader.consume_pod_logs(
                context=mock.MagicMock(),
                core_api=mock_flaky_core_api,
                pod_name="foo",
                namespace="bar",
            )

        assert mock_extract.call_count == 3
        assert mock_extract.call_args_list[0] == mock.call(
            handler=mock.ANY,
            log_line=LOG_LINES[0].decode("utf-8").split(" ", 1)[1],
            file=mock.ANY,
        )
        assert mock_extract.call_args_list[1] == mock.call(
            handler=mock.ANY,
            log_line=LOG_LINES[1].decode("utf-8").split(" ", 1)[1],
            file=mock.ANY,
        )
        assert mock_extract.call_args_list[2] == mock.call(
            handler=mock.ANY,
            log_line=LOG_LINES[2].decode("utf-8").split(" ", 1)[1],
            file=mock.ANY,
        )


def test_stream_retry_and_fail():
    reader = PipesK8sPodLogsMessageReader()

    with mock.patch("dagster._core.pipes.utils.extract_message_or_forward_to_file") as mock_extract:
        mock_flaky_core_api = mock.MagicMock()
        mock_flaky_core_api.read_namespaced_pod_log.side_effect = [
            flaky_log_stream() for i in range(6)
        ]

        with reader.read_messages(handler=mock.MagicMock()):
            with pytest.raises(Exception, match="transient network error"):
                reader.consume_pod_logs(
                    context=mock.MagicMock(),
                    core_api=mock_flaky_core_api,
                    pod_name="foo",
                    namespace="bar",
                )
        # only logged/processed the first line because lines are processed once the processor
        # realizes a new line has come in
        assert mock_extract.call_count == 1
        assert mock_extract.call_args_list[0] == mock.call(
            handler=mock.ANY,
            log_line=LOG_LINES[0].decode("utf-8").split(" ", 1)[1],
            file=mock.ANY,
        )


@pytest.mark.filterwarnings("ignore::dagster.PreviewWarning")
@pytest.mark.filterwarnings("ignore::dagster.BetaWarning")
def test_happy_path():
    # Given
    stop_it = threading.Event()
    reader = PipesK8sPodLogsMessageReader()
    mock_read = mock.MagicMock()
    mock_list = mock.MagicMock()

    generator = reader._extract_logs(  # noqa: SLF001
        pod_exit_event=stop_it,
        read_namespaced_pod_log=mock_read,
        list_namespaced_pod=mock_list,
        pod_name="foo",
        namespace="default",
        container="bar",
        sleeper=_noop,
        logger=logging.getLogger("test"),
    )
    # Get the first stream
    next(generator)
    stop_it.set()

    with pytest.raises(StopIteration):
        # No more streams created
        next(generator)

    mock_read.assert_called_once_with(
        since_seconds=3600,
        name="foo",
        namespace="default",
        container="bar",
        _preload_content=False,
        timestamps=True,
        follow=True,
    )


@pytest.mark.filterwarnings("ignore::dagster.PreviewWarning")
@pytest.mark.filterwarnings("ignore::dagster.BetaWarning")
def test_unhappy_path():
    # Given
    stop_it = threading.Event()
    reader = PipesK8sPodLogsMessageReader()
    mock_read = mock.MagicMock()
    mock_list = mock.MagicMock()

    generator = reader._extract_logs(  # noqa: SLF001
        pod_exit_event=stop_it,
        read_namespaced_pod_log=mock_read,
        list_namespaced_pod=mock_list,
        pod_name="foo",
        namespace="default",
        container="bar",
        sleeper=_noop,
        logger=logging.getLogger("test"),
    )
    # Get the first stream
    next(generator)
    next(generator)

    stop_it.set()

    with pytest.raises(StopIteration):
        # No more streams created
        next(generator)

    calls = [
        mock.call(
            since_seconds=3600,
            name="foo",
            namespace="default",
            container="bar",
            _preload_content=False,
            timestamps=True,
            follow=True,
        ),
        mock.call().stream(),
        mock.call(
            since_seconds=5,
            name="foo",
            namespace="default",
            container="bar",
            _preload_content=False,
            timestamps=True,
            follow=True,
        ),
        mock.call().stream(),
    ]

    mock_read.assert_has_calls(calls)


@pytest.mark.filterwarnings("ignore::dagster.PreviewWarning")
@pytest.mark.filterwarnings("ignore::dagster.BetaWarning")
def test_happy_path_startup_exception():
    # Given
    stop_it = threading.Event()
    reader = PipesK8sPodLogsMessageReader()
    mock_read = mock.MagicMock(
        side_effect=[kubernetes.client.ApiException("Foo"), mock.MagicMock(), mock.MagicMock()]
    )
    mock_list = mock.MagicMock()

    generator = reader._extract_logs(  # noqa: SLF001
        pod_exit_event=stop_it,
        read_namespaced_pod_log=mock_read,
        list_namespaced_pod=mock_list,
        pod_name="foo",
        namespace="default",
        container="bar",
        sleeper=_noop,
        logger=logging.getLogger("test"),
    )
    # Get the first stream
    next(generator)
    next(generator)

    stop_it.set()

    with pytest.raises(StopIteration):
        # No more streams created
        next(generator)

    calls = [
        mock.call(
            since_seconds=3600,
            name="foo",
            namespace="default",
            container="bar",
            _preload_content=False,
            timestamps=True,
            follow=True,
        ),
        mock.call(
            since_seconds=3600,
            name="foo",
            namespace="default",
            container="bar",
            _preload_content=False,
            timestamps=True,
            follow=True,
        ),
        mock.call(
            since_seconds=5,
            name="foo",
            namespace="default",
            container="bar",
            _preload_content=False,
            timestamps=True,
            follow=True,
        ),
    ]

    mock_read.assert_has_calls(calls)


# Tests for Kube timestamp parsing necessary for proper log ordering
# Docker only logs RFC3339Nano timestamp: https://docs.docker.com/reference/cli/docker/container/logs/
# This is not necessarily true for other runtimes such as containerd, etc
# These tests only target RFC3339Nano timestamp as valid, though others may pass as well


def test_valid_timestamp_with_nanoseconds():
    timestamp = "2024-03-22T02:17:29.185548486Z"
    assert _is_kube_timestamp(timestamp) is True


def test_invalid_timestamp_without_fractional_seconds():
    # Invalid because no nanoseconds
    timestamp = "2024-03-22T02:17:29Z"
    assert _is_kube_timestamp(timestamp) is False


def test_invalid_timestamp_with_bad_date():
    # Invalid date (Feb 30 doesn't exist)
    timestamp = "2024-02-30T02:17:29Z"
    assert _is_kube_timestamp(timestamp) is False


def test_invalid_timestamp_without_z():
    timestamp = "2024-03-22T02:17:29"
    assert _is_kube_timestamp(timestamp) is False
