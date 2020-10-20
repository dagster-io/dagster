import pytest
from dagster import (
    DagsterEventType,
    DagsterExecutionStepNotFoundError,
    DagsterStepOutputNotFoundError,
    DependencyDefinition,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
    lambda_solid,
    reconstructable,
)
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.execution.plan.objects import StepOutputHandle
from dagster.core.instance import DagsterInstance
from dagster.core.storage.intermediate_storage import build_fs_intermediate_storage


def define_inty_pipeline():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid(input_defs=[InputDefinition("num", Int)], output_def=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    @lambda_solid
    def user_throw_exception():
        raise Exception("whoops")

    pipeline = PipelineDefinition(
        name="basic_external_plan_execution",
        solid_defs=[return_one, add_one, user_throw_exception],
        dependencies={"add_one": {"num": DependencyDefinition("return_one")}},
    )
    return pipeline


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
    pipeline = define_inty_pipeline()

    run_config = {"storage": {"filesystem": {}}}

    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(pipeline, run_config=run_config,)
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline, execution_plan=execution_plan
    )
    assert execution_plan.get_step_by_key("return_one.compute")

    return_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(["return_one.compute"]),
            instance,
            run_config=run_config,
            pipeline_run=pipeline_run,
        )
    )

    intermediate_storage = build_fs_intermediate_storage(
        instance.intermediates_directory, pipeline_run.run_id
    )
    assert get_step_output(return_one_step_events, "return_one.compute")
    assert intermediate_storage.has_intermediate(None, StepOutputHandle("return_one.compute"))
    assert (
        intermediate_storage.get_intermediate(None, Int, StepOutputHandle("return_one.compute")).obj
        == 1
    )

    add_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(["add_one.compute"]),
            instance,
            run_config=run_config,
            pipeline_run=pipeline_run,
        )
    )

    assert get_step_output(add_one_step_events, "add_one.compute")
    assert intermediate_storage.has_intermediate(None, StepOutputHandle("add_one.compute"))
    assert (
        intermediate_storage.get_intermediate(None, Int, StepOutputHandle("add_one.compute")).obj
        == 2
    )


def test_using_intermediates_file_system_is_persistent():
    pipeline = define_inty_pipeline()

    run_config = {"intermediate_storage": {"filesystem": {}}}
    execution_plan = create_execution_plan(pipeline, run_config=run_config,)

    assert execution_plan.artifacts_persisted


def test_using_intermediates_file_system_for_subplan():
    pipeline = define_inty_pipeline()

    run_config = {"intermediate_storage": {"filesystem": {}}}

    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(pipeline, run_config=run_config,)
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline, execution_plan=execution_plan
    )
    assert execution_plan.get_step_by_key("return_one.compute")

    return_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(["return_one.compute"]),
            instance,
            run_config=run_config,
            pipeline_run=pipeline_run,
        )
    )

    intermediate_storage = build_fs_intermediate_storage(
        instance.intermediates_directory, pipeline_run.run_id
    )
    assert get_step_output(return_one_step_events, "return_one.compute")
    assert intermediate_storage.has_intermediate(None, StepOutputHandle("return_one.compute"))
    assert (
        intermediate_storage.get_intermediate(None, Int, StepOutputHandle("return_one.compute")).obj
        == 1
    )

    add_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(["add_one.compute"]),
            instance,
            run_config=run_config,
            pipeline_run=pipeline_run,
        )
    )

    assert get_step_output(add_one_step_events, "add_one.compute")
    assert intermediate_storage.has_intermediate(None, StepOutputHandle("add_one.compute"))
    assert (
        intermediate_storage.get_intermediate(None, Int, StepOutputHandle("add_one.compute")).obj
        == 2
    )


def test_using_intermediates_to_override():
    pipeline = define_inty_pipeline()

    run_config = {"storage": {"filesystem": {}}, "intermediate_storage": {"in_memory": {}}}

    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(pipeline, run_config=run_config,)
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline, execution_plan=execution_plan
    )
    assert execution_plan.get_step_by_key("return_one.compute")

    return_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(["return_one.compute"]),
            instance,
            run_config=run_config,
            pipeline_run=pipeline_run,
        )
    )

    intermediate_storage = build_fs_intermediate_storage(
        instance.intermediates_directory, pipeline_run.run_id
    )
    assert get_step_output(return_one_step_events, "return_one.compute")
    assert not intermediate_storage.has_intermediate(None, StepOutputHandle("return_one.compute"))


