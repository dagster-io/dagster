"""Worker lifetime policy and its event transport; no external services required."""

import json
import multiprocessing
import os
import queue
import threading
import time
from pathlib import Path

import pytest
from dagster._config import process_config
from dagster._core.definitions.executor_definition import (
    MULTI_PROC_CONFIG,
    _core_multiprocess_executor_creation,
)
from dagster._core.executor._deadline_spool import AtomicEventSpool, EventTransportError
from dagster._core.executor.child_process_executor import (
    ChildProcessCommand,
    ChildProcessDeadlineExceeded,
    ChildProcessStartEvent,
    ChildProcessSystemErrorEvent,
    execute_child_process_with_deadline,
)
from dagster._utils.error import SerializableErrorInfo


def executor_from_config(config):
    result = process_config(MULTI_PROC_CONFIG.config_type, config)
    if not result.success:
        raise ValueError(str(result.errors))
    assert result.value is not None
    return _core_multiprocess_executor_creation(result.value)


def test_default_and_enabled_configuration():
    # Inspect wiring directly without adding test-only public executor properties.
    assert executor_from_config({})._step_worker_timeout_seconds is None  # noqa: SLF001
    enabled = executor_from_config({"step_worker_timeout_seconds": 120})
    assert enabled._step_worker_timeout_seconds == 120  # noqa: SLF001
    assert enabled._step_worker_timeout_max_event_bytes == 32 * 1024 * 1024  # noqa: SLF001
    small = executor_from_config(
        {"step_worker_timeout_seconds": 0.5, "step_worker_timeout_max_event_bytes": 64}
    )
    assert small._step_worker_timeout_max_event_bytes == 64  # noqa: SLF001


@pytest.mark.parametrize("timeout", [0, -1, True, float("nan"), float("inf"), 10**1000])
def test_invalid_timeout_configuration(timeout):
    with pytest.raises((ValueError, TypeError)):
        executor_from_config({"step_worker_timeout_seconds": timeout})


@pytest.mark.parametrize("cap", [0, -1, True, 1.5])
def test_invalid_cap_configuration(cap):
    with pytest.raises((ValueError, TypeError)):
        executor_from_config(
            {"step_worker_timeout_seconds": 10, "step_worker_timeout_max_event_bytes": cap}
        )


def test_cap_requires_timeout():
    with pytest.raises(ValueError, match="requires"):
        executor_from_config({"step_worker_timeout_max_event_bytes": 128})


def test_capacity_is_reused_without_lifetime_limit(tmp_path):
    spool = AtomicEventSpool(str(tmp_path), 100_000)
    for _ in range(10_001):
        spool.put(ChildProcessStartEvent(os.getpid()))
        assert spool.get_nowait().pid == os.getpid()
    large = ChildProcessSystemErrorEvent(os.getpid(), SerializableErrorInfo("x" * 65_536, [], None))
    for _ in range(513):  # More than the old 32 MiB lifetime byte ceiling.
        spool.put(large)
        assert spool.get_nowait() == large
    assert not list(tmp_path.iterdir())


def test_capacity_backpressure_releases_after_consumption(tmp_path, monkeypatch):
    import dagster._core.executor._deadline_spool as module

    monkeypatch.setattr(module, "MAX_PENDING_FRAMES", 1)
    spool = AtomicEventSpool(str(tmp_path), 1024)
    spool.put(ChildProcessStartEvent(1))
    finished = threading.Event()
    errors = []

    def publish():
        try:
            spool.put(ChildProcessStartEvent(2))
        except Exception as exc:
            errors.append(exc)
        finally:
            finished.set()

    worker = threading.Thread(target=publish)
    worker.start()
    try:
        assert not finished.wait(0.05)
        assert spool.get_nowait().pid == 1
        assert finished.wait(2)
        assert spool.get_nowait().pid == 2
        assert not errors
    finally:
        if not finished.is_set():
            try:
                spool.get_nowait()
            except queue.Empty:
                pass
        worker.join(timeout=2)
    assert not worker.is_alive()


def test_oversize_rejected_before_frame_creation(tmp_path):
    spool = AtomicEventSpool(str(tmp_path), 1)
    with pytest.raises(EventTransportError, match="event_size_limit"):
        spool.put(ChildProcessStartEvent(1))
    assert not list(tmp_path.glob("*.ready"))
    assert not list(tmp_path.glob("[0-9]*.partial"))


