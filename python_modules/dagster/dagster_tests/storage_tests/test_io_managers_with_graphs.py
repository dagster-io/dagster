import dagster as dg


def named_io_manager(storage_dict, name):
    @dg.io_manager
    def my_io_manager(_):
        class MyIOManager(dg.IOManager):
            def handle_output(self, context, obj):
                storage_dict[tuple(context.get_run_scoped_output_identifier())] = {
                    "value": obj,
                    "output_manager_name": name,
                }

            def load_input(self, context):
                result = storage_dict[
                    tuple(context.upstream_output.get_run_scoped_output_identifier())  # pyright: ignore[reportOptionalMemberAccess]
                ]
                return {**result, "input_manager_name": name}

        return MyIOManager()

    return my_io_manager


def test_graph_output():
    @dg.op(out=dg.Out(io_manager_key="inner_manager"))
    def my_op(_):
        return 5

    @dg.op(
        ins={"x": dg.In()},
        out=dg.Out(io_manager_key="inner_manager"),
    )
    def my_op_takes_input(_, x):
        return x

    # Values ingested by inner_manager and outer_manager are stored in storage_dict
    storage_dict = {}

    # Only use the io managers on inner ops for handling inputs and storing outputs.

    @dg.graph
    def my_graph():
        return my_op_takes_input(my_op())

    @dg.job(resource_defs={"inner_manager": named_io_manager(storage_dict, "inner")})
    def my_job():
        my_graph()

    result = my_job.execute_in_process()
    assert result.success
    # Ensure that the IO manager used to store and load my_composite.my_op_takes_input is the
    # manager of my_op_takes_input, not my_composite.
    assert storage_dict[(result.run_id, "my_graph.my_op_takes_input", "result")]["value"] == {
        "value": 5,
        "output_manager_name": "inner",
        "input_manager_name": "inner",
    }


def test_graph_upstream_output():
    # Only use the io managers on inner ops for loading downstream inputs.

    @dg.op(out=dg.Out(io_manager_key="inner_manager"))
    def my_op(_):
        return 5

    @dg.graph
    def my_graph():
        return my_op()

    @dg.op
    def downstream_op(_, input1):
        assert input1 == {
            "value": 5,
            "output_manager_name": "inner",
            "input_manager_name": "inner",
        }

    storage_dict = {}

    @dg.job(resource_defs={"inner_manager": named_io_manager(storage_dict, "inner")})
    def my_job():
        downstream_op(my_graph())

    result = my_job.execute_in_process()
    assert result.success


def test_io_manager_config_inside_composite():
    stored_dict = {}

    @dg.io_manager(output_config_schema={"output_suffix": str})
    def inner_manager(_):
        class MyHardcodedIOManager(dg.IOManager):
            def handle_output(self, context, obj):
                keys = tuple(
                    context.get_run_scoped_output_identifier() + [context.config["output_suffix"]]  # pyright: ignore[reportOperatorIssue]
                )
                stored_dict[keys] = obj

            def load_input(self, context):
                keys = tuple(
                    context.upstream_output.get_run_scoped_output_identifier()  # pyright: ignore[reportOptionalMemberAccess]
                    + [context.upstream_output.config["output_suffix"]]  # type: ignore
                )
                return stored_dict[keys]

        return MyHardcodedIOManager()

    @dg.op(out=dg.Out(io_manager_key="inner_manager"))
    def my_op(_):
        return "hello"

    @dg.op
    def my_op_takes_input(_, x):
        assert x == "hello"
        return x

    @dg.graph
    def my_graph():
        return my_op_takes_input(my_op())

    @dg.job(resource_defs={"inner_manager": inner_manager})
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
    my_dagster_type = dg.DagsterType(name="foo", type_check_fn=lambda _, _a: True)

    @dg.op(ins={"data": dg.In(my_dagster_type)})
    def inner_op(data):
        return data

    @dg.graph
    def my_graph(data):
        return inner_op(data)

    @dg.op
    def top_level_op():
        return "from top_level_op"

    @dg.job
    def my_job():
        # inner_op should be connected to top_level_op
        my_graph(top_level_op())

    result = my_job.execute_in_process()
    assert result.success
    assert result.output_for_node("my_graph.inner_op") == "from top_level_op"


def test_inner_inputs_connected_to_nested_outer_dependency():
    my_dagster_type = dg.DagsterType(name="foo", type_check_fn=lambda _, _a: True)

    @dg.op(ins={"data": dg.In(my_dagster_type)})
    def inner_op(data):
        return data

    @dg.graph
    def inner_graph(data_1):
        # source output handle should be top_level op
        return inner_op(data_1)

    @dg.graph
    def middle_graph(data_2):
        return inner_graph(data_2)

    @dg.graph
    def outer_graph(data_3):
        return middle_graph(data_3)

    @dg.op
    def top_level_op():
        return "from top_level_op"

    @dg.job
    def my_job():
        # inner_op should be connected to top_level_op
        outer_graph(top_level_op())

    result = my_job.execute_in_process()
    assert result.success
    assert (
        result.output_for_node("outer_graph.middle_graph.inner_graph.inner_op")
        == "from top_level_op"
    )