def test_using_file_system_for_subplan_multiprocessing():

    run_config = {"storage": {"filesystem": {}}}
    instance = DagsterInstance.local_temp()

    pipeline = reconstructable(define_inty_pipeline)

    execution_plan = create_execution_plan(pipeline, run_config=run_config)
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline.get_definition(), execution_plan=execution_plan
    )

    assert execution_plan.get_step_by_key("return_one.compute")

    return_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(["return_one.compute"]),
            instance,
            run_config=dict(run_config, execution={"multiprocess": {}}),
            pipeline_run=pipeline_run,
        )
    )

    intermediate_storage = build_fs_intermediate_storage(
        instance.intermediates_directory, pipeline_run.run_id
    )

    assert get_step_output(return_one_step_events, "return_one.compute")
    assert intermediate_storage.has_intermediate(None, StepOutputHandle("return_one.compute"))
    assert (
        intermediate_storage.get_intermediate(None, Int, StepOutputHandle("return_one.compute")).obj
        == 1
    )

    add_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(["add_one.compute"]),
            instance,
            run_config=dict(run_config, execution={"multiprocess": {}}),
            pipeline_run=pipeline_run,
        )
    )

    assert get_step_output(add_one_step_events, "add_one.compute")
    assert intermediate_storage.has_intermediate(None, StepOutputHandle("add_one.compute"))
    assert (
        intermediate_storage.get_intermediate(None, Int, StepOutputHandle("add_one.compute")).obj
        == 2
    )


def test_using_intermediate_file_system_for_subplan_multiprocessing():

    run_config = {"intermediate_storage": {"filesystem": {}}}
    instance = DagsterInstance.local_temp()

    pipeline = reconstructable(define_inty_pipeline)

    execution_plan = create_execution_plan(pipeline, run_config=run_config)
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline.get_definition(), execution_plan=execution_plan
    )

    assert execution_plan.get_step_by_key("return_one.compute")

    return_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(["return_one.compute"]),
            instance,
            run_config=dict(run_config, execution={"multiprocess": {}}),
            pipeline_run=pipeline_run,
        )
    )

    intermediate_storage = build_fs_intermediate_storage(
        instance.intermediates_directory, pipeline_run.run_id
    )

    assert get_step_output(return_one_step_events, "return_one.compute")
    assert intermediate_storage.has_intermediate(None, StepOutputHandle("return_one.compute"))
    assert (
        intermediate_storage.get_intermediate(None, Int, StepOutputHandle("return_one.compute")).obj
        == 1
    )

    add_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(["add_one.compute"]),
            instance,
            run_config=dict(run_config, execution={"multiprocess": {}}),
            pipeline_run=pipeline_run,
        )
    )

    assert get_step_output(add_one_step_events, "add_one.compute")
    assert intermediate_storage.has_intermediate(None, StepOutputHandle("add_one.compute"))
    assert (
        intermediate_storage.get_intermediate(None, Int, StepOutputHandle("add_one.compute")).obj
        == 2
    )


def test_execute_step_wrong_step_key():
    pipeline = define_inty_pipeline()
    instance = DagsterInstance.ephemeral()

    execution_plan = create_execution_plan(pipeline)
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline, execution_plan=execution_plan
    )

    with pytest.raises(DagsterExecutionStepNotFoundError) as exc_info:
        execute_plan(
            execution_plan.build_subset_plan(["nope"]), instance, pipeline_run=pipeline_run
        )

    assert exc_info.value.step_keys == ["nope"]

    assert str(exc_info.value) == "Execution plan does not contain step: nope"

    with pytest.raises(DagsterExecutionStepNotFoundError) as exc_info:
        execute_plan(
            execution_plan.build_subset_plan(["nope", "nuh_uh"]),
            instance,
            pipeline_run=pipeline_run,
        )

    assert exc_info.value.step_keys == ["nope", "nuh_uh"]

    assert str(exc_info.value) == "Execution plan does not contain steps: nope, nuh_uh"


def test_using_file_system_for_subplan_missing_input():
    pipeline = define_inty_pipeline()
    run_config = {"storage": {"filesystem": {}}}

    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(pipeline, run_config=run_config)
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline, execution_plan=execution_plan
    )

    with pytest.raises(DagsterStepOutputNotFoundError):
        execute_plan(
            execution_plan.build_subset_plan(["add_one.compute"]),
            instance,
            run_config=run_config,
            pipeline_run=pipeline_run,
        )


def test_using_file_system_for_subplan_invalid_step():
    pipeline = define_inty_pipeline()

    run_config = {"storage": {"filesystem": {}}}

    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(pipeline, run_config=run_config)
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline, execution_plan=execution_plan
    )

    with pytest.raises(DagsterExecutionStepNotFoundError):
        execute_plan(
            execution_plan.build_subset_plan(["nope"]),
            instance,
            run_config=run_config,
            pipeline_run=pipeline_run,
        )