def test_malformed_frame_is_transport_error(tmp_path):
    (tmp_path / "00000000.ready").write_bytes(b"{invalid")
    with pytest.raises(EventTransportError, match="Invalid worker event frame"):
        AtomicEventSpool(str(tmp_path)).get_nowait()


class StuckBeforeStepStart(ChildProcessCommand):
    def execute(self):
        while True:
            time.sleep(0.01)
        yield  # A real child command that never emits STEP_START.


class OversizeWithoutMarker(ChildProcessCommand):
    def execute(self):
        original = Path.write_text

        def deny_marker(path, *args, **kwargs):
            if path.name == "transport-error.partial":
                raise OSError("synthetic full disk for diagnostic marker")
            return original(path, *args, **kwargs)

        Path.write_text = deny_marker
        yield ChildProcessSystemErrorEvent(os.getpid(), SerializableErrorInfo("x" * 4096, [], None))


def collect_worker(command, tmp_path, seconds=3, cap=1024):
    processes = []
    try:
        processes.extend(
            item
            for item in execute_child_process_with_deadline(
                multiprocessing.get_context("spawn"),
                command,
                seconds,
                str(tmp_path),
                lambda: False,
                cap,
            )
            if isinstance(item, multiprocessing.process.BaseProcess)
        )
    finally:
        for process in processes:
            assert not process.is_alive()
            assert process.exitcode is not None
        assert not list(tmp_path.glob("attempt-*"))
    return processes


def test_deadline_is_armed_before_step_start(tmp_path):
    with pytest.raises(ChildProcessDeadlineExceeded, match="worker lifetime exceeded 3 seconds"):
        collect_worker(StuckBeforeStepStart(), tmp_path)


def test_transport_failure_without_diagnostic_marker_is_not_timeout(tmp_path):
    with pytest.raises(EventTransportError):
        collect_worker(OversizeWithoutMarker(), tmp_path, seconds=10)


import dagster as dg


@dg.resource
def retry_after_stuck_initialization(context):
    root = Path(context.instance.storage_directory())
    marker = root / "initializing-worker"
    if not marker.exists():
        marker.write_text(str(os.getpid()))
        while True:
            time.sleep(0.01)
    old_pid = int(marker.read_text())
    try:
        os.kill(old_pid, 0)
    except ProcessLookupError:
        (root / "previous-worker-gone").write_text(str(old_pid))
    else:
        raise AssertionError("Retry began before old worker exited")
    return 1


@dg.op(required_resource_keys={"stuck"}, retry_policy=dg.RetryPolicy(max_retries=1))
def use_initialized_resource(context):
    return context.resources.stuck


@dg.job(resource_defs={"stuck": retry_after_stuck_initialization})
def resource_initialization_deadline_job():
    use_initialized_resource()


def test_actual_resource_initialization_timeout_retries_after_exit(tmp_path):
    with dg.instance_for_test(
        temp_dir=str(tmp_path),
        overrides={
            "telemetry": {"enabled": False},
            "compute_logs": {
                "module": "dagster._core.storage.noop_compute_log_manager",
                "class": "NoOpComputeLogManager",
            },
        },
    ) as instance:
        result = dg.execute_job(
            dg.reconstructable(resource_initialization_deadline_job),
            instance=instance,
            run_config={
                "execution": {
                    "config": {
                        "multiprocess": {
                            "max_concurrent": 2,
                            "start_method": {"spawn": {}},
                            "step_worker_timeout_seconds": 8,
                        }
                    }
                }
            },
            raise_on_error=False,
        )
        assert result.success
        assert (Path(instance.storage_directory()) / "previous-worker-gone").exists()
        types = [event.event_type_value for event in result.all_events]
        assert types.count("STEP_UP_FOR_RETRY") == 1
        assert types.count("STEP_RESTARTED") == 1
        assert not list(Path(instance.storage_directory()).glob("attempt-*"))


def pause_real_event(context, event_type):
    """Test-only stall after the actual event is committed, before transport publication."""
    import signal

    original = AtomicEventSpool._put  # noqa: SLF001 - deliberate real transport fault injection
    root = Path(context.instance.storage_directory())

    def paused(spool, event):
        if getattr(event, "event_type_value", None) == event_type:
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            (root / "paused-event").write_text(str(os.getpid()))
            while True:
                time.sleep(0.01)
        return original(spool, event)

    pytest.MonkeyPatch().setattr(AtomicEventSpool, "_put", paused)
    return 1


