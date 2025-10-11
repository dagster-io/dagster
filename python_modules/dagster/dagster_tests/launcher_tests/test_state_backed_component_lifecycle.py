import inspect
import sys
import tempfile
import textwrap
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Callable

import dagster as dg
from dagster._core.instance_for_test import instance_for_test
from dagster._core.test_utils import poll_for_finished_run
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.utils import make_new_run_id
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import GrpcServerTarget
from dagster._grpc.server import GrpcServerProcess
from dagster._utils.env import environ


@contextmanager
def _temp_script(script_fn: Callable[[], Any]) -> Iterator[str]:
    """Create a temporary script file from a function, similar to _temp_script pattern."""
    # drop the signature line
    source = textwrap.dedent(inspect.getsource(script_fn).split("\n", 1)[1])
    with NamedTemporaryFile(suffix=".py") as file:
        file.write(source.encode())
        file.flush()
        yield file.name


def _scope_component_defs():
    """The actual script that will be written to the test file."""
    import os
    from pathlib import Path
    from unittest.mock import MagicMock

    import dagster as dg
    from dagster.components.component.state_backed_component import StateBackedComponent
    from dagster.components.utils.defs_state import DefsStateConfig

    class TestStateBackedComponent(StateBackedComponent, dg.Model, dg.Resolvable):
        sentinel_file_path: str
        defs_state: DefsStateConfig = DefsStateConfig.legacy_code_server_snapshots()

        @property
        def defs_state_config(self) -> DefsStateConfig:
            return self.defs_state

        def get_defs_state_key(self) -> str:
            return "test_state_backed_component"

        def build_defs_from_state(self, context, state_path):
            # because refresh_if_dev is True, we should always have a state path
            # for this test
            assert state_path is not None
            state_content = state_path.read_text().strip()
            asset_name = f"asset_{state_content}"

            @dg.asset(name=asset_name)
            def the_asset():
                return dg.MaterializeResult(metadata={"state_content": state_content})

            return dg.Definitions(assets=[the_asset])

        def write_state_to_path(self, state_path):
            sentinel_path = Path(self.sentinel_file_path)
            current_count = int(sentinel_path.read_text().strip())
            new_count = current_count + 1
            sentinel_path.write_text(str(new_count))
            state_path.write_text(f"state_content_{new_count}")

    @dg.definitions
    def defs():
        sentinel_path = Path(os.environ["SENTINEL_DIR"]) / "write_state_calls.txt"
        component = TestStateBackedComponent(sentinel_file_path=str(sentinel_path))
        return component.build_defs(MagicMock())


def test_state_backed_component_lifecycle():
    """Test that state-backed components are executed the correct number of times with gRPC server."""
    with (
        tempfile.TemporaryDirectory() as temp_dir,
        _temp_script(_scope_component_defs) as script_path,
        instance_for_test() as instance,
        environ({"SENTINEL_DIR": temp_dir, "DAGSTER_IS_DEV_CLI": "1"}),
    ):
        sentinel_path = Path(temp_dir) / "write_state_calls.txt"
        sentinel_path.write_text("0")  # Initialize with 0 calls

        loadable_target_origin = LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="defs",
            python_file=script_path,
        )

        with (
            GrpcServerProcess(
                instance_ref=instance.get_ref(),
                loadable_target_origin=loadable_target_origin,
                max_workers=4,
                wait_on_exit=False,
            ) as server_process,
            WorkspaceProcessContext(
                instance,
                GrpcServerTarget(
                    host="localhost",
                    socket=server_process.socket,
                    port=server_process.port,
                    location_name="test_state_backed",
                ),
            ) as workspace_process_context,
        ):
            workspace = workspace_process_context.create_request_context()
            # Test is now working - we can continue with the actual test logic

            # Get the code location and repository
            code_location = workspace.get_code_location("test_state_backed")
            # Check what repositories are available
            available_repos = list(code_location.get_repositories().keys())
            repository = code_location.get_repository(available_repos[0])

            # Check initial state - should have been called once during server startup
            assert int(sentinel_path.read_text().strip()) == 1

            # Get the asset job and create an execution plan, shouldn't require additional calls
            asset_job = repository.get_full_job("__ASSET_JOB")
            remote_execution_plan = code_location.get_execution_plan(
                remote_job=asset_job,
                run_config={},
                step_keys_to_execute=None,
                known_state=None,
            )
            assert int(sentinel_path.read_text().strip()) == 1

            # Create and launch a run
            run_id = make_new_run_id()
            instance.create_run(
                job_name="__ASSET_JOB",
                run_id=run_id,
                run_config={},
                resolved_op_selection=None,
                step_keys_to_execute=None,
                status=None,
                tags=None,
                root_run_id=None,
                parent_run_id=None,
                job_snapshot=asset_job.job_snapshot,
                execution_plan_snapshot=remote_execution_plan.execution_plan_snapshot,
                parent_job_snapshot=asset_job.parent_job_snapshot,
                remote_job_origin=asset_job.get_remote_origin(),
                job_code_origin=asset_job.get_python_origin(),
                asset_selection=None,
                op_selection=None,
                asset_check_selection=None,
                asset_graph=repository.asset_graph,
            )
            instance.launch_run(run_id=run_id, workspace=workspace)

            # should succeed
            finished_run = poll_for_finished_run(instance, run_id)
            assert finished_run.status == dg.DagsterRunStatus.SUCCESS

            # should not require additional calls
            assert int(sentinel_path.read_text().strip()) == 1

            # make sure the asset was created correctly
            asset_keys = list(repository.asset_graph.remote_asset_nodes_by_key.keys())
            assert len(asset_keys) == 1
            assert asset_keys[0].to_user_string() == "asset_state_content_1"
