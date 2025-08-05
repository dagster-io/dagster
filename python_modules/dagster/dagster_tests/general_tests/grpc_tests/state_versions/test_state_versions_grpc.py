import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import dagster as dg
import pytest
import yaml
from dagster._api.list_repositories import sync_list_repositories_grpc
from dagster._api.snapshot_execution_plan import sync_get_external_execution_plan_grpc
from dagster._core.code_pointer import ModuleCodePointer
from dagster._core.definitions.assets.job.asset_job import IMPLICIT_ASSET_JOB_NAME
from dagster._core.origin import JobPythonOrigin, RepositoryPythonOrigin
from dagster._core.remote_origin import (
    GrpcServerCodeLocationOrigin,
    RemoteJobOrigin,
    RemoteRepositoryOrigin,
)
from dagster._core.remote_representation.external_data import RepositorySnap
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.test_utils import poll_for_finished_run
from dagster._core.utils import make_new_run_id
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._core.workspace.load_target import GrpcServerTarget
from dagster._grpc.client import DagsterGrpcClient
from dagster._grpc.server import wait_for_grpc_server
from dagster._utils import find_free_port
from dagster_dg_core.utils import activate_venv
from dagster_dg_core_tests.utils import ProxyRunner, isolated_example_project_foo_bar

from dagster_tests.general_tests.grpc_tests.test_persistent import entrypoints