@dg.resource
def pause_start(context):
    return pause_real_event(context, "STEP_START")


@dg.resource
def pause_success(context):
    return pause_real_event(context, "STEP_SUCCESS")


@dg.resource
def pause_retry(context):
    return pause_real_event(context, "STEP_UP_FOR_RETRY")


@dg.op(required_resource_keys={"pause"})
def produce_value(context):
    return context.resources.pause


@dg.op(required_resource_keys={"pause"}, retry_policy=dg.RetryPolicy(max_retries=1))
def request_retry(context):
    raise dg.RetryRequested(max_retries=1)


@dg.job(resource_defs={"pause": pause_start})
def start_publication_job():
    produce_value()


@dg.job(resource_defs={"pause": pause_success})
def success_publication_job():
    produce_value()


@dg.job(resource_defs={"pause": pause_retry})
def cancel_committed_retry_job():
    request_retry()


def run_lifetime_job(job, instance, *, timeout=8, cap=None, start_method="spawn"):
    config = {
        "max_concurrent": 2,
        "start_method": {start_method: {}},
        "step_worker_timeout_seconds": timeout,
    }
    if cap is not None:
        config["step_worker_timeout_max_event_bytes"] = cap
    return dg.execute_job(
        dg.reconstructable(job),
        instance=instance,
        run_config={"execution": {"config": {"multiprocess": config}}},
        raise_on_error=False,
    )


def assert_paused_worker_gone(instance):
    root = Path(instance.storage_directory())
    pid = int((root / "paused-event").read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)
    assert not list(root.glob("attempt-*"))


def test_real_blocked_start_publication_expires(tmp_path):
    with dg.instance_for_test(
        temp_dir=str(tmp_path),
        overrides={
            "compute_logs": {
                "module": "dagster._core.storage.noop_compute_log_manager",
                "class": "NoOpComputeLogManager",
            }
        },
    ) as instance:
        result = run_lifetime_job(start_publication_job, instance)
        assert not result.success
        stored = [
            e.dagster_event.event_type_value
            for e in instance.all_logs(result.run_id)
            if e.dagster_event
        ]
        assert stored.count("STEP_START") == 1
        assert stored.count("STEP_FAILURE") == 1
        messages = [entry.message for entry in instance.all_logs(result.run_id)]
        assert any("configured worker lifetime of 8 seconds" in message for message in messages)
        assert not any("out of memory" in message for message in messages)
        assert_paused_worker_gone(instance)


def test_real_committed_success_survives_worker_deadline(tmp_path):
    with dg.instance_for_test(
        temp_dir=str(tmp_path),
        overrides={
            "compute_logs": {
                "module": "dagster._core.storage.noop_compute_log_manager",
                "class": "NoOpComputeLogManager",
            }
        },
    ) as instance:
        result = run_lifetime_job(success_publication_job, instance)
        assert result.success
        stored = [
            e.dagster_event.event_type_value
            for e in instance.all_logs(result.run_id)
            if e.dagster_event
        ]
        assert stored.count("STEP_SUCCESS") == 1
        assert "STEP_FAILURE" not in stored and "STEP_UP_FOR_RETRY" not in stored
        assert_paused_worker_gone(instance)


def test_real_committed_retry_cancellation_prevents_new_worker(tmp_path):
    import signal

    with dg.instance_for_test(
        temp_dir=str(tmp_path),
        overrides={
            "compute_logs": {
                "module": "dagster._core.storage.noop_compute_log_manager",
                "class": "NoOpComputeLogManager",
            }
        },
    ) as instance:
        errors = []
        finished = threading.Event()

        def cancel():
            try:
                marker = Path(instance.storage_directory()) / "paused-event"
                until = time.monotonic() + 15
                while not finished.is_set() and not marker.exists() and time.monotonic() < until:
                    time.sleep(0.01)
                if finished.is_set():
                    return
                assert marker.exists()
                runs = instance.get_runs()
                assert len(runs) == 1
                logs = instance.all_logs(runs[0].run_id)
                assert (
                    sum(
                        bool(e.dagster_event and e.dagster_event.is_step_up_for_retry) for e in logs
                    )
                    == 1
                )
                if finished.is_set():
                    return
                instance.report_run_canceling(runs[0])
                if not finished.is_set():
                    os.kill(os.getpid(), signal.SIGINT)
            except Exception as exc:
                errors.append(exc)

        thread = threading.Thread(target=cancel)
        thread.start()
        try:
            result = run_lifetime_job(cancel_committed_retry_job, instance, timeout=20)
        finally:
            finished.set()
            thread.join(timeout=16)
        assert not thread.is_alive() and not errors
        assert not result.success
        stored = [
            e.dagster_event.event_type_value
            for e in instance.all_logs(result.run_id)
            if e.dagster_event
        ]
        assert stored.count("STEP_UP_FOR_RETRY") == 1
        assert stored.count("STEP_WORKER_STARTING") == 1
        assert "STEP_RESTARTED" not in stored and "PIPELINE_CANCELED" in stored
        assert_paused_worker_gone(instance)


