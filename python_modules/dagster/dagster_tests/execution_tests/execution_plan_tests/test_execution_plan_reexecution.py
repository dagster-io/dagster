import os
import pickle

import pytest

from dagster import (
    DependencyDefinition,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
    execute_pipeline,
    lambda_solid,
    reexecute_pipeline,
)
from dagster._core.definitions.pipeline_base import InMemoryPipeline
from dagster._core.errors import DagsterExecutionStepNotFoundError, DagsterInvariantViolationError
from dagster._core.events import get_step_output_event
from dagster._core.execution.api import execute_plan
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.instance import DagsterInstance
from dagster._core.system_config.objects import ResolvedRunConfig
from dagster._core.test_utils import default_mode_def_for_test


def define_addy_pipeline(using_file_system=False):
    @lambda_solid(input_defs=[InputDefinition("num", Int)], output_def=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    @lambda_solid(input_defs=[InputDefinition("num", Int)], output_def=OutputDefinition(Int))
    def add_two(num):
        return num + 2

    @lambda_solid(input_defs=[InputDefinition("num", Int)], output_def=OutputDefinition(Int))
    def add_three(num):
        return num + 3

    pipeline_def = PipelineDefinition(
        name="execution_plan_reexecution",
        solid_defs=[add_one, add_two, add_three],
        dependencies={
            "add_two": {"num": DependencyDefinition("add_one")},
            "add_three": {"num": DependencyDefinition("add_two")},
        },
        mode_defs=[default_mode_def_for_test] if using_file_system else None,
    )
    return pipeline_def


def test_execution_plan_reexecution():
    pipeline_def = define_addy_pipeline(using_file_system=True)
    instance = DagsterInstance.ephemeral()
    run_config = {"solids": {"add_one": {"inputs": {"num": {"value": 3}}}}}
    result = execute_pipeline(
        pipeline_def,
        run_config=run_config,
        instance=instance,
    )

    assert result.success

    with open(
        os.path.join(instance.storage_directory(), result.run_id, "add_one", "result"),
        "rb",
    ) as read_obj:
        assert pickle.load(read_obj) == 4

    with open(
        os.path.join(instance.storage_directory(), result.run_id, "add_two", "result"),
        "rb",
    ) as read_obj:
        assert pickle.load(read_obj) == 6

    ## re-execute add_two

    resolved_run_config = ResolvedRunConfig.build(
        pipeline_def,
        run_config=run_config,
    )
    execution_plan = ExecutionPlan.build(
        InMemoryPipeline(pipeline_def),
        resolved_run_config,
        known_state=KnownExecutionState.build_for_reexecution(
            instance,
            instance.get_run_by_id(result.run_id),
        ),
    )

    subset_plan = execution_plan.build_subset_plan(["add_two"], pipeline_def, resolved_run_config)
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline_def,
        execution_plan=subset_plan,
        run_config=run_config,
        parent_run_id=result.run_id,
        root_run_id=result.run_id,
    )

    step_events = execute_plan(
        subset_plan,
        InMemoryPipeline(pipeline_def),
        run_config=run_config,
        pipeline_run=pipeline_run,
        instance=instance,
    )
    assert not os.path.exists(
        os.path.join(instance.storage_directory(), pipeline_run.run_id, "add_one", "result")
    )
    with open(
        os.path.join(instance.storage_directory(), pipeline_run.run_id, "add_two", "result"),
        "rb",
    ) as read_obj:
        assert pickle.load(read_obj) == 6

    assert not get_step_output_event(step_events, "add_one")
    assert get_step_output_event(step_events, "add_two")


def test_execution_plan_reexecution_with_in_memory():
    pipeline_def = define_addy_pipeline()
    instance = DagsterInstance.ephemeral()
    run_config = {"solids": {"add_one": {"inputs": {"num": {"value": 3}}}}}
    result = execute_pipeline(pipeline_def, run_config=run_config, instance=instance)

    assert result.success

    ## re-execute add_two

    resolved_run_config = ResolvedRunConfig.build(pipeline_def, run_config=run_config)
    execution_plan = ExecutionPlan.build(
        InMemoryPipeline(pipeline_def),
        resolved_run_config,
        known_state=KnownExecutionState.build_for_reexecution(
            instance,
            instance.get_run_by_id(result.run_id),
        ),
    )

    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline_def,
        execution_plan=execution_plan,
        run_config=run_config,
        parent_run_id=result.run_id,
        root_run_id=result.run_id,
    )

    with pytest.raises(DagsterInvariantViolationError):
        execute_plan(
            execution_plan.build_subset_plan(["add_two"], pipeline_def, resolved_run_config),
            InMemoryPipeline(pipeline_def),
            run_config=run_config,
            pipeline_run=pipeline_run,
            instance=instance,
        )


def test_pipeline_step_key_subset_execution():
    pipeline_def = define_addy_pipeline(using_file_system=True)
    instance = DagsterInstance.ephemeral()
    run_config = {"solids": {"add_one": {"inputs": {"num": {"value": 3}}}}}
    result = execute_pipeline(pipeline_def, run_config=run_config, instance=instance)

    assert result.success
    with open(
        os.path.join(instance.storage_directory(), result.run_id, "add_one", "result"),
        "rb",
    ) as read_obj:
        assert pickle.load(read_obj) == 4

    with open(
        os.path.join(instance.storage_directory(), result.run_id, "add_two", "result"),
        "rb",
    ) as read_obj:
        assert pickle.load(read_obj) == 6

    ## re-execute add_two

    pipeline_reexecution_result = reexecute_pipeline(
        pipeline_def,
        parent_run_id=result.run_id,
        run_config=run_config,
        step_selection=["add_two"],
        instance=instance,
    )

    assert pipeline_reexecution_result.success

    step_events = pipeline_reexecution_result.step_event_list
    assert step_events
    assert not os.path.exists(
        os.path.join(
            instance.storage_directory(), pipeline_reexecution_result.run_id, "add_one", "result"
        )
    )
    with open(
        os.path.join(
            instance.storage_directory(), pipeline_reexecution_result.run_id, "add_two", "result"
        ),
        "rb",
    ) as read_obj:
        assert pickle.load(read_obj) == 6

    assert not get_step_output_event(step_events, "add_one")
    assert get_step_output_event(step_events, "add_two")

    with pytest.raises(
        DagsterExecutionStepNotFoundError,
        match="Step selection refers to unknown step: nope",
    ):
        reexecute_pipeline(
            pipeline_def,
            parent_run_id=result.run_id,
            run_config=run_config,
            step_selection=["nope"],
            instance=instance,
        )
