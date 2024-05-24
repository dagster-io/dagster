import re

import pytest
from dagster._api.snapshot_execution_plan import sync_get_external_execution_plan_grpc
from dagster._core.definitions.events import AssetKey
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation.handle import JobHandle
from dagster._core.snap.execution_plan_snapshot import ExecutionPlanSnapshot

from .utils import get_bar_repo_code_location


def test_execution_plan_error_grpc(instance: DagsterInstance):
    with get_bar_repo_code_location(instance) as code_location:
        job_handle = JobHandle("foo", code_location.get_repository("bar_repo").handle)
        api_client = code_location.client

        with pytest.raises(
            DagsterUserCodeProcessError,
            match=re.escape(
                "AssetKey(s) ['fake'] were selected, but no AssetsDefinition objects supply these keys."
            ),
        ):
            sync_get_external_execution_plan_grpc(
                api_client,
                job_handle.get_external_origin(),
                run_config={},
                asset_selection={AssetKey("fake")},
                job_snapshot_id="12345",
            )


def test_execution_plan_snapshot_api_grpc(instance: DagsterInstance):
    with get_bar_repo_code_location(instance) as code_location:
        job_handle = JobHandle("foo", code_location.get_repository("bar_repo").handle)
        api_client = code_location.client

        execution_plan_snapshot = sync_get_external_execution_plan_grpc(
            api_client,
            job_handle.get_external_origin(),
            run_config={},
            job_snapshot_id="12345",
        )

        assert isinstance(execution_plan_snapshot, ExecutionPlanSnapshot)
        assert execution_plan_snapshot.step_keys_to_execute == [
            "do_something",
            "do_input",
        ]
        assert len(execution_plan_snapshot.steps) == 2


def test_execution_plan_with_step_keys_to_execute_snapshot_api_grpc(instance: DagsterInstance):
    with get_bar_repo_code_location(instance) as code_location:
        job_handle = JobHandle("foo", code_location.get_repository("bar_repo").handle)
        api_client = code_location.client

        execution_plan_snapshot = sync_get_external_execution_plan_grpc(
            api_client,
            job_handle.get_external_origin(),
            run_config={},
            job_snapshot_id="12345",
            step_keys_to_execute=["do_something"],
        )

        assert isinstance(execution_plan_snapshot, ExecutionPlanSnapshot)
        assert execution_plan_snapshot.step_keys_to_execute == [
            "do_something",
        ]
        assert len(execution_plan_snapshot.steps) == 2


def test_execution_plan_with_subset_snapshot_api_grpc(instance: DagsterInstance):
    with get_bar_repo_code_location(instance) as code_location:
        job_handle = JobHandle("foo", code_location.get_repository("bar_repo").handle)
        api_client = code_location.client

        execution_plan_snapshot = sync_get_external_execution_plan_grpc(
            api_client,
            job_handle.get_external_origin(),
            run_config={"ops": {"do_input": {"inputs": {"x": {"value": "test"}}}}},
            job_snapshot_id="12345",
            op_selection=["do_input"],
        )

        assert isinstance(execution_plan_snapshot, ExecutionPlanSnapshot)
        assert execution_plan_snapshot.step_keys_to_execute == [
            "do_input",
        ]
        assert len(execution_plan_snapshot.steps) == 1
