from dagster import DependencyDefinition, GraphDefinition, In, Int, Out, Output, op
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.execution.api import create_execution_plan, execute_plan
from dagster._core.instance import DagsterInstance


def define_two_int_pipeline():
    @op
    def return_one():
        return 1

    @op(ins={"num": In()})
    def add_one(num):
        return num + 1

    return GraphDefinition(
        name="pipeline_ints",
        node_defs=[return_one, add_one],
        dependencies={"add_one": {"num": DependencyDefinition("return_one")}},
    ).to_job()


def find_events(events, event_type=None):
    return [e for e in events if (not event_type or e.event_type_value == event_type)]


def test_execution_plan_simple_two_steps():
    job_def = define_two_int_pipeline()
    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(job_def)
    dagster_run = instance.create_run_for_job(job_def=job_def, execution_plan=execution_plan)

    assert isinstance(execution_plan.steps, list)
    assert len(execution_plan.steps) == 2

    assert execution_plan.get_step_by_key("return_one")
    assert execution_plan.get_step_by_key("add_one")

    events = execute_plan(
        execution_plan,
        InMemoryJob(job_def),
        dagster_run=dagster_run,
        instance=instance,
    )
    step_starts = find_events(events, event_type="STEP_START")
    assert len(step_starts) == 2
    step_successes = find_events(events, event_type="STEP_SUCCESS")
    assert len(step_successes) == 2

    output_events = find_events(events, event_type="STEP_OUTPUT")

    assert output_events[0].step_key == "return_one"
    assert output_events[0].is_successful_output

    assert output_events[1].step_key == "add_one"
    assert output_events[1].is_successful_output


def test_execution_plan_two_outputs():
    @op(
        out={
            "num_one": Out(
                Int,
            ),
            "num_two": Out(
                Int,
            ),
        }
    )
    def return_one_two(_context):
        yield Output(1, "num_one")
        yield Output(2, "num_two")

    job_def = GraphDefinition(name="return_one_two_pipeline", node_defs=[return_one_two]).to_job()

    execution_plan = create_execution_plan(job_def)

    instance = DagsterInstance.ephemeral()
    dagster_run = instance.create_run_for_job(job_def=job_def, execution_plan=execution_plan)
    events = execute_plan(
        execution_plan,
        InMemoryJob(job_def),
        dagster_run=dagster_run,
        instance=instance,
    )

    output_events = find_events(events, event_type="STEP_OUTPUT")
    assert output_events[0].step_key == "return_one_two"
    assert output_events[0].step_output_data.output_name == "num_one"
    assert output_events[1].step_key == "return_one_two"
    assert output_events[1].step_output_data.output_name == "num_two"


def test_reentrant_execute_plan():
    called = {}

    @op
    def has_tag(context):
        assert context.has_tag("foo")
        assert context.get_tag("foo") == "bar"
        called["yup"] = True

    job_def = GraphDefinition(name="has_tag_pipeline", node_defs=[has_tag]).to_job()
    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(job_def)
    dagster_run = instance.create_run_for_job(
        job_def=job_def, tags={"foo": "bar"}, execution_plan=execution_plan
    )
    execute_plan(
        execution_plan,
        InMemoryJob(job_def),
        dagster_run=dagster_run,
        instance=instance,
    )

    assert called["yup"]
