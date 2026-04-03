"""Unit tests for the multi-task Pipes fix (dagster-io/dagster#33700).

Tests are split into two groups:
  Group A — PipesMessageHandler (dagster core, no Databricks dependency)
  Group B — Databricks-specific classes (pipes.py loaded directly to bypass
             the full dagster_databricks package init chain)
"""

import importlib.util
import json
import sys
import threading
import types
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest

# ---------------------------------------------------------------------------
# Load dagster_databricks.pipes module directly, bypassing __init__.py.
# This avoids the pyspark / dagster_pyspark chain that is not installed in
# pure unit-test environments.
# ---------------------------------------------------------------------------
_PIPES_PY = Path(__file__).parent.parent / "dagster_databricks" / "pipes.py"


# Pre-populate sys.modules with stubs for the databricks SDK which is not
# installed in pure unit-test environments.
def _stub(name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    # Return a MagicMock for any undefined attribute so that type annotations
    # like `jobs.RunState` and `files.FilesAPI` resolve without error.
    mod.__getattr__ = lambda attr: MagicMock()  # type: ignore[method-assign]
    sys.modules[name] = mod
    return mod


for _n in (
    "databricks",
    "databricks.sdk",
    "databricks.sdk.service",
    "databricks.sdk.service.files",
    "databricks.sdk.service.jobs",
):
    if _n not in sys.modules:
        _stub(_n)

# Attach sub-namespaces so attribute access works
sys.modules["databricks"].sdk = sys.modules["databricks.sdk"]  # type: ignore[attr-defined]
sys.modules["databricks.sdk"].service = sys.modules["databricks.sdk.service"]  # type: ignore[attr-defined]
sys.modules["databricks.sdk.service"].files = sys.modules["databricks.sdk.service.files"]  # type: ignore[attr-defined]
sys.modules["databricks.sdk.service"].jobs = sys.modules["databricks.sdk.service.jobs"]  # type: ignore[attr-defined]
sys.modules["databricks.sdk"].WorkspaceClient = MagicMock  # type: ignore[attr-defined]

_PIPES_MODULE_NAME = "dagster_databricks_pipes_module"
_spec = importlib.util.spec_from_file_location(_PIPES_MODULE_NAME, _PIPES_PY)
assert _spec is not None
_db_pipes = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
# Register in sys.modules so patch() can find it by name
sys.modules[_PIPES_MODULE_NAME] = _db_pipes
_spec.loader.exec_module(_db_pipes)  # type: ignore[union-attr]

PipesDatabricksServerlessClient = _db_pipes.PipesDatabricksServerlessClient
PipesUnityCatalogVolumesMessageReader = _db_pipes.PipesUnityCatalogVolumesMessageReader

# ---------------------------------------------------------------------------
# Standard imports (no Databricks dependency)
# ---------------------------------------------------------------------------
from dagster._core.pipes.context import PipesMessageHandler, PipesSession
from dagster._core.pipes.utils import PipesThreadedMessageReader
from dagster_pipes import (
    DAGSTER_PIPES_MESSAGES_ENV_VAR,
    PIPES_PROTOCOL_VERSION,
    PIPES_PROTOCOL_VERSION_FIELD,
    decode_param,
    encode_param,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _closed_message() -> dict[str, Any]:
    return {
        PIPES_PROTOCOL_VERSION_FIELD: PIPES_PROTOCOL_VERSION,
        "method": "closed",
        "params": None,
    }


def _make_handler(expected_closed_messages: int = 1) -> PipesMessageHandler:
    return PipesMessageHandler(
        MagicMock(), MagicMock(), expected_closed_messages=expected_closed_messages
    )


def _log_message(message: str = "hello") -> dict[str, Any]:
    return {
        PIPES_PROTOCOL_VERSION_FIELD: PIPES_PROTOCOL_VERSION,
        "method": "log",
        "params": {"message": message, "level": "info"},
    }


def _closed_with_exception_message() -> dict[str, Any]:
    return {
        PIPES_PROTOCOL_VERSION_FIELD: PIPES_PROTOCOL_VERSION,
        "method": "closed",
        "params": {
            "exception": {
                "message": "boom",
                "stack": ["trace"],
                "name": "ValueError",
                "cause": None,
                "context": None,
            }
        },
    }


class _FakeThreadedReader(PipesThreadedMessageReader):
    def __init__(self, chunks_by_path: dict[str, list[str]]):
        super().__init__(interval=-1)
        self._chunks_by_path = chunks_by_path

    def messages_are_readable(self, params):  # type: ignore[override]
        return True

    @contextmanager
    def get_params(self):
        yield {}

    def download_messages(self, cursor, params):  # type: ignore[override]
        chunks = self._chunks_by_path[params["path"]]
        if not chunks:
            return None

        index = 1 if cursor is None else cursor
        return index + 1, chunks.pop(0)

    def no_messages_debug_text(self) -> str:
        return "fake reader"


# ---------------------------------------------------------------------------
# Group A — PipesMessageHandler: N-closed-message counting
# ---------------------------------------------------------------------------


def test_handler_single_task_closed_on_first_message():
    """Default (1 task): backward compat — session closes after first 'closed'."""
    handler = _make_handler(expected_closed_messages=1)
    assert not handler.received_closed_message
    handler.handle_message(_closed_message())
    assert handler.received_closed_message


def test_handler_multi_task_not_closed_until_all_tasks_close():
    """3 tasks: closed only after receiving 3 'closed' messages."""
    handler = _make_handler(expected_closed_messages=3)
    handler.handle_message(_closed_message())
    assert not handler.received_closed_message
    handler.handle_message(_closed_message())
    assert not handler.received_closed_message
    handler.handle_message(_closed_message())
    assert handler.received_closed_message


def test_handler_closed_count_is_thread_safe():
    """Concurrent 'closed' messages from N threads are counted without data races."""
    n_tasks = 10
    handler = _make_handler(expected_closed_messages=n_tasks)
    barrier = threading.Barrier(n_tasks)

    def send_closed():
        barrier.wait()  # maximise contention
        handler.handle_message(_closed_message())

    threads = [threading.Thread(target=send_closed) for _ in range(n_tasks)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert handler.received_closed_message
    assert handler._received_closed_count == n_tasks  # noqa: SLF001


def test_handler_emits_close_exception_before_marking_closed():
    """The final close exception should be emitted before the session is marked closed."""
    handler = _make_handler(expected_closed_messages=1)
    observed_closed_state: list[bool] = []

    with patch(
        "dagster._core.pipes.context.DagsterEvent.engine_event",
        side_effect=lambda *_args, **_kwargs: observed_closed_state.append(
            handler.received_closed_message
        ),
    ):
        handler.handle_message(_closed_with_exception_message())

    assert observed_closed_state == [False]
    assert handler.received_closed_message


def test_messages_thread_uses_task_closed_event_instead_of_global_closed_flag():
    """A multi-task reader thread should keep draining until its own task closes."""
    chunk = "\n".join(
        [
            json.dumps(_log_message()),
        ]
    )
    reader = _FakeThreadedReader({"/task_1": [chunk]})
    handler = MagicMock()
    handler.received_closed_message = True
    task_closed = threading.Event()
    is_session_closed = threading.Event()
    is_session_closed.set()

    with (
        patch("dagster._core.pipes.utils.WAIT_FOR_LOGS_AFTER_EXECUTION_INTERVAL", -1),
        patch("dagster._core.pipes.utils.time.sleep", return_value=None),
    ):
        reader._messages_thread(  # noqa: SLF001
            handler, {"path": "/task_1"}, is_session_closed, task_closed
        )

    handler.handle_message.assert_called_once()


# ---------------------------------------------------------------------------
# Group B — Databricks: per-task path injection
# ---------------------------------------------------------------------------


def _make_session(base_path: str) -> MagicMock:
    session = MagicMock(spec=PipesSession)
    session.message_reader_params = {"path": base_path}
    session.context_injector_params = {"path": f"{base_path}/context.json"}
    session.get_bootstrap_env_vars.return_value = {
        DAGSTER_PIPES_MESSAGES_ENV_VAR: encode_param({"path": base_path}),
    }
    session.get_bootstrap_cli_arguments.return_value = {}
    session.default_remote_invocation_info = {}
    return session


def _make_serverless_client() -> Any:
    return PipesDatabricksServerlessClient.__new__(PipesDatabricksServerlessClient)


def test_enrich_task_dict_injects_per_task_path_notebook():
    """Each task's notebook_task params must point to its own task_{i} subdirectory."""
    client = _make_serverless_client()
    session = _make_session("/Volumes/base/tmp/ABC")

    for i in range(3):
        task_dict: dict[str, Any] = {"notebook_task": {"base_parameters": {}}}
        result = client._enrich_submit_task_dict(  # noqa: SLF001
            context=MagicMock(), session=session, submit_task_dict=task_dict, task_index=i
        )
        injected = decode_param(
            result["notebook_task"]["base_parameters"][DAGSTER_PIPES_MESSAGES_ENV_VAR]
        )
        assert injected["path"] == f"/Volumes/base/tmp/ABC/task_{i}"


def test_enrich_task_dict_without_task_index_uses_shared_path():
    """task_index=None (single-task) leaves the shared base path unchanged."""
    client = _make_serverless_client()
    session = _make_session("/Volumes/base/tmp/ABC")

    task_dict: dict[str, Any] = {"notebook_task": {"base_parameters": {}}}
    result = client._enrich_submit_task_dict(  # noqa: SLF001
        context=MagicMock(), session=session, submit_task_dict=task_dict, task_index=None
    )
    injected = decode_param(
        result["notebook_task"]["base_parameters"][DAGSTER_PIPES_MESSAGES_ENV_VAR]
    )
    assert injected["path"] == "/Volumes/base/tmp/ABC"


def test_enrich_task_dict_all_paths_unique():
    """No two tasks must receive the same message directory path."""
    client = _make_serverless_client()
    session = _make_session("/Volumes/base")
    paths: set[str] = set()

    for i in range(5):
        task_dict: dict[str, Any] = {"notebook_task": {"base_parameters": {}}}
        result = client._enrich_submit_task_dict(  # noqa: SLF001
            context=MagicMock(), session=session, submit_task_dict=task_dict, task_index=i
        )
        path = decode_param(
            result["notebook_task"]["base_parameters"][DAGSTER_PIPES_MESSAGES_ENV_VAR]
        )["path"]
        assert path not in paths, f"Duplicate path: {path}"
        paths.add(path)


# ---------------------------------------------------------------------------
# Group B — Databricks: PipesUnityCatalogVolumesMessageReader
# ---------------------------------------------------------------------------


def _make_reader(num_tasks: int) -> Any:
    reader = PipesUnityCatalogVolumesMessageReader.__new__(PipesUnityCatalogVolumesMessageReader)
    reader.num_tasks = num_tasks
    reader.include_stdio_in_messages = True
    reader.volume_path = "/Volumes/test"
    reader.files_client = MagicMock()
    reader.interval = 10
    reader.log_readers = {}
    reader.opened_payload = None
    reader.launched_payload = None
    reader.counter = 1
    return reader


def test_reader_get_params_creates_task_subdirs():
    """get_params() creates task_{i} subdirectories and returns their paths when num_tasks > 1."""
    reader = _make_reader(num_tasks=3)
    base_path = "/Volumes/test/tmp/XYZ"

    @contextmanager
    def fake_volumes_tempdir(files_client, volume_path):
        yield base_path

    with patch(f"{_db_pipes.__name__}.volumes_tempdir", fake_volumes_tempdir):
        with reader.get_params() as params:
            assert params["path"] == base_path
            assert params["task_paths"] == [
                f"{base_path}/task_0",
                f"{base_path}/task_1",
                f"{base_path}/task_2",
            ]
            reader.files_client.create_directory.assert_has_calls(
                [
                    call(f"{base_path}/task_0"),
                    call(f"{base_path}/task_1"),
                    call(f"{base_path}/task_2"),
                ],
                any_order=False,
            )


def test_reader_get_params_no_task_paths_for_single_task():
    """Single-task path: task_paths key must NOT be added (backward compat)."""
    reader = _make_reader(num_tasks=1)

    @contextmanager
    def fake_volumes_tempdir(files_client, volume_path):
        yield "/Volumes/test/tmp/SINGLE"

    with patch(f"{_db_pipes.__name__}.volumes_tempdir", fake_volumes_tempdir):
        with reader.get_params() as params:
            assert "task_paths" not in params


def test_reader_read_messages_skips_log_threads_without_log_readers():
    """read_messages() starts only message threads when no log readers are configured."""
    reader = _make_reader(num_tasks=3)
    base_path = "/Volumes/test/tmp/MT"
    task_paths = [f"{base_path}/task_{i}" for i in range(3)]

    handler = MagicMock()
    handler.received_closed_message = True  # threads exit immediately

    @contextmanager
    def fake_volumes_tempdir(files_client, volume_path):
        yield base_path

    with (
        patch(f"{_db_pipes.__name__}.volumes_tempdir", fake_volumes_tempdir),
        patch.object(reader, "_messages_thread", side_effect=lambda *a, **kw: None) as mock_msg,
        patch.object(reader, "_logs_thread", side_effect=lambda *a, **kw: None) as mock_log,
        patch(f"{_db_pipes.__name__}._join_thread"),
    ):
        with reader.read_messages(handler):
            pass

    assert mock_msg.call_count == 3
    assert mock_log.call_count == 0

    # Each call used a distinct task path
    msg_paths = {
        c.args[1]["path"] if c.args else c.kwargs["params"]["path"] for c in mock_msg.call_args_list
    }
    assert msg_paths == set(task_paths)


def test_reader_read_messages_spawns_log_threads_when_log_readers_exist():
    """read_messages() starts per-task log threads when log readers are configured."""
    reader = _make_reader(num_tasks=3)
    reader.log_readers = {"0": MagicMock()}
    base_path = "/Volumes/test/tmp/MT"

    handler = MagicMock()
    handler.received_closed_message = True

    @contextmanager
    def fake_volumes_tempdir(files_client, volume_path):
        yield base_path

    with (
        patch(f"{_db_pipes.__name__}.volumes_tempdir", fake_volumes_tempdir),
        patch.object(reader, "_messages_thread", side_effect=lambda *a, **kw: None) as mock_msg,
        patch.object(reader, "_logs_thread", side_effect=lambda *a, **kw: None) as mock_log,
        patch(f"{_db_pipes.__name__}._join_thread"),
    ):
        with reader.read_messages(handler):
            pass

    assert mock_msg.call_count == 3
    assert mock_log.call_count == 3


def test_reader_download_messages_uses_cursor_not_shared_counter():
    """download_messages() must use the cursor arg, not self.counter.

    This keeps concurrent per-task reader threads from sharing state and skipping chunks.
    """
    reader = _make_reader(num_tasks=3)
    reader.counter = 99  # would cause skipped chunks if used instead of cursor

    chunk_data = '{"method": "log"}'
    reader.download_messages_chunk = MagicMock(return_value=chunk_data)

    # Start at cursor=1 (first chunk)
    result = reader.download_messages(1, {"path": "/task_0"})
    assert result is not None
    new_cursor, _chunk = result
    assert new_cursor == 2  # advanced by 1, not based on self.counter
    reader.download_messages_chunk.assert_called_once_with(1, {"path": "/task_0"})

    # Simulate a second independent thread starting fresh at cursor=None (defaults to 1)
    result2 = reader.download_messages(None, {"path": "/task_1"})
    assert result2 is not None
    assert result2[0] == 2  # also starts at 1, independent of task_0's cursor

    # self.counter must remain unchanged
    assert reader.counter == 99


def test_run_multi_task_allows_unity_catalog_reader_for_multi_task():
    """run_multi_task() must accept a custom Unity Catalog reader and update num_tasks."""
    client = PipesDatabricksServerlessClient.__new__(PipesDatabricksServerlessClient)
    client.message_reader = PipesUnityCatalogVolumesMessageReader.__new__(
        PipesUnityCatalogVolumesMessageReader
    )
    client.message_reader.num_tasks = 1
    client.context_injector = None
    client.client = MagicMock()
    client.volume_path = "/Volumes/test"
    client.forward_termination = True
    client._poll_til_success = MagicMock()
    client._extract_dagster_metadata = MagicMock(return_value={})
    client._enrich_submit_task_dict = MagicMock(side_effect=lambda **kwargs: kwargs["submit_task_dict"])

    task1 = MagicMock()
    task2 = MagicMock()
    task1.as_dict.return_value = {"task_key": "task1"}
    task2.as_dict.return_value = {"task_key": "task2"}
    pipes_session = MagicMock()

    @contextmanager
    def fake_open_pipes_session(**kwargs):
        assert kwargs["message_reader"] is client.message_reader
        assert kwargs["expected_closed_messages"] == 2
        yield pipes_session

    with (
        patch(f"{_db_pipes.__name__}.open_pipes_session", fake_open_pipes_session),
        patch.object(_db_pipes.jobs.SubmitTask, "from_dict", side_effect=lambda task_dict: task_dict),
    ):
        client.run_multi_task(
            context=MagicMock(),
            tasks=[task1, task2],
        )

    assert client.message_reader.num_tasks == 2


def test_run_multi_task_allows_non_unity_catalog_custom_reader_for_single_task():
    """run_multi_task() must preserve single-task support for arbitrary custom readers."""
    client = PipesDatabricksServerlessClient.__new__(PipesDatabricksServerlessClient)
    client.message_reader = MagicMock()
    client.context_injector = None
    client.client = MagicMock()
    client.volume_path = "/Volumes/test"
    client.forward_termination = True
    client._poll_til_success = MagicMock()
    client._extract_dagster_metadata = MagicMock(return_value={})
    client._enrich_submit_task_dict = MagicMock(side_effect=lambda **kwargs: kwargs["submit_task_dict"])

    task = MagicMock()
    task.as_dict.return_value = {"task_key": "task1"}
    pipes_session = MagicMock()

    @contextmanager
    def fake_open_pipes_session(**kwargs):
        assert kwargs["message_reader"] is client.message_reader
        assert kwargs["expected_closed_messages"] == 1
        yield pipes_session

    with (
        patch(f"{_db_pipes.__name__}.open_pipes_session", fake_open_pipes_session),
        patch.object(_db_pipes.jobs.SubmitTask, "from_dict", side_effect=lambda task_dict: task_dict),
    ):
        client.run_multi_task(
            context=MagicMock(),
            tasks=[task],
        )


def test_run_multi_task_rejects_non_unity_catalog_custom_reader_for_multi_task():
    """run_multi_task() must still reject arbitrary custom readers for multi-task runs."""
    client = PipesDatabricksServerlessClient.__new__(PipesDatabricksServerlessClient)
    client.message_reader = MagicMock()
    client.context_injector = None
    client.client = MagicMock()
    client.volume_path = "/Volumes/test"

    task1 = MagicMock()
    task2 = MagicMock()

    with pytest.raises(ValueError, match="custom message_reader is not supported"):
        client.run_multi_task(
            context=MagicMock(),
            tasks=[task1, task2],
        )