@dg.op
def default_value():
    return 1


@dg.job
def default_queue_job():
    default_value()


def test_actual_default_queue_job_remains_successful(tmp_path):
    with dg.instance_for_test(
        temp_dir=str(tmp_path),
        overrides={
            "compute_logs": {
                "module": "dagster._core.storage.noop_compute_log_manager",
                "class": "NoOpComputeLogManager",
            }
        },
    ) as instance:
        result = dg.execute_job(
            dg.reconstructable(default_queue_job), instance=instance, raise_on_error=False
        )
        assert result.success
        assert not list(Path(instance.storage_directory()).glob("attempt-*"))


def test_actual_tiny_cap_is_nonretryable_transport_error(tmp_path):
    with dg.instance_for_test(
        temp_dir=str(tmp_path),
        overrides={
            "compute_logs": {
                "module": "dagster._core.storage.noop_compute_log_manager",
                "class": "NoOpComputeLogManager",
            }
        },
    ) as instance:
        result = run_lifetime_job(cancel_committed_retry_job, instance, cap=1)
        assert not result.success
        stored = [
            e.dagster_event.event_type_value
            for e in instance.all_logs(result.run_id)
            if e.dagster_event
        ]
        errors = [
            str(e.dagster_event.event_specific_data)
            for e in instance.all_logs(result.run_id)
            if e.dagster_event
        ]
        assert any(
            "EventTransportError" in text and "step_worker_timeout_max_event_bytes=1" in text
            for text in errors
        )
        assert "STEP_UP_FOR_RETRY" not in stored
        assert stored.count("STEP_WORKER_STARTING") == 1
        assert not list(Path(instance.storage_directory()).glob("attempt-*"))


class OversizeWithStuckCleanup(ChildProcessCommand):
    def execute(self):
        import signal

        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        try:
            yield ChildProcessSystemErrorEvent(
                os.getpid(), SerializableErrorInfo("x" * 4096, [], None)
            )
        finally:
            while True:
                time.sleep(0.01)


def test_transport_marker_wins_over_deadline_during_cleanup(tmp_path):
    with pytest.raises(EventTransportError, match="event exceeds"):
        collect_worker(OversizeWithStuckCleanup(), tmp_path, seconds=5)


@pytest.mark.skipif(
    "forkserver" not in multiprocessing.get_all_start_methods(), reason="forkserver unavailable"
)
def test_forkserver_resource_timeout_retry(tmp_path):
    with dg.instance_for_test(
        temp_dir=str(tmp_path),
        overrides={
            "compute_logs": {
                "module": "dagster._core.storage.noop_compute_log_manager",
                "class": "NoOpComputeLogManager",
            }
        },
    ) as instance:
        result = run_lifetime_job(
            resource_initialization_deadline_job, instance, start_method="forkserver"
        )
        assert result.success
        assert (Path(instance.storage_directory()) / "previous-worker-gone").exists()
        assert sum(e.event_type_value == "STEP_UP_FOR_RETRY" for e in result.all_events) == 1
        assert not list(Path(instance.storage_directory()).glob("attempt-*"))


@pytest.mark.skipif(
    "forkserver" not in multiprocessing.get_all_start_methods(), reason="forkserver unavailable"
)
def test_forkserver_default_queue_control(tmp_path):
    with dg.instance_for_test(
        temp_dir=str(tmp_path),
        overrides={
            "compute_logs": {
                "module": "dagster._core.storage.noop_compute_log_manager",
                "class": "NoOpComputeLogManager",
            }
        },
    ) as instance:
        result = dg.execute_job(
            dg.reconstructable(default_queue_job),
            instance=instance,
            run_config={
                "execution": {
                    "config": {
                        "multiprocess": {"max_concurrent": 2, "start_method": {"forkserver": {}}}
                    }
                }
            },
            raise_on_error=False,
        )
        assert result.success


