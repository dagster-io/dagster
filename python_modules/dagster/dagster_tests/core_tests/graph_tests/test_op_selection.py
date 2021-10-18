from dagster import ConfigMapping, DynamicOut, DynamicOutput, In, graph, op, root_input_manager
from dagster.core.events import DagsterEventType


@op
def return_one():
    return 1


@op
def return_two():
    return 2


@op
def adder(num1: int, num2: int):
    return num1 + num2


@op
def add_one(num: int):
    return num + 1


@graph
def do_it_all():
    add_one(adder(return_one(), return_two()))


def test_simple_op_selection_on_job_def():
    my_subset_job = do_it_all.to_job(op_selection=["*adder"])
    result = my_subset_job.execute_in_process()

    assert result.success

    executed_step_keys = [
        evt.step_key
        for evt in result.all_node_events
        if evt.event_type == DagsterEventType.STEP_SUCCESS
    ]
    assert len(executed_step_keys) == 3
    assert "add_one" not in [executed_step_keys]


def test_select_all_on_job_def():
    my_subset_job = do_it_all.to_job(op_selection=["*"])
    result = my_subset_job.execute_in_process()

    assert result.success

    executed_step_keys = [
        evt.step_key
        for evt in result.all_node_events
        if evt.event_type == DagsterEventType.STEP_SUCCESS
    ]
    assert len(executed_step_keys) == 4


def test_simple_op_selection_on_job_execution():
    my_job = do_it_all.to_job()
    result = my_job.execute_in_process(op_selection=["*adder"])

    assert result.success

    executed_step_keys = [
        evt.step_key
        for evt in result.all_node_events
        if evt.event_type == DagsterEventType.STEP_SUCCESS
    ]
    assert len(executed_step_keys) == 3
    assert "add_one" not in [executed_step_keys]


def test_simple_op_selection_on_subset_execution():
    my_subset_job = do_it_all.to_job(op_selection=["*adder"])
    # option 1 - overwrites op_selection
    result = my_subset_job.execute_in_process(op_selection=["*"])

    assert result.success

    executed_step_keys = [
        evt.step_key
        for evt in result.all_node_events
        if evt.event_type == DagsterEventType.STEP_SUCCESS
    ]
    assert len(executed_step_keys) == 3
    assert "add_one" not in [executed_step_keys]


def test_unselected_extra_config_input():
    @op
    def root(_):
        return "public.table_1"

    @op(config_schema={"some_config": str})
    def takes_input(_, input_table):
        return input_table

    @graph
    def full():
        takes_input(root())

    # Requires passing some config to the op to bypass the op block level optionality
    run_config = {"ops": {"takes_input": {"config": {"some_config": "a"}}}}

    full_job = full.to_job()
    assert full_job.execute_in_process(run_config=run_config).success

    # Subselected job shouldn't require the unselected solid's config
    assert full_job.execute_in_process(op_selection=["root"]).success
    # Should also be able to ignore the extra input config
    assert full_job.execute_in_process(run_config=run_config, op_selection=["root"]).success


def test_unsatisfied_input_use_config():
    @op
    def start(_, x):
        return x

    @op
    def end(_, x=1):
        return x

    @graph
    def testing():
        end(start())

    full_job = testing.to_job()

    result = full_job.execute_in_process(
        run_config={"ops": {"start": {"inputs": {"x": {"value": 4}}}}}
    )
    assert result.success
    assert result.output_for_node("end") == 4

    # test to ensure that if start is not being executed its input config is still allowed (and ignored)
    subset_result = full_job.execute_in_process(
        run_config={"ops": {"start": {"inputs": {"x": {"value": 4}}}}},
        op_selection=["end"],
    )
    assert subset_result.success
    assert subset_result.output_for_node("end") == 1

    # test to ensure that if the input is connected we will use the input value provided in config
    subset_result = full_job.execute_in_process(
        run_config={"ops": {"end": {"inputs": {"x": {"value": 4}}}}},
        op_selection=["end"],
    )
    assert subset_result.success
    assert subset_result.output_for_node("end") == 4


