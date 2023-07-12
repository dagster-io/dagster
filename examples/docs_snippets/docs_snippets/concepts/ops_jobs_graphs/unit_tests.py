# ruff: isort: skip_file

from dagster import (
    AssetMaterialization,
    Config,
    DagsterEventType,
    ExpectationResult,
    ExecuteInProcessResult,
    OpExecutionContext,
    Output,
    Out,
    op,
    graph,
)


class AddOneConfig(Config):
    num: int = 1


class AddTwoConfig(Config):
    num: int = 1


@op
def add_one(config: AddOneConfig) -> int:
    return config.num + 1


@op
def add_two(config: AddTwoConfig) -> int:
    return config.num + 2


@op
def subtract(left: int, right: int) -> int:
    return left - right


@graph
def do_math():
    subtract(add_one(), add_two())


do_math_job = do_math.to_job()


@op(out={"a_num": Out(dagster_type=int)})
def emit_events_op():
    a_num = 2
    yield ExpectationResult(
        success=a_num > 0, label="positive", description="A num must be positive"
    )
    yield AssetMaterialization(
        asset_key="persisted_string",
        description="Let us pretend we persisted the string somewhere",
    )
    yield Output(value=a_num, output_name="a_num")


@graph
def emit_events():
    emit_events_op()


emit_events_job = emit_events.to_job()


# start_test_job_marker
def test_job():
    result = do_math_job.execute_in_process()

    # return type is ExecuteInProcessResult
    assert isinstance(result, ExecuteInProcessResult)
    assert result.success
    # inspect individual op result
    assert result.output_for_node("add_one") == 2
    assert result.output_for_node("add_two") == 3
    assert result.output_for_node("subtract") == -1


# end_test_job_marker


# start_invocation_op_marker
@op
def my_op_to_test():
    return 5


# end_invocation_op_marker


# start_test_op_marker
def test_op_with_invocation():
    assert my_op_to_test() == 5


# end_test_op_marker


# start_invocation_op_inputs_marker
@op
def my_op_with_inputs(x, y):
    return x + y


# end_invocation_op_inputs_marker


# start_test_op_with_inputs_marker
def test_inputs_op_with_invocation():
    assert my_op_with_inputs(5, 6) == 11


# end_test_op_with_inputs_marker


# start_op_requires_foo_marker
from dagster import ConfigurableResource


class FooResource(ConfigurableResource):
    my_string: str


@op
def op_requires_foo(foo: FooResource):
    return f"found {foo.my_string}"


# end_op_requires_foo_marker


# start_op_requires_config

from dagster import Config


class MyOpConfig(Config):
    my_int: int


@op
def op_requires_config(config: MyOpConfig):
    return config.my_int * 2


# end_op_requires_config

# start_op_invocation_config


def test_op_with_config():
    assert op_requires_config(MyOpConfig(my_int=5)) == 10


# end_op_invocation_config


# start_op_requires_context_marker


@op
def context_op(context: OpExecutionContext):
    context.log.info(f"My run ID is {context.run_id}")


# end_op_requires_context_marker

# start_test_op_with_resource_client

from dagster import ConfigurableResource
import mock


class Client:
    def __init__(self, api_key):
        self._api_key = api_key

    def query(self, body):
        ...


class MyClientResource(ConfigurableResource):
    api_key: str

    def get_client(self) -> Client:
        return Client(self.api_key)


@op
def my_client_op(client_resource: MyClientResource):
    return client_resource.get_client().query({"foo": "bar"})


def test_my_client_op():
    class FakeClient:
        def query(self, body):
            assert body == {"foo": "bar"}
            return {"baz": "qux"}

    mock_client_resource = mock.Mock()
    mock_client_resource.get_client.return_value = FakeClient()

    assert my_client_op(mock_client_resource) == {"baz": "qux"}


# end_test_op_with_resource_client

# start_op_invocation_context_marker


def test_op_with_context():
    context = build_op_context()
    context_op(context)


# end_op_invocation_context_marker

# start_test_op_resource_marker


def test_op_with_resource():
    assert op_requires_foo(FooResource(my_string="bar")) == "found bar"


# end_test_op_resource_marker

from dagster import resource


