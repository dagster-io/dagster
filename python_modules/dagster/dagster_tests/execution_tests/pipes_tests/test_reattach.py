import os
import subprocess
import time
import uuid
from enum import Enum
from pathlib import Path

import dagster as dg
import pytest
from dagster import AssetExecutionContext, OpExecutionContext
from dagster._core.errors import DagsterPipesExecutionError
from dagster._core.events import DagsterEventType, EngineEventData
from dagster._core.pipes.client import PipesClient, PipesClientCompletedInvocation
from dagster._core.pipes.context import PipesExtras
from dagster._core.pipes.reattach import (
    PIPES_LAUNCH_HANDLE_METADATA_KEY,
    PipesLaunchHandle,
    find_latest_launch_handle,
    find_latest_launch_handle_for_run,
    record_external_launch,
    record_external_reattach,
)
from dagster._core.pipes.utils import (
    PipesTempFileContextInjector,
    PipesTempFileMessageReader,
    open_pipes_session,
)
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.tags import RESUME_RETRY_TAG
from dagster._serdes import deserialize_value, serialize_value

POLL_TIMEOUT_SECONDS = 15


class ExternalRunState(Enum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


# ########################
# ##### FIXTURES
# ########################


@pytest.fixture
def client(tmp_path):
    return ReattachableSubprocessClient(tmp_path / "runs")


# ########################
# ##### TESTS
# ########################


def test_launch_records_handle(client):
    @dg.asset
    def my_asset(context: AssetExecutionContext):
        return client.run(context=context, cmd="echo hello").get_materialize_result()

    with dg.instance_for_test() as instance:
        result = dg.materialize([my_asset], instance=instance, raise_on_error=False)
        assert result.success
        assert client.launch_count == 1
        assert client.reattach_log == []

        handles = _handles_from_run(instance, result.run_id, "my_asset")
        assert len(handles) == 1
        handle = handles[0]
        assert handle.client_name == "ReattachableSubprocessClient"
        assert handle.step_key == "my_asset"
        assert handle.retry_number == 0
        workdir = Path(handle.extras["workdir"])
        assert (workdir / "exit_status").read_text().strip() == "0"
        assert (workdir / "stdout.log").read_text().strip() == "hello"


def test_reattach_semantics(client):
    # Crash after launching a still-running subprocess: the in-run retry must find the
    # live process via the handle and adopt it instead of launching a duplicate.
    @dg.asset(retry_policy=dg.RetryPolicy(max_retries=1))
    def crashes_then_reattaches(context: AssetExecutionContext):
        return client.run(
            context=context,
            cmd="sleep 1; echo done",
            crash_on_first_attempt=True,
        ).get_materialize_result()

    with dg.instance_for_test() as instance:
        result = dg.materialize([crashes_then_reattaches], instance=instance, raise_on_error=False)
        assert result.success
        assert client.launch_count == 1
        assert len(client.reattach_log) == 1

        # both the launch and the reattach are recorded, pointing at the same process
        handles = _handles_from_run(instance, result.run_id, "crashes_then_reattaches")
        assert [h.retry_number for h in handles] == [0, 1]
        assert len({h.external_run_id for h in handles}) == 1

    # Process finished (successfully) while the "waiter" was down: the retry adopts the
    # completed run's exit status from the filesystem; the process itself is gone.
    client2 = ReattachableSubprocessClient(client.root.parent / "runs2")

    @dg.asset(retry_policy=dg.RetryPolicy(max_retries=1))
    def adopts_finished(context: AssetExecutionContext):
        invocation = client2.run(
            context=context,
            cmd="echo already-done",
            crash_on_first_attempt=True,
            wait_before_crash=True,
        )
        return invocation.get_materialize_result()

    with dg.instance_for_test() as instance:
        result = dg.materialize([adopts_finished], instance=instance, raise_on_error=False)
        assert result.success
        assert client2.launch_count == 1
        assert len(client2.reattach_log) == 1

    # A terminally failed process must NOT be adopted: the retry exists to re-execute,
    # so a fresh process is launched.
    client3 = ReattachableSubprocessClient(client.root.parent / "runs3")

    @dg.asset(retry_policy=dg.RetryPolicy(max_retries=1))
    def fails_then_relaunches(context: AssetExecutionContext):
        cmd = "exit 3" if client3.launch_count == 0 else "echo ok"
        return client3.run(context=context, cmd=cmd).get_materialize_result()

    with dg.instance_for_test() as instance:
        result = dg.materialize([fails_then_relaunches], instance=instance, raise_on_error=False)
        assert result.success
        assert client3.launch_count == 2
        assert client3.reattach_log == []


def test_ancestry_lookup():
    # Handles written in a parent run are found from a from-failure retry of that run,
    # but not from an intentional re-execution, a different step, or a different client.
    with dg.instance_for_test() as instance:
        parent = _add_run(instance, run_id=str(uuid.uuid4()))
        retry_child = _add_run(
            instance,
            run_id=str(uuid.uuid4()),
            parent_run_id=parent.run_id,
            root_run_id=parent.run_id,
            tags={RESUME_RETRY_TAG: "true"},
        )
        reexecution_child = _add_run(
            instance,
            run_id=str(uuid.uuid4()),
            parent_run_id=parent.run_id,
            root_run_id=parent.run_id,
        )

        def _find(run, step_key="the_step", client_name="ReattachableSubprocessClient"):
            return find_latest_launch_handle_for_run(
                instance=instance, run=run, step_key=step_key, client_name=client_name
            )

        assert _find(retry_child) is None

        handle = PipesLaunchHandle(
            client_name="ReattachableSubprocessClient",
            external_run_id="ext-123",
            step_key="the_step",
            retry_number=0,
            launched_at=0.0,
        )
        instance.report_engine_event(
            "[pipes] Launched external run ext-123 via ReattachableSubprocessClient.",
            dagster_run=parent,
            engine_event_data=EngineEventData(
                metadata={
                    PIPES_LAUNCH_HANDLE_METADATA_KEY: dg.MetadataValue.text(serialize_value(handle))
                }
            ),
            step_key="the_step",
        )

        assert _find(retry_child) == handle

        # an intentional re-execution (no from-failure retry tag) does not inherit the
        # parent's handle
        assert _find(reexecution_child) is None

        # step_key or client mismatch finds nothing
        assert _find(retry_child, step_key="other_step") is None
        assert _find(retry_child, client_name="OtherClient") is None


# ########################
# ##### HELPERS
# ########################


class ReattachableSubprocessClient(PipesClient):
    """Reference reattachable pipes client backed by real subprocesses.

    A subprocess is "an engine with no API", so every volatile resource moves into the
    filesystem at launch and the handle records paths instead of live resources:

    - identity: (pid, create time) in handle extras, checked before adoption
    - channel: stdout/stderr redirected to files in a per-launch workdir
    - terminal status: a shell wrapper writes the exit code to a file, so a reattacher
      never needs to be the process's parent to get the verdict
    """

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.reattach_log: list[str] = []

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @property
    def launch_count(self) -> int:
        return len(list(self.root.iterdir()))

    def run(  # ty: ignore[invalid-method-override]
        self,
        *,
        context: OpExecutionContext | AssetExecutionContext,
        cmd: str,
        crash_on_first_attempt: bool = False,
        wait_before_crash: bool = False,
        extras: PipesExtras | None = None,
    ) -> PipesClientCompletedInvocation:
        with open_pipes_session(
            context=context,
            context_injector=PipesTempFileContextInjector(),
            message_reader=PipesTempFileMessageReader(),
            extras=extras,
        ) as session:
            handle = find_latest_launch_handle(context, client_name="ReattachableSubprocessClient")
            if handle and self._get_state(handle) in (
                ExternalRunState.RUNNING,
                ExternalRunState.SUCCESS,
            ):
                handle = record_external_reattach(context, handle)
                self.reattach_log.append(handle.external_run_id)
            else:
                handle = self._launch(context, cmd)
                if crash_on_first_attempt and context.retry_number == 0:
                    if wait_before_crash:
                        self._poll_to_completion(handle)
                    raise RuntimeError("simulated step worker crash")

            exit_status = self._poll_to_completion(handle)
            if exit_status != 0:
                raise DagsterPipesExecutionError(
                    f"External run {handle.external_run_id} failed with code {exit_status}."
                )
        return PipesClientCompletedInvocation(session)

    def _launch(
        self, context: OpExecutionContext | AssetExecutionContext, cmd: str
    ) -> PipesLaunchHandle:
        external_run_id = str(uuid.uuid4())
        workdir = self.root / external_run_id
        workdir.mkdir()
        # The wrapper writes the exit code to a file so that a reattacher never needs to
        # be the process's parent to learn the verdict.
        process = subprocess.Popen(
            ["/bin/sh", "-c", f"({cmd}) > stdout.log 2> stderr.log; echo $? > exit_status"],
            cwd=workdir,
            start_new_session=True,
        )
        return record_external_launch(
            context,
            client_name="ReattachableSubprocessClient",
            external_run_id=external_run_id,
            extras={
                "workdir": str(workdir),
                "pid": process.pid,
                "create_time": _process_create_time(process.pid),
            },
        )

    def _get_state(self, handle: PipesLaunchHandle) -> ExternalRunState:
        workdir = Path(handle.extras["workdir"])
        exit_status_file = workdir / "exit_status"
        if exit_status_file.exists():
            return (
                ExternalRunState.SUCCESS
                if exit_status_file.read_text().strip() == "0"
                else ExternalRunState.FAILED
            )
        pid = handle.extras["pid"]
        if _is_alive(pid) and _process_create_time(pid) == handle.extras["create_time"]:
            return ExternalRunState.RUNNING
        # re-check: the process may have written its status and exited between the two
        # checks above
        if exit_status_file.exists():
            return (
                ExternalRunState.SUCCESS
                if exit_status_file.read_text().strip() == "0"
                else ExternalRunState.FAILED
            )
        # process gone without writing a status file: unrecoverable
        return ExternalRunState.FAILED

    def _poll_to_completion(self, handle: PipesLaunchHandle) -> int:
        workdir = Path(handle.extras["workdir"])
        exit_status_file = workdir / "exit_status"
        deadline = time.time() + POLL_TIMEOUT_SECONDS
        while time.time() < deadline:
            if exit_status_file.exists():
                return int(exit_status_file.read_text().strip())
            if self._get_state(handle) == ExternalRunState.FAILED:
                return -1
            time.sleep(0.05)
        raise TimeoutError(f"External run {handle.external_run_id} did not complete in time.")


def _is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _process_create_time(pid: int) -> str | None:
    """Process start time via `ps`, used to guard PID reuse (works on Linux and macOS)."""
    result = subprocess.run(
        ["ps", "-p", str(pid), "-o", "lstart="], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _handles_from_run(instance, run_id: str, step_key: str) -> list[PipesLaunchHandle]:
    handles = []
    for entry in instance.all_logs(run_id, of_type=DagsterEventType.ENGINE_EVENT):
        if entry.step_key != step_key or entry.dagster_event is None:
            continue
        value = entry.dagster_event.engine_event_data.metadata.get(PIPES_LAUNCH_HANDLE_METADATA_KEY)
        if value is not None:
            handles.append(deserialize_value(value.value, PipesLaunchHandle))
    return handles


def _add_run(instance, run_id: str, parent_run_id=None, root_run_id=None, tags=None) -> DagsterRun:
    run = DagsterRun(
        job_name="fake_job",
        run_id=run_id,
        parent_run_id=parent_run_id,
        root_run_id=root_run_id,
        tags=tags or {},
    )
    instance.run_storage.add_run(run)
    return run
