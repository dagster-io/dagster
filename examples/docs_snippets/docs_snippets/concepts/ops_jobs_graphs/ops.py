# ruff: isort: skip_file


import requests

import dagster as dg


class MockResponse:
    def json(self):
        return {}


class MockRequest:
    def get(self, _url):
        return MockResponse()


requests = MockRequest()

# start_op_marker


@dg.op
def my_op():
    return "hello"


# end_op_marker


# start_configured_op_marker
import dagster as dg


class MyOpConfig(dg.Config):
    api_endpoint: str


@dg.op
def my_configurable_op(config: MyOpConfig):
    data = requests.get(f"{config.api_endpoint}/data").json()
    return data


# end_configured_op_marker


# start_input_op_marker
@dg.op
def my_input_op(abc, xyz):
    pass


# end_input_op_marker


# start_typed_input_op_marker
MyDagsterType = dg.DagsterType(
    type_check_fn=lambda _, value: value % 2 == 0, name="MyDagsterType"
)


@dg.op(ins={"abc": dg.In(dagster_type=MyDagsterType)})
def my_typed_input_op(abc):
    pass


# end_typed_input_op_marker


# start_output_op_marker
@dg.op
def my_output_op():
    return 5


# end_output_op_marker


# start_multi_output_op_marker
@dg.op(out={"first_output": dg.Out(), "second_output": dg.Out()})
def my_multi_output_op():
    return 5, 6


# end_multi_output_op_marker


# start_op_context_marker
@dg.op
def context_op(context: dg.OpExecutionContext):
    context.log.info(f"My run ID is {context.run_id}")


# end_op_context_marker


# start_op_factory_pattern_marker
def my_op_factory(
    name="default_name",
    ins=None,
    **kwargs,
):
    """Args:
        name (str): The name of the new op.
        ins (Dict[str, In]): Any Ins for the new op. Default: None.

    Returns:
        function: The new op.
    """

    @dg.op(name=name, ins=ins or {"start": dg.In(dg.Nothing)}, **kwargs)
    def my_inner_op(**kwargs):
        # Op logic here
        pass

    return my_inner_op


# end_op_factory_pattern_marker

# start_return_annotation
import dagster as dg


@dg.op
def return_annotation_op() -> int:
    return 5


# end_return_annotation
# start_tuple_return
import dagster as dg


@dg.op(out={"int_output": dg.Out(), "str_output": dg.Out()})
def my_multiple_output_annotation_op() -> tuple[int, str]:
    return (5, "foo")


# end_tuple_return

# start_single_output_tuple
import dagster as dg


@dg.op
def my_single_tuple_output_op() -> tuple[int, str]:
    return (5, "foo")  # Will be viewed as one output


# end_single_output_tuple