class MissingMarkerWithStuckCleanup(ChildProcessCommand):
    def __init__(self, root):
        self.root = root

    def execute(self):
        import signal

        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        original = Path.write_text

        def deny_marker(path, *args, **kwargs):
            if path.name == "transport-error.partial":
                raise OSError("synthetic full disk for transport marker")
            return original(path, *args, **kwargs)

        Path.write_text = deny_marker
        try:
            yield ChildProcessSystemErrorEvent(
                os.getpid(), SerializableErrorInfo("x" * 4096, [], None)
            )
        finally:
            (Path(self.root) / "cleanup-entered").write_text(str(os.getpid()))
            while True:
                time.sleep(0.01)


def test_combined_failure_exits_before_user_cleanup(tmp_path):
    with pytest.raises(EventTransportError):
        collect_worker(MissingMarkerWithStuckCleanup(str(tmp_path)), tmp_path, seconds=4)
    assert not (tmp_path / "cleanup-entered").exists()


class FullCapacityCommand(ChildProcessCommand):
    def __init__(self, root):
        self.root = root

    def execute(self):
        import sys

        import dagster._core.executor._deadline_spool as module

        pytest.MonkeyPatch().setattr(module, "MAX_PENDING_FRAMES", 1)
        original = AtomicEventSpool._wait_for_capacity  # noqa: SLF001

        def observe(spool, size):
            ready = list(Path(spool.directory).glob("*.ready"))
            if ready:
                (Path(self.root) / "capacity-wait-observed").write_text(
                    json.dumps(
                        {
                            "pid": os.getpid(),
                            "no_site": sys.flags.no_site,
                            "isolated": sys.flags.isolated,
                            "dont_write_bytecode": sys.dont_write_bytecode,
                            "home_present": "HOME" in os.environ,
                        }
                    )
                )
            return original(spool, size)

        pytest.MonkeyPatch().setattr(AtomicEventSpool, "_wait_for_capacity", observe)
        while True:
            yield ChildProcessStartEvent(os.getpid())


def test_capacity_writer_is_killable_at_lifetime_limit(tmp_path, monkeypatch):
    original_read = AtomicEventSpool.get_nowait

    def pause_reader(spool):
        if (tmp_path / "capacity-wait-observed").exists():
            if list(Path(spool.directory).glob("*.ready")):
                (tmp_path / "parent-observed-full").write_text("reader paused with retained frame")
            raise queue.Empty
        return original_read(spool)

    monkeypatch.setattr(AtomicEventSpool, "get_nowait", pause_reader)
    with pytest.raises(ChildProcessDeadlineExceeded):
        collect_worker(FullCapacityCommand(str(tmp_path)), tmp_path, seconds=4)
    assert (tmp_path / "parent-observed-full").exists()
    pid = json.loads((tmp_path / "capacity-wait-observed").read_text())["pid"]
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


class UserReservedExit(ChildProcessCommand):
    def execute(self):
        os._exit(73)


def test_reserved_exit_is_conservatively_nonretryable(tmp_path):
    with pytest.raises(EventTransportError):
        collect_worker(UserReservedExit(), tmp_path, seconds=5)


@dg.op
def independent_noncooperative(context):
    import signal

    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    (Path(context.instance.storage_directory()) / "independent-pid").write_text(str(os.getpid()))
    while True:
        time.sleep(0.01)


@dg.op
def fail_transport_after_independent_starts(context):
    marker = Path(context.instance.storage_directory()) / "independent-pid"
    until = time.monotonic() + 10
    while not marker.exists() and time.monotonic() < until:
        time.sleep(0.01)
    assert marker.exists()
    yield dg.AssetMaterialization(
        asset_key="oversize_after_peer_starts", metadata={"payload": "x" * 65_536}
    )


@dg.job
def fatal_transport_with_live_peer_job():
    independent_noncooperative()
    fail_transport_after_independent_starts()


