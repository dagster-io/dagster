# pylint: disable=unused-argument

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

MyDagsterType = DagsterType(type_check_fn=lambda _, value: value % 2 == 0, name="MyDagsterType")


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
def x_op(
    arg, name="default_name", ins=None, **kwargs,
):
    """
    Args:
        args (any): One or more arguments used to generate the nwe op
        name (str): The name of the new op.
        ins (Dict[str, In]): Any Ins for the new op. Default: None.

    Returns:
        function: The new op.
    """

    @op(name=name, ins=ins or {"start": In(Nothing)}, **kwargs)
    def _x_op(context):
        # Op logic here
        pass

    return _x_op


# end_op_factory_pattern_marker
