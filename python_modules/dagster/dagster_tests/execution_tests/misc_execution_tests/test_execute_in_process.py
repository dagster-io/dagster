import dagster as dg
import pytest
from dagster._core.errors import DagsterMaxRetriesExceededError
from dagster._core.execution.context.op_execution_context import OpExecutionContext


def get_solids():
    @dg.op
    def emit_one():
        return 1

    @dg.op
    def add(x, y):
        return x + y

    return emit_one, add


def test_output_value():
    @dg.graph
    def a():
        get_solids()[0]()

    result = a.execute_in_process()

    assert result.success
    assert result.output_for_node("emit_one") == 1


def test_output_values():
    @dg.op(out={"a": dg.Out(), "b": dg.Out()})
    def two_outs():
        return 1, 2

    @dg.graph
    def a():
        two_outs()

    result = a.execute_in_process()

    assert result.success
    assert result.output_for_node("two_outs", "a") == 1
    assert result.output_for_node("two_outs", "b") == 2


def test_dynamic_output_values():
    @dg.op(out=dg.DynamicOut())
    def two_outs():
        yield dg.DynamicOutput(1, "a")
        yield dg.DynamicOutput(2, "b")

    @dg.op
    def add_one(x):
        return x + 1

    @dg.graph
    def a():
        two_outs().map(add_one)

    result = a.execute_in_process()

    assert result.success
    assert result.output_for_node("two_outs") == {"a": 1, "b": 2}
    assert result.output_for_node("add_one") == {"a": 2, "b": 3}


def test_execute_graph():
    emit_one, add = get_solids()

    @dg.graph
    def emit_two():
        return add(emit_one(), emit_one())

    @dg.graph
    def emit_three():
        return add(emit_two(), emit_one())

    result = emit_three.execute_in_process()

    assert result.success

    assert result.output_value() == 3

    assert result.output_for_node("add") == 3
    assert result.output_for_node("emit_two") == 2
    assert result.output_for_node("emit_one") == 1
    assert result.output_for_node("emit_two.emit_one") == 1
    assert result.output_for_node("emit_two.emit_one_2") == 1


def test_graph_with_required_resources():
    @dg.op(required_resource_keys={"a"})
    def basic_reqs(context):
        return context.resources.a

    @dg.graph
    def basic_graph():
        return basic_reqs()

    result = basic_graph.execute_in_process(resources={"a": "foo"})
    assert result.output_value() == "foo"

    @dg.resource
    def basic_resource():
        return "bar"

    result = basic_graph.execute_in_process(resources={"a": basic_resource})
    assert result.output_value() == "bar"


def test_executor_config_ignored_by_execute_in_process():
    # Ensure that execute_in_process is able to properly ignore provided executor config.
    @dg.op
    def my_op():
        return 0

    @dg.graph
    def my_graph():
        my_op()

    my_job = my_graph.to_job(
        config={"execution": {"config": {"multiprocess": {"max_concurrent": 5}}}}
    )

    result = my_job.execute_in_process()
    assert result.success


def test_output_for_node_composite():
    @dg.op(out={"foo": dg.Out()})
    def my_op():
        return 5

    @dg.graph(out={"bar": dg.GraphOut()})
    def my_graph():
        return my_op()

    @dg.graph(out={"baz": dg.GraphOut()})
    def my_top_graph():
        return my_graph()

    result = my_graph.execute_in_process()
    assert result.success
    assert result.output_for_node("my_op", "foo") == 5
    assert result.output_value("bar") == 5

    result = my_top_graph.execute_in_process()
    assert result.output_for_node("my_graph", "bar") == 5
    assert result.output_for_node("my_graph.my_op", "foo") == 5
    assert result.output_value("baz") == 5


def test_output_for_node_not_found():
    @dg.op
    def op_exists():
        return 5

    @dg.graph
    def basic():
        return op_exists()

    result = basic.execute_in_process()
    assert result.success

    with pytest.raises(dg.DagsterInvariantViolationError, match="name_doesnt_exist"):
        result.output_for_node("op_exists", "name_doesnt_exist")

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="Could not find top-level output 'name_doesnt_exist'",
    ):
        result.output_value("name_doesnt_exist")

    with pytest.raises(
        dg.DagsterInvariantViolationError, match="basic has no op named op_doesnt_exist"
    ):
        result.output_for_node("op_doesnt_exist")


def _get_step_successes(event_list):
    return [event for event in event_list if event.is_step_success]


def test_step_events_for_node():
    @dg.op
    def op_exists():
        return 5

    @dg.graph
    def basic():
        return op_exists()

    @dg.graph
    def nested():
        return basic()

    result = nested.execute_in_process()
    node_events = result.all_node_events
    assert len(_get_step_successes(node_events)) == 1

    basic_events = result.events_for_node("basic")
    assert len(_get_step_successes(basic_events)) == 1

    op_events = result.events_for_node("basic.op_exists")
    assert len(_get_step_successes(op_events)) == 1