def test_fatal_transport_reaps_other_active_worker(tmp_path):
    import signal

    with dg.instance_for_test(
        temp_dir=str(tmp_path),
        overrides={
            "compute_logs": {
                "module": "dagster._core.storage.noop_compute_log_manager",
                "class": "NoOpComputeLogManager",
            }
        },
    ) as instance:
        pid = None
        try:
            # ExceptionInfo deliberately keeps the original traceback/active iterators alive.
            with pytest.raises(EventTransportError) as retained_error:
                dg.execute_job(
                    dg.reconstructable(fatal_transport_with_live_peer_job),
                    instance=instance,
                    run_config={
                        "execution": {
                            "config": {
                                "multiprocess": {
                                    "max_concurrent": 2,
                                    "start_method": {"spawn": {}},
                                    "step_worker_timeout_seconds": 30,
                                    "step_worker_timeout_max_event_bytes": 8192,
                                }
                            }
                        }
                    },
                    raise_on_error=True,
                )
            assert "event exceeds" in str(retained_error.value)
            pid = int((Path(instance.storage_directory()) / "independent-pid").read_text())
            alive = True
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                alive = False
            (tmp_path / "product-cleanup-observation.json").write_text(
                json.dumps({"pid": pid, "alive_after_transport_error": alive})
            )
            assert not alive
            assert not list(Path(instance.storage_directory()).glob("attempt-*"))
        finally:
            marker = Path(instance.storage_directory()) / "independent-pid"
            if pid is None and marker.exists():
                pid = int(marker.read_text())
            if pid is not None:
                for process in multiprocessing.active_children():
                    if process.pid == pid and process.is_alive():
                        # Bounded fixture rescue is explicitly separate from product cleanup.
                        (tmp_path / "fixture-rescue.json").write_text(json.dumps({"pid": pid}))
                        os.kill(pid, signal.SIGKILL)
                        process.join(timeout=2)
                        assert not process.is_alive()


def test_cleanup_attempts_every_iterator_after_failure():
    from dagster._core.executor.multiprocess import _close_step_iterators

    closed = []

    def first():
        try:
            yield None
        finally:
            closed.append("first")
            raise RuntimeError("synthetic cleanup failure")

    def second():
        try:
            yield None
        finally:
            closed.append("second")

    one, two = first(), second()
    next(one)
    next(two)
    failures = _close_step_iterators([one, two])
    assert closed == ["first", "second"]
    assert len(failures) == 1 and str(failures[0]) == "synthetic cleanup failure"


def test_consumer_close_reaps_actual_live_worker(tmp_path):
    iterator = execute_child_process_with_deadline(
        multiprocessing.get_context("spawn"),
        StuckBeforeStepStart(),
        20,
        str(tmp_path),
        lambda: False,
        1024,
    )
    process = next(iterator)
    assert isinstance(process, multiprocessing.process.BaseProcess)
    try:
        until = time.monotonic() + 5
        for item in iterator:
            if isinstance(item, ChildProcessStartEvent):
                break
            assert time.monotonic() < until
        assert process.is_alive()
        iterator.close()
        assert not process.is_alive() and process.exitcode < 0
        assert not list(tmp_path.glob("attempt-*"))
    finally:
        iterator.close()


@dg.job
def close_active_worker_job():
    independent_noncooperative()


def test_run_iterator_close_reaps_active_worker(tmp_path):
    from types import GeneratorType

    from dagster._core.execution.api import execute_run_iterator

    with dg.instance_for_test(
        temp_dir=str(tmp_path),
        overrides={
            "compute_logs": {
                "module": "dagster._core.storage.noop_compute_log_manager",
                "class": "NoOpComputeLogManager",
            }
        },
    ) as instance:
        config = {
            "execution": {
                "config": {
                    "multiprocess": {
                        "max_concurrent": 2,
                        "start_method": {"spawn": {}},
                        "step_worker_timeout_seconds": 30,
                    }
                }
            }
        }
        run = instance.create_run_for_job(close_active_worker_job, run_config=config)
        iterator = execute_run_iterator(dg.reconstructable(close_active_worker_job), run, instance)
        assert isinstance(iterator, GeneratorType)
        pid = None
        try:
            for event in iterator:
                if event.is_step_start:
                    break
            marker = Path(instance.storage_directory()) / "independent-pid"
            until = time.monotonic() + 3
            while not marker.exists() and time.monotonic() < until:
                time.sleep(0.01)
            assert marker.exists()
            pid = int(marker.read_text())
            iterator.close()
            with pytest.raises(ProcessLookupError):
                os.kill(pid, 0)
            assert not list(Path(instance.storage_directory()).glob("attempt-*"))
        finally:
            iterator.close()
            if pid is not None:
                for process in multiprocessing.active_children():
                    if process.pid == pid and process.is_alive():
                        (tmp_path / "consumer-close-fixture-rescue").write_text(str(pid))
                        process.kill()
                        process.join(timeout=2)
                        assert not process.is_alive()
