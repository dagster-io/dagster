from dagster import DagsterType, In, Out, graph, job, op, root_input_manager
from dagster._core.storage.io_manager import IOManager, io_manager


def named_io_manager(storage_dict, name):
    @io_manager
    def my_io_manager(_):
        class MyIOManager(IOManager):
            def handle_output(self, context, obj):
                storage_dict[tuple(context.get_run_scoped_output_identifier())] = {
                    "value": obj,
                    "output_manager_name": name,
                }

            def load_input(self, context):
                result = storage_dict[
                    tuple(context.upstream_output.get_run_scoped_output_identifier())
                ]
                return {**result, "input_manager_name": name}

        return MyIOManager()

    return my_io_manager


def test_composite_solid_output():
    @op(out=Out(io_manager_key="inner_manager"))
    def my_op(_):
        return 5

    @op(
        ins={"x": In()},
        out=Out(io_manager_key="inner_manager"),
    )
    def my_op_takes_input(_, x):
        return x

    # Values ingested by inner_manager and outer_manager are stored in storage_dict
    storage_dict = {}

    # Only use the io managers on inner ops for handling inputs and storing outputs.

    @graph
    def my_graph():
        return my_op_takes_input(my_op())

    @job(resource_defs={"inner_manager": named_io_manager(storage_dict, "inner")})
    def my_job():
        my_graph()

    result = my_job.execute_in_process()
    assert result.success
    # Ensure that the IO manager used to store and load my_composite.my_solid_takes_input is the
    # manager of my_solid_takes_input, not my_composite.
    assert storage_dict[(result.run_id, "my_graph.my_op_takes_input", "result")]["value"] == {
        "value": 5,
        "output_manager_name": "inner",
        "input_manager_name": "inner",
    }


def test_composite_solid_upstream_output():
    # Only use the io managers on inner ops for loading downstream inputs.

    @op(out=Out(io_manager_key="inner_manager"))
    def my_op(_):
        return 5

    @graph
    def my_graph():
        return my_op()

    @op
    def downstream_op(_, input1):
        assert input1 == {
            "value": 5,
            "output_manager_name": "inner",
            "input_manager_name": "inner",
        }

    storage_dict = {}

    @job(resource_defs={"inner_manager": named_io_manager(storage_dict, "inner")})
    def my_job():
        downstream_op(my_graph())

    result = my_job.execute_in_process()
    assert result.success


def test_io_manager_config_inside_composite():
    stored_dict = {}

    @io_manager(output_config_schema={"output_suffix": str})
    def inner_manager(_):
        class MyHardcodedIOManager(IOManager):
            def handle_output(self, context, obj):
                keys = tuple(
                    context.get_run_scoped_output_identifier() + [context.config["output_suffix"]]
                )
                stored_dict[keys] = obj

            def load_input(self, context):
                keys = tuple(
                    context.upstream_output.get_run_scoped_output_identifier()
                    + [context.upstream_output.config["output_suffix"]]
                )
                return stored_dict[keys]

        return MyHardcodedIOManager()

    @op(out=Out(io_manager_key="inner_manager"))
    def my_op(_):
        return "hello"

    @op
    def my_op_takes_input(_, x):
        assert x == "hello"
        return x

    @graph
    def my_graph():
        return my_op_takes_input(my_op())

    @job(resource_defs={"inner_manager": inner_manager})
    def my_job():
        my_graph()

    result = my_job.execute_in_process(
        run_config={
            "ops": {
                "my_graph": {
                    "ops": {"my_op": {"outputs": {"result": {"output_suffix": "my_suffix"}}}},
                }
            }
        },
    )
    assert result.success
    assert result.output_for_node("my_graph.my_op") == "hello"
    assert stored_dict.get((result.run_id, "my_graph.my_op", "result", "my_suffix")) == "hello"


def test_inner_inputs_connected_to_outer_dependency():
    my_dagster_type = DagsterType(name="foo", type_check_fn=lambda _, _a: True)

    @op(ins={"data": In(my_dagster_type)})
    def inner_op(data):
        return data

    @graph
    def my_graph(data):
        return inner_op(data)

    @op
    def top_level_op():
        return "from top_level_op"

    @job
    def my_job():
        # inner_solid should be connected to top_level_solid
        my_graph(top_level_op())

    result = my_job.execute_in_process()
    assert result.success
    assert result.output_for_node("my_graph.inner_op") == "from top_level_op"


def test_inner_inputs_connected_to_outer_dependency_with_root_input_manager():
    called = {}

    @root_input_manager(input_config_schema={"test": str})
    def my_root(_):
        # should not reach
        called["my_root"] = True

    @op(ins={"data": In(dagster_type=str, root_manager_key="my_root")})
    def inner_op(_, data):
        return data

    @graph
    def my_graph(data: str):
        return inner_op(data)

    @op
    def top_level_op():
        return "from top_level_op"

    @job(resource_defs={"my_root": my_root})
    def my_job():
        # inner_solid should be connected to top_level_solid
        my_graph(top_level_op())

    result = my_job.execute_in_process()
    assert result.success
    assert result.output_for_node("my_graph.inner_op") == "from top_level_op"
    assert "my_root" not in called


def test_inner_inputs_connected_to_nested_outer_dependency():
    my_dagster_type = DagsterType(name="foo", type_check_fn=lambda _, _a: True)

    @op(ins={"data": In(my_dagster_type)})
    def inner_op(data):
        return data

    @graph
    def inner_graph(data_1):
        # source output handle should be top_level solid
        return inner_op(data_1)

    @graph
    def middle_graph(data_2):
        return inner_graph(data_2)

    @graph
    def outer_graph(data_3):
        return middle_graph(data_3)

    @op
    def top_level_op():
        return "from top_level_op"

    @job
    def my_job():
        # inner_solid should be connected to top_level_solid
        outer_graph(top_level_op())

    result = my_job.execute_in_process()
    assert result.success
    assert (
        result.output_for_node("outer_graph.middle_graph.inner_graph.inner_op")
        == "from top_level_op"
    )