def test_output_value_error():
    @dg.job
    def my_job():
        pass

    result = my_job.execute_in_process()

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="Attempted to retrieve top-level outputs for 'my_job', which has no outputs.",
    ):
        result.output_value()


def test_partitions_key():
    @dg.op
    def my_op(context):
        assert (
            context._step_execution_context.plan_data.dagster_run.tags["dagster/partition"]  # noqa: SLF001
            == "2020-01-01"
        )

    @dg.daily_partitioned_config(start_date="2020-01-01")
    def my_partitioned_config(_start, _end):
        return {}

    @dg.job(config=my_partitioned_config)
    def my_job():
        my_op()

    assert my_job.execute_in_process(partition_key="2020-01-01").success


def test_asset_materialization():
    @dg.op(out={})
    def my_op():
        yield dg.AssetMaterialization("abc")

    @dg.job
    def my_job():
        my_op()

    result = my_job.execute_in_process()
    assert result.asset_materializations_for_node("my_op") == [
        dg.AssetMaterialization(asset_key=dg.AssetKey(["abc"]))
    ]


def test_asset_observation():
    @dg.op(out={})
    def my_op():
        yield dg.AssetObservation("abc")

    @dg.job
    def my_job():
        my_op()

    result = my_job.execute_in_process()
    assert result.asset_observations_for_node("my_op") == [
        dg.AssetObservation(asset_key=dg.AssetKey(["abc"]))
    ]


def test_dagster_run():
    @dg.op
    def success_op():
        return True

    @dg.job
    def my_success_job():
        success_op()

    result = my_success_job.execute_in_process()
    assert result.success
    assert result.dagster_run.is_success

    @dg.op
    def fail_op():
        raise Exception

    @dg.job
    def my_failure_job():
        fail_op()

    result = my_failure_job.execute_in_process(raise_on_error=False)
    assert not result.success
    assert not result.dagster_run.is_success


def test_dynamic_output_for_node():
    @dg.op(out=dg.DynamicOut())
    def fanout():
        for i in range(3):
            yield dg.DynamicOutput(value=i, mapping_key=str(i))

    @dg.op(
        out={
            "output1": dg.Out(int),
            "output2": dg.Out(int),
        }
    )
    def return_as_tuple(x):
        yield dg.Output(value=x, output_name="output1")
        yield dg.Output(value=5, output_name="output2")

    @dg.job
    def myjob():
        fanout().map(return_as_tuple)

    # get result
    result = myjob.execute_in_process()

    # assertions
    assert result.output_for_node("return_as_tuple", "output1") == {
        "0": 0,
        "1": 1,
        "2": 2,
    }
    assert result.output_for_node("return_as_tuple", "output2") == {
        "0": 5,
        "1": 5,
        "2": 5,
    }


def test_execute_in_process_input_values():
    @dg.op
    def requires_input_op(x: int):
        return x + 1

    @dg.graph
    def requires_input_graph(x):
        return requires_input_op(x)

    result = requires_input_graph.alias("named_graph").execute_in_process(input_values={"x": 5})
    assert result.success
    assert result.output_value() == 6
    result = requires_input_graph.to_job().execute_in_process(input_values={"x": 5})
    assert result.success
    assert result.output_value() == 6


def test_retries_exceeded():
    called = []

    @dg.op
    def always_fail():
        exception = Exception("I have failed.")
        called.append("yes")
        raise dg.RetryRequested(max_retries=2) from exception

    @dg.graph
    def fail():
        always_fail()

    with pytest.raises(DagsterMaxRetriesExceededError, match="Exceeded max_retries of 2"):
        fail.execute_in_process()

    result = fail.execute_in_process(raise_on_error=False)
    assert not result.success
    assert (
        "Exception: I have failed"
        in result.filter_events(lambda evt: evt.is_step_failure)[
            0
        ].event_specific_data.error_display_string  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
    )


def test_execute_in_process_defaults_override():
    @dg.op
    def some_op(context):
        assert context.job_def.resource_defs["io_manager"] == dg.mem_io_manager

    @dg.graph
    def some_graph():
        some_op()

    # Ensure that from every execute_in_process entrypoint, the default io manager is overridden with mem_io_manager
    some_graph.execute_in_process()

    some_graph.to_job().execute_in_process()

    some_graph.alias("hello").execute_in_process()


from dagster_test.utils.definitions_execute_in_process import definitions_execute_job_in_process


def test_definitions_method():
    """Test definitions-based in process execution, which should have attached the repository."""

    @dg.op
    def some_op(context: OpExecutionContext):
        assert context.repository_def

    @dg.job
    def my_job():
        some_op()

    @dg.schedule(job=my_job, cron_schedule="0 0 * * *")
    def my_schedule():
        pass

    @dg.sensor(job=my_job)
    def my_sensor():
        pass

    result = definitions_execute_job_in_process(
        defs=dg.Definitions(jobs=[my_job], schedules=[my_schedule], sensors=[my_sensor]),
        job_name="my_job",
    )
    assert result.success