# start_test_job_with_config
from dagster import RunConfig


def test_job_with_config():
    result = do_math_job.execute_in_process(
        run_config=RunConfig(
            ops={
                "add_one": AddOneConfig(num=2),
                "add_two": AddTwoConfig(num=3),
            }
        )
    )

    assert result.success

    assert result.output_for_node("add_one") == 3
    assert result.output_for_node("add_two") == 5
    assert result.output_for_node("subtract") == -2


# end_test_job_with_config


# start_test_event_stream
def test_event_stream():
    job_result = emit_events_job.execute_in_process()

    assert job_result.success

    # when one op has multiple outputs, you need to specify output name
    assert job_result.output_for_node("emit_events_op", output_name="a_num") == 2

    events_for_step = job_result.events_for_node("emit_events_op")
    assert [se.event_type for se in events_for_step] == [
        DagsterEventType.STEP_START,
        DagsterEventType.STEP_EXPECTATION_RESULT,
        DagsterEventType.ASSET_MATERIALIZATION,
        DagsterEventType.STEP_OUTPUT,
        DagsterEventType.HANDLED_OUTPUT,
        DagsterEventType.STEP_SUCCESS,
    ]

    # ops communicate what they did via the event stream, viewable in tools (e.g. dagit)
    (
        _start,
        expectation_event,
        materialization_event,
        _num_output_event,
        _num_handled_output_operation,
        _success,
    ) = events_for_step

    # apologies for verboseness here! we can do better.
    expectation_result = expectation_event.event_specific_data.expectation_result
    assert isinstance(expectation_result, ExpectationResult)
    assert expectation_result.success
    assert expectation_result.label == "positive"

    materialization = materialization_event.event_specific_data.materialization
    assert isinstance(materialization, AssetMaterialization)
    assert materialization.label == "persisted_string"


# end_test_event_stream

# start_test_basic_asset
from dagster import asset


@asset
def basic_asset():
    return 5


# An example unit test for basic_asset.
def test_basic_asset():
    assert basic_asset() == 5


# end_test_basic_asset

# start_test_input_asset
from dagster import asset


@asset
def asset_with_inputs(x, y):
    return x + y


# An example unit test for asset_with_inputs.
def test_asset_with_inputs():
    assert asset_with_inputs(5, 6) == 11


# end_test_input_asset


# start_test_resource_asset
from dagster import asset, ConfigurableResource, build_op_context, with_resources


class BarResource(ConfigurableResource):
    my_string: str


@asset
def asset_requires_bar(bar: BarResource) -> str:
    return bar.my_string


def test_asset_requires_bar():
    result = asset_requires_bar(bar=BarResource(my_string="bar"))
    ...


# end_test_resource_asset


# start_test_config_asset
from dagster import asset, Config, build_op_context


class MyAssetConfig(Config):
    my_string: str


@asset
def asset_requires_config(config: MyAssetConfig) -> str:
    return config.my_string


def test_asset_requires_config():
    result = asset_requires_config(config=MyAssetConfig(my_string="foo"))
    ...


# end_test_config_asset


def get_data_from_source():
    pass


def extract_structured_data(_):
    pass


# start_materialize_asset
from dagster import asset, materialize_to_memory


@asset
def data_source():
    return get_data_from_source()


@asset
def structured_data(data_source):
    return extract_structured_data(data_source)


# An example unit test using materialize_to_memory
def test_data_assets():
    result = materialize_to_memory([data_source, structured_data])
    assert result.success
    # Materialized objects can be accessed in terms of the underlying op
    materialized_data = result.output_for_node("structured_data")
    ...


# end_materialize_asset


# start_materialize_resources
from dagster import asset, materialize_to_memory, ConfigurableResource
import mock


class MyServiceResource(ConfigurableResource):
    ...


@asset
def asset_requires_service(service: MyServiceResource):
    ...


@asset
def other_asset_requires_service(service: MyServiceResource):
    ...


def test_assets_require_service():
    # Mock objects can be provided directly.
    result = materialize_to_memory(
        [asset_requires_service, other_asset_requires_service],
        resources={"service": mock.MagicMock()},
    )
    assert result.success
    ...


# end_materialize_resources
