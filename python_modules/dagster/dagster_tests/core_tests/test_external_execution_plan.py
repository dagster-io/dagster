import os
import pickle
import re

import pytest

from dagster import (
    In,
    Out,
    op,
    DagsterEventType,
    DagsterExecutionStepNotFoundError,
    DependencyDefinition,
    Int,
    reconstructable,
)
from dagster._core.definitions.pipeline_base import InMemoryPipeline
from dagster._core.execution.api import execute_plan
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.instance import DagsterInstance
from dagster._core.system_config.objects import ResolvedRunConfig
from dagster._core.test_utils import default_mode_def_for_test, instance_for_test
from dagster._legacy import (
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    lambda_solid,
)


def define_inty_pipeline(using_file_system=False):
    @op
    def return_one():
        return 1

    @op(ins={"num": In(Int)}, out=Out(Int))
    def add_one(num):
        return num + 1

    @op
    def user_throw_exception():
        raise Exception("whoops")

    pipeline = PipelineDefinition(
        name="basic_external_plan_execution",
        solid_defs=[return_one, add_one, user_throw_exception],
        dependencies={"add_one": {"num": DependencyDefinition("return_one")}},
        mode_defs=[default_mode_def_for_test] if using_file_system else None,
    )
    return pipeline


def define_reconstructable_inty_pipeline():
    return define_inty_pipeline(using_file_system=True)


def get_step_output(step_events, step_key, output_name="result"):
    for step_event in step_events:
        if (
            step_event.event_type == DagsterEventType.STEP_OUTPUT
            and step_event.step_key == step_key
            and step_event.step_output_data.output_name == output_name
        ):
            return step_event
    return None


def test_using_file_system_for_subplan():
    pipeline = define_inty_pipeline(using_file_system=True)

    instance = DagsterInstance.ephemeral()

    resolved_run_config = ResolvedRunConfig.build(pipeline)
    execution_plan = ExecutionPlan.build(
        InMemoryPipeline(pipeline), resolved_run_config
    )
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline, execution_plan=execution_plan
    )
    assert execution_plan.get_step_by_key("return_one")

    return_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(
                ["return_one"], pipeline, resolved_run_config
            ),
            InMemoryPipeline(pipeline),
            instance,
            pipeline_run=pipeline_run,
        )
    )

    assert get_step_output(return_one_step_events, "return_one")
    with open(
        os.path.join(
            instance.storage_directory(), pipeline_run.run_id, "return_one", "result"
        ),
        "rb",
    ) as read_obj:
        assert pickle.load(read_obj) == 1

    add_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(
                ["add_one"], pipeline, resolved_run_config
            ),
            InMemoryPipeline(pipeline),
            instance,
            pipeline_run=pipeline_run,
        )
    )

    assert get_step_output(add_one_step_events, "add_one")
    with open(
        os.path.join(
            instance.storage_directory(), pipeline_run.run_id, "add_one", "result"
        ),
        "rb",
    ) as read_obj:
        assert pickle.load(read_obj) == 2


def test_using_file_system_for_subplan_multiprocessing():
    with instance_for_test() as instance:
        pipeline = reconstructable(define_reconstructable_inty_pipeline)

        resolved_run_config = ResolvedRunConfig.build(
            pipeline.get_definition(),
        )
        execution_plan = ExecutionPlan.build(
            pipeline,
            resolved_run_config,
        )
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=pipeline.get_definition(), execution_plan=execution_plan
        )

        assert execution_plan.get_step_by_key("return_one")

        return_one_step_events = list(
            execute_plan(
                execution_plan.build_subset_plan(
                    ["return_one"], pipeline.get_definition(), resolved_run_config
                ),
                pipeline,
                instance,
                run_config=dict(execution={"multiprocess": {}}),
                pipeline_run=pipeline_run,
            )
        )

        assert get_step_output(return_one_step_events, "return_one")
        with open(
            os.path.join(
                instance.storage_directory(),
                pipeline_run.run_id,
                "return_one",
                "result",
            ),
            "rb",
        ) as read_obj:
            assert pickle.load(read_obj) == 1

        add_one_step_events = list(
            execute_plan(
                execution_plan.build_subset_plan(
                    ["add_one"], pipeline.get_definition(), resolved_run_config
                ),
                pipeline,
                instance,
                run_config=dict(execution={"multiprocess": {}}),
                pipeline_run=pipeline_run,
            )
        )

        assert get_step_output(add_one_step_events, "add_one")
        with open(
            os.path.join(
                instance.storage_directory(), pipeline_run.run_id, "add_one", "result"
            ),
            "rb",
        ) as read_obj:
            assert pickle.load(read_obj) == 2


def test_execute_step_wrong_step_key():
    pipeline = define_inty_pipeline()
    instance = DagsterInstance.ephemeral()

    resolved_run_config = ResolvedRunConfig.build(
        pipeline,
    )
    execution_plan = ExecutionPlan.build(
        InMemoryPipeline(pipeline),
        resolved_run_config,
    )
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline, execution_plan=execution_plan
    )

    with pytest.raises(DagsterExecutionStepNotFoundError) as exc_info:
        execute_plan(
            execution_plan.build_subset_plan(
                ["nope.compute"], pipeline, resolved_run_config
            ),
            InMemoryPipeline(pipeline),
            instance,
            pipeline_run=pipeline_run,
        )

    assert exc_info.value.step_keys == ["nope.compute"]

    assert (
        str(exc_info.value)
        == "Can not build subset plan from unknown step: nope.compute"
    )

    with pytest.raises(DagsterExecutionStepNotFoundError) as exc_info:
        execute_plan(
            execution_plan.build_subset_plan(
                ["nope.compute", "nuh_uh.compute"], pipeline, resolved_run_config
            ),
            InMemoryPipeline(pipeline),
            instance,
            pipeline_run=pipeline_run,
        )

    assert set(exc_info.value.step_keys) == {"nope.compute", "nuh_uh.compute"}

    assert re.match("Can not build subset plan from unknown steps", str(exc_info.value))


def test_using_file_system_for_subplan_missing_input():
    pipeline = define_inty_pipeline(using_file_system=True)

    instance = DagsterInstance.ephemeral()
    resolved_run_config = ResolvedRunConfig.build(
        pipeline,
    )
    execution_plan = ExecutionPlan.build(
        InMemoryPipeline(pipeline),
        resolved_run_config,
    )
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline, execution_plan=execution_plan
    )

    events = execute_plan(
        execution_plan.build_subset_plan(["add_one"], pipeline, resolved_run_config),
        InMemoryPipeline(pipeline),
        instance,
        pipeline_run=pipeline_run,
    )
    failures = [event for event in events if event.event_type_value == "STEP_FAILURE"]
    assert len(failures) == 1
    assert failures[0].step_key == "add_one"
    assert (
        "DagsterExecutionLoadInputError"
        in failures[0].event_specific_data.error.message
    )


def test_using_file_system_for_subplan_invalid_step():
    pipeline = define_inty_pipeline(using_file_system=True)

    instance = DagsterInstance.ephemeral()

    resolved_run_config = ResolvedRunConfig.build(
        pipeline,
    )
    execution_plan = ExecutionPlan.build(
        InMemoryPipeline(pipeline),
        resolved_run_config,
    )

    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline, execution_plan=execution_plan
    )

    with pytest.raises(DagsterExecutionStepNotFoundError):
        execute_plan(
            execution_plan.build_subset_plan(
                ["nope.compute"], pipeline, resolved_run_config
            ),
            InMemoryPipeline(pipeline),
            instance,
            pipeline_run=pipeline_run,
        )