@pytest.mark.parametrize("entrypoint", entrypoints())
def test_state_versions_grpc(entrypoint):
    port = find_free_port()

    with (
        # setup tempdir for the repo, activate the virtualenv
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner, in_workspace=False, use_editable_dagster=True, uv_sync=True
        ) as project_dir,
        activate_venv(project_dir / ".venv"),
        # test instance with run launcher configured for GRPC runs
        dg.instance_for_test() as instance,
    ):
        # write a local component defs.yaml
        component_dir = project_dir / "src/foo_bar/defs/the_component"
        component_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            Path(__file__).parent / "sample_state_backed_component.py",
            component_dir / "local.py",
        )
        with (component_dir / "defs.yaml").open("w") as f:
            yaml.dump(
                {"type": ".local.SampleStateBackedComponent"},
                f,
            )

        # add some pre-existing state, keep track of it
        with tempfile.TemporaryDirectory() as temp_dir:
            p = Path(temp_dir) / "state.json"
            p.write_text("hi")
            instance.defs_state_storage.upload_state_from_path(
                path=p,
                key="the_component",
                version="abcde-12345",
            )

        original_state_versions = instance.defs_state_storage.get_latest_defs_state_info()
        assert original_state_versions and len(original_state_versions.info_mapping) == 1
        assert original_state_versions.get_version("the_component") == "abcde-12345"

        # add some new state with a different value, should NOT use this
        with tempfile.TemporaryDirectory() as temp_dir:
            p = Path(temp_dir) / "state.json"
            p.write_text("blah")
            instance.defs_state_storage.upload_state_from_path(
                path=p,
                key="the_component",
                version="fghij-67890",
            )

        subprocess_args = entrypoint + [
            "--port",
            str(port),
            "--python-file",
            str(project_dir / "src/foo_bar/definitions.py"),
            "--instance-ref",
            dg.serialize_value(instance.get_ref()),
            "--state-info",
            dg.serialize_value(original_state_versions),
        ]

        process = subprocess.Popen(subprocess_args)

        try:
            client = DagsterGrpcClient(port=port, host="localhost")
            wait_for_grpc_server(process, client, subprocess_args)
            list_repositories_response = sync_list_repositories_grpc(client)
            # should be using the original state versions even though we added new state
            assert list_repositories_response.state_info == original_state_versions

            # Get the repository origin from the response
            repo_symbol = list_repositories_response.repository_symbols[0]
            repo_name = repo_symbol.repository_name
            code_location_origin = GrpcServerCodeLocationOrigin(port=port, host="localhost")

            remote_repo_origin = RemoteRepositoryOrigin(
                code_location_origin=code_location_origin, repository_name=repo_name
            )

            # Verify the repository has the expected assets
            serialized_repo = client.external_repository(
                remote_repo_origin,
                defer_snapshots=False,
            )
            repo_snap = dg.deserialize_value(serialized_repo, RepositorySnap)
            assert len(repo_snap.asset_nodes) == 1
            # asset key should be using the old state value
            assert repo_snap.asset_nodes[0].asset_key == dg.AssetKey("hi")

            # Execute the implicit asset job using execution plan pattern

            job_origin = RemoteJobOrigin(
                job_name=IMPLICIT_ASSET_JOB_NAME,
                repository_origin=remote_repo_origin,
            )

            # Get the job snapshot from the remote job
            job_response = client.external_job(remote_repo_origin, IMPLICIT_ASSET_JOB_NAME)
            from dagster._core.remote_representation.external_data import JobDataSnap

            job_data_snap = dg.deserialize_value(job_response.serialized_job_data, JobDataSnap)
            job_snapshot = job_data_snap.job

            # Get execution plan snapshot over GRPC (following test_api_snapshot_execution_plan.py pattern)
            execution_plan_snapshot = sync_get_external_execution_plan_grpc(
                client,
                job_origin,
                run_config={},
                job_snapshot_id=job_snapshot.snapshot_id,
            )
            # should be using the old state value
            assert execution_plan_snapshot.step_keys_to_execute == ["hi"]

            run_id = make_new_run_id()

            # Create run with execution plan (following test_external_execution_plan.py pattern)
            # For GRPC-based runs, we need a JobPythonOrigin that points to the remote server

            # Create a repository origin that points to the GRPC server
            # We need to use a special code pointer that the DefaultRunLauncher can handle
            repository_origin = RepositoryPythonOrigin(
                executable_path=sys.executable,
                code_pointer=ModuleCodePointer(
                    module="dagster._grpc.client",
                    fn_name="DagsterGrpcClient",
                    working_directory=None,
                ),
            )
            job_code_origin = JobPythonOrigin(
                job_name=IMPLICIT_ASSET_JOB_NAME,
                repository_origin=repository_origin,
            )

            instance.create_run(
                run_id=run_id,
                job_name=IMPLICIT_ASSET_JOB_NAME,
                run_config={},
                status=DagsterRunStatus.NOT_STARTED,
                tags={},
                root_run_id=None,
                parent_run_id=None,
                step_keys_to_execute=execution_plan_snapshot.step_keys_to_execute,
                execution_plan_snapshot=execution_plan_snapshot,
                job_snapshot=job_snapshot,
                parent_job_snapshot=None,
                asset_selection=None,
                asset_check_selection=None,
                resolved_op_selection=None,
                op_selection=None,
                remote_job_origin=job_origin,
                job_code_origin=job_code_origin,
                asset_graph=MagicMock(),
            )
            # create workspace context
            with WorkspaceProcessContext(
                instance,
                GrpcServerTarget(
                    host="localhost",
                    port=port,
                    socket=None,
                    location_name=f"grpc:localhost:{port}",
                ),
            ) as workspace_context:
                workspace_request_context = workspace_context.create_request_context()
                instance.launch_run(run_id=run_id, workspace=workspace_request_context)

                finished_run = poll_for_finished_run(instance, run_id)

            assert finished_run
            assert finished_run.run_id == run_id
            assert finished_run.status == DagsterRunStatus.SUCCESS

            # Verify that the run created an AssetMaterialization event with the key "hi"
            event_records = instance.all_logs(run_id)
            asset_materialization_events = [
                record
                for record in event_records
                if record.dagster_event
                and record.dagster_event.event_type_value == "ASSET_MATERIALIZATION"
            ]
            assert len(asset_materialization_events) == 1
            materialization_event = asset_materialization_events[0]
            assert materialization_event.dagster_event is not None
            assert materialization_event.dagster_event.asset_key == dg.AssetKey("hi")

        finally:
            process.terminate()
            process.wait()