def test_unsatisfied_input_use_root_input_manager():
    @root_input_manager(input_config_schema=int)
    def config_io_man(context):
        return context.config

    @op(ins={"x": In(root_manager_key="my_loader")})
    def start(_, x):
        return x

    @op(ins={"x": In(root_manager_key="my_loader")})
    def end(_, x):
        return x

    @graph
    def testing_io():
        end(start())

    full_job = testing_io.to_job(resource_defs={"my_loader": config_io_man})
    result = full_job.execute_in_process(
        run_config={
            "ops": {"start": {"inputs": {"x": 4}}},
        },
    )
    assert result.success
    assert result.output_for_node("end") == 4

    # test to ensure that if start is not being executed its input config is still allowed (and ignored)
    subset_result = full_job.execute_in_process(
        run_config={
            "ops": {"end": {"inputs": {"x": 1}}},
        },
        op_selection=["end"],
    )
    assert subset_result.success
    assert subset_result.output_for_node("end") == 1


def test_op_selection_on_dynamic_orchestration():
    @op
    def num_range():
        return 3

    @op(out=DynamicOut())
    def emit(num: int = 2):
        for i in range(num):
            yield DynamicOutput(value=i, mapping_key=str(i))

    @op
    def emit_ten(_):
        return 10

    @op
    def multiply_by_two(context, y):
        context.log.info("multiply_by_two is returning " + str(y * 2))
        return y * 2

    @op
    def multiply_inputs(context, y, ten):
        context.log.info("multiply_inputs is returning " + str(y * ten))
        return y * ten

    @op
    def sum_numbers(_, nums):
        return sum(nums)

    @op
    def echo(_, x: int) -> int:
        return x

    @graph
    def dynamic_graph():
        numbers = emit(num_range())
        dynamic = numbers.map(lambda num: multiply_by_two(multiply_inputs(num, emit_ten())))
        n = sum_numbers(dynamic.collect())
        echo(n)  # test transitive downstream of collect

    full_job = dynamic_graph.to_job()
    result = full_job.execute_in_process()
    assert result.success
    assert result.output_for_node("echo") == 60

    result = full_job.execute_in_process(
        op_selection=["emit*", "emit_ten"],
    )
    assert result.success
    assert result.output_for_node("echo") == 20


def test_op_selection_on_alias():
    @graph
    def _aliased():
        add_one.alias("add_one_1")(return_one.alias("return_one_1")())
        add_one.alias("add_one_2")(return_one.alias("return_one_2")())

    full_job = _aliased.to_job()
    result = full_job.execute_in_process()
    assert result.success
    assert (
        len(
            [
                evt.step_key
                for evt in result.all_node_events
                if evt.event_type == DagsterEventType.STEP_SUCCESS
            ]
        )
        == 4
    )

    subsetted_job = _aliased.to_job(op_selection=["return_one_2*"])
    result_for_subset_def = subsetted_job.execute_in_process()
    assert result_for_subset_def.success
    assert (
        len(
            [
                evt.step_key
                for evt in result_for_subset_def.all_node_events
                if evt.event_type == DagsterEventType.STEP_SUCCESS
            ]
        )
        == 2
    )

    result_for_subset = subsetted_job.execute_in_process(op_selection=["return_one_2*"])
    assert result_for_subset.success
    assert (
        len(
            [
                evt.step_key
                for evt in result_for_subset.all_node_events
                if evt.event_type == DagsterEventType.STEP_SUCCESS
            ]
        )
        == 2
    )


def test_op_selection_with_config_mapping():
    def my_config_fn(val):
        config_val = {"config": {"foo": val["foo"]}}
        return {
            "ops": {
                "my_op": config_val,
                "my_other_op": config_val,
            }
        }

    @op
    def my_op(context):
        return context.op_config["foo"]

    @graph
    def my_graph():
        my_op()
        my_op.alias("my_other_op")()

    my_job = my_graph.to_job(config=ConfigMapping(my_config_fn))
    result = my_job.execute_in_process(run_config={"foo": "bar"})
    assert result.success
    assert result.output_for_node("my_op") == "bar"
    assert result.output_for_node("my_other_op") == "bar"

    subset_result = my_job.execute_in_process(
        run_config={"foo": "bar"}, op_selection=["my_other_op"]
    )
    assert subset_result.success
    assert subset_result.output_for_node("my_other_op") == "bar"
