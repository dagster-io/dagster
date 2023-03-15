# isort: skip_file
# pylint: disable=unused-argument,reimported

import requests

from dagster import DagsterType, In, Nothing, Out, op


class MockResponse:
    def json(self):
        return {}


class MockRequest:
    def get(self, _url):
        return MockResponse()


requests = MockRequest()

# start_op_marker


@op
def my_op():
    return "hello"


# end_op_marker


# start_configured_op_marker
@op(config_schema={"api_endpoint": str})
def my_configurable_op(context):
    api_endpoint = context.op_config["api_endpoint"]
    data = requests.get(f"{api_endpoint}/data").json()
    return data


# end_configured_op_marker

# start_input_op_marker


@op
def my_input_op(abc, xyz):
    pass


# end_input_op_marker


# start_typed_input_op_marker


MyDagsterType = DagsterType(
    type_check_fn=lambda _, value: value % 2 == 0, name="MyDagsterType"
)


@op(ins={"abc": In(dagster_type=MyDagsterType)})
def my_typed_input_op(abc):
    pass


# end_typed_input_op_marker


# start_output_op_marker


@op
def my_output_op():
    return 5


# end_output_op_marker

# start_multi_output_op_marker


@op(out={"first_output": Out(), "second_output": Out()})
def my_multi_output_op():
    return 5, 6


# end_multi_output_op_marker


# start_op_context_marker
@op(config_schema={"name": str})
def context_op(context):
    name = context.op_config["name"]
    context.log.info(f"My name is {name}")


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

    @op(name=name, ins=ins or {"start": In(Nothing)}, **kwargs)
    def my_inner_op(**kwargs):
        # Op logic here
        pass

    return my_inner_op


# end_op_factory_pattern_marker

# start_return_annotation
from dagster import op


@op
def return_annotation_op() -> int:
    return 5


# end_return_annotation
# start_tuple_return
from dagster import op
from typing import Tuple


@op(out={"int_output": Out(), "str_output": Out()})
def my_multiple_output_annotation_op() -> Tuple[int, str]:
    return (5, "foo")


# end_tuple_return

# start_single_output_tuple
from dagster import op
from typing import Tuple


@op
def my_single_tuple_output_op() -> Tuple[int, str]:
    return (5, "foo")  # Will be viewed as one output


# end_single_output_tuple
