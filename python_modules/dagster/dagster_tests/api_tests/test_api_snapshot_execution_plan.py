import re

import pytest
from dagster.api.snapshot_execution_plan import sync_get_external_execution_plan_grpc
from dagster.core.errors import DagsterUserCodeProcessError
from dagster.core.host_representation.handle import PipelineHandle
from dagster.core.snap.execution_plan_snapshot import ExecutionPlanSnapshot

from .utils import get_bar_repo_repository_location


def test_execution_plan_error_grpc():
    with get_bar_repo_repository_location() as repository_location:
        pipeline_handle = PipelineHandle(
            "foo", repository_location.get_repository("bar_repo").handle
        )
        api_client = repository_location.client

        with pytest.raises(
            DagsterUserCodeProcessError,
            match=re.escape("Could not find mode made_up_mode in pipeline foo"),
        ):
            sync_get_external_execution_plan_grpc(
                api_client,
                pipeline_handle.get_external_origin(),
                run_config={},
                mode="made_up_mode",
                pipeline_snapshot_id="12345",
            )


def test_execution_plan_snapshot_api_grpc():
    with get_bar_repo_repository_location() as repository_location:
        pipeline_handle = PipelineHandle(
            "foo", repository_location.get_repository("bar_repo").handle
        )
        api_client = repository_location.client

        execution_plan_snapshot = sync_get_external_execution_plan_grpc(
            api_client,
            pipeline_handle.get_external_origin(),
            run_config={},
            mode="default",
            pipeline_snapshot_id="12345",
        )

        assert isinstance(execution_plan_snapshot, ExecutionPlanSnapshot)
        assert execution_plan_snapshot.step_keys_to_execute == [
            "do_something",
            "do_input",
        ]
        assert len(execution_plan_snapshot.steps) == 2


def test_execution_plan_with_step_keys_to_execute_snapshot_api_grpc():
    with get_bar_repo_repository_location() as repository_location:
        pipeline_handle = PipelineHandle(
            "foo", repository_location.get_repository("bar_repo").handle
        )
        api_client = repository_location.client

        execution_plan_snapshot = sync_get_external_execution_plan_grpc(
            api_client,
            pipeline_handle.get_external_origin(),
            run_config={},
            mode="default",
            pipeline_snapshot_id="12345",
            step_keys_to_execute=["do_something"],
        )

        assert isinstance(execution_plan_snapshot, ExecutionPlanSnapshot)
        assert execution_plan_snapshot.step_keys_to_execute == [
            "do_something",
        ]
        assert len(execution_plan_snapshot.steps) == 2


def test_execution_plan_with_subset_snapshot_api_grpc():
    with get_bar_repo_repository_location() as repository_location:
        pipeline_handle = PipelineHandle(
            "foo", repository_location.get_repository("bar_repo").handle
        )
        api_client = repository_location.client

        execution_plan_snapshot = sync_get_external_execution_plan_grpc(
            api_client,
            pipeline_handle.get_external_origin(),
            run_config={"solids": {"do_input": {"inputs": {"x": {"value": "test"}}}}},
            mode="default",
            pipeline_snapshot_id="12345",
            solid_selection=["do_input"],
        )

        assert isinstance(execution_plan_snapshot, ExecutionPlanSnapshot)
        assert execution_plan_snapshot.step_keys_to_execute == [
            "do_input",
        ]
        assert len(execution_plan_snapshot.steps) == 1
