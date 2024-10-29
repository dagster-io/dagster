import logging
import threading
from unittest import mock

import kubernetes
import pytest
from dagster_k8s.pipes import PipesK8sPodLogsMessageReader, _is_kube_timestamp


def _noop(*args, **kwargs):
    pass


@pytest.mark.filterwarnings("ignore::dagster.ExperimentalWarning")
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


@pytest.mark.filterwarnings("ignore::dagster.ExperimentalWarning")
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


@pytest.mark.filterwarnings("ignore::dagster.ExperimentalWarning")
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
