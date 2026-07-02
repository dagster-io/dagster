# ruff: noqa: SLF001

import threading
import time

import dagster._core.workspace.context as ws_context
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.remote_origin import GrpcServerCodeLocationOrigin
from dagster._core.remote_representation.code_location import CodeLocation
from dagster._core.test_utils import instance_for_test
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.workspace import (
    CodeLocationEntry,
    CodeLocationLoadStatus,
    CurrentWorkspace,
    DefinitionsSource,
)
from dagster._time import get_current_timestamp


def _wait_until(predicate, timeout_s: float, sleep_s: float = 0.02) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(sleep_s)
    return False


class DummyCodeLocation(CodeLocation):
    """Minimal CodeLocation implementation for this test."""

    def __init__(self, *args, **kwargs):
        pass

    def get_display_metadata(self):
        return {}

    def cleanup(self) -> None:
        pass


# CodeLocation may be ABC; allow instantiation for this test across Dagster versions.
try:
    DummyCodeLocation.__abstractmethods__ = frozenset()  # type: ignore[attr-defined]
except Exception:
    pass


def test_grpc_code_location_load_error_auto_recovers(monkeypatch):
    """Repro for #33297-style behavior at the core level.

    - First refresh fails with DagsterUserCodeUnreachableError (e.g. DEADLINE_EXCEEDED)
    - Background retry loop keeps retrying
    - Later the server becomes healthy
    - Expected: workspace auto-retries and clears load_error WITHOUT manual refresh
    """
    # Speed up retry loop for unit test
    monkeypatch.setattr(ws_context, "LOCATION_LOAD_RETRY_BASE_DELAY", 0.05, raising=False)
    monkeypatch.setattr(ws_context, "LOCATION_LOAD_RETRY_MAX_DELAY", 0.2, raising=False)
    monkeypatch.setattr(ws_context, "LOCATION_LOAD_RETRY_JITTER", 0.0, raising=False)

    healthy = {"value": False}
    calls = {"total": 0, "unhealthy": 0, "healthy": 0}
    saw_healthy_call = threading.Event()

    origin = GrpcServerCodeLocationOrigin(host="fake", port=3030, location_name="loc")

    def fake_create_location(self, instance):
        calls["total"] += 1
        if not healthy["value"]:
            calls["unhealthy"] += 1
            raise DagsterUserCodeUnreachableError("simulated DEADLINE_EXCEEDED during initial load")

        calls["healthy"] += 1
        saw_healthy_call.set()
        return DummyCodeLocation()

    monkeypatch.setattr(GrpcServerCodeLocationOrigin, "create_location", fake_create_location)
    monkeypatch.setattr(GrpcServerCodeLocationOrigin, "reload_location", fake_create_location)

    with instance_for_test() as instance:
        with WorkspaceProcessContext(
            instance=instance,
            workspace_load_target=None,
            version="test",
            read_only=False,
        ) as ctx:
            # Inject entry so refresh_code_location has something to refresh
            entry = CodeLocationEntry(
                origin=origin,
                code_location=None,
                load_error=None,
                load_status=CodeLocationLoadStatus.LOADED,
                display_metadata=origin.get_display_metadata(),
                update_timestamp=get_current_timestamp(),
                version_key=str(get_current_timestamp()),
                definitions_source=DefinitionsSource.CODE_SERVER,
            )
            with ctx._lock:
                ctx._current_workspace = CurrentWorkspace(code_location_entries={"loc": entry})

            # 1) First refresh fails -> should be in load_error and scheduled for retry
            ctx.refresh_code_location("loc")
            assert ctx._retry_thread.is_alive()
            assert "loc" in ctx._retry_state
            assert ctx.has_code_location_error("loc") is True
            assert calls["total"] == 1

            # 2) Wait until at least one background retry happened while still unhealthy
            ok = _wait_until(lambda: calls["total"] >= 2, timeout_s=2.0, sleep_s=0.02)
            assert ok, f"Expected background retry attempts, but none occurred (calls={calls})"

            # 3) Now server becomes healthy
            healthy["value"] = True

            # Test-only: force the next retry to run ASAP after healthy=True
            with ctx._retry_cv:
                st = ctx._retry_state.get("loc")
                if st is not None:
                    st["next_ts"] = time.time()
                    ctx._retry_cv.notify()

            # 4) Ensure we actually executed at least one "healthy" attempt
            assert saw_healthy_call.wait(timeout=3.0), (
                f"Never observed a post-healthy retry attempt. calls={calls}, "
                f"retry_state={ctx._retry_state}"
            )

            # 5) Expect recovery (load_error cleared)
            ok = _wait_until(
                lambda: not ctx.has_code_location_error("loc"),
                timeout_s=3.0,
                sleep_s=0.05,
            )
            assert ok, f"Expected load_error to clear after post-healthy retry. calls={calls}"

            assert "loc" not in ctx._retry_state
