import asyncio
from datetime import datetime
from functools import partial

import pendulum
import pytest
from dagster import (
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    DailyPartitionsDefinition,
    DynamicOut,
    DynamicOutput,
    ExpectationResult,
    Failure,
    Field,
    In,
    MultiPartitionsDefinition,
    Noneable,
    Nothing,
    Out,
    Output,
    RetryRequested,
    Selector,
    StaticPartitionsDefinition,
    TimeWindow,
    asset,
    build_op_context,
    op,
    resource,
)
from dagster._core.definitions.decorators.graph_decorator import graph
from dagster._core.errors import (
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvalidPropertyError,
    DagsterInvariantViolationError,
    DagsterResourceFunctionError,
    DagsterStepOutputNotFoundError,
    DagsterTypeCheckDidNotPass,
)
from dagster._legacy import (
    pipeline,
)
from dagster._utils.test import wrap_op_in_graph_and_execute


def test_solid_invocation_no_arg():
    @op
    def basic_solid():
        return 5

    result = basic_solid()
    assert result == 5

    basic_solid(build_op_context())

    with pytest.raises(
        DagsterInvalidInvocationError,
        match=(
            "Too many input arguments were provided for op 'basic_solid'. This may be because an"
            " argument was provided for the context parameter, but no context parameter was defined"
            " for the op."
        ),
    ):
        basic_solid(None)

    # Ensure alias is accounted for in error message
    with pytest.raises(
        DagsterInvalidInvocationError,
        match=(
            "Too many input arguments were provided for op 'aliased_basic_solid'. This may be"
            " because an argument was provided for the context parameter, but no context parameter"
            " was defined for the op."
        ),
    ):
        basic_solid.alias("aliased_basic_solid")(None)


def test_solid_invocation_none_arg():
    @op
    def basic_solid(_):
        return 5

    result = basic_solid(None)
    assert result == 5


def test_solid_invocation_context_arg():
    @op
    def basic_solid(context):
        context.log.info("yay")

    basic_solid(None)
    basic_solid(build_op_context())
    basic_solid(context=None)
    basic_solid(context=build_op_context())


def test_solid_invocation_empty_run_config():
    @op
    def basic_solid(context):
        assert context.run_config is not None
        assert context.run_config == {"resources": {}}

    basic_solid(context=build_op_context())


def test_solid_invocation_run_config_with_config():
    @op(config_schema={"foo": str})
    def basic_solid(context):
        assert context.run_config
        assert context.run_config["ops"] == {"basic_solid": {"config": {"foo": "bar"}}}

    basic_solid(build_op_context(op_config={"foo": "bar"}))


def test_solid_invocation_out_of_order_input_defs():
    @op(ins={"x": In(), "y": In()})
    def check_correct_order(y, x):
        assert y == 6
        assert x == 5

    check_correct_order(6, 5)
    check_correct_order(x=5, y=6)
    check_correct_order(6, x=5)


def test_solid_invocation_with_resources():
    @op(required_resource_keys={"foo"})
    def solid_requires_resources(context):
        assert context.resources.foo == "bar"
        return context.resources.foo

    # Ensure that a check invariant is raise when we attempt to invoke without context
    with pytest.raises(
        DagsterInvalidInvocationError,
        match=(
            "Compute function of op 'solid_requires_resources' has context argument, but no "
            "context was provided when invoking."
        ),
    ):
        solid_requires_resources()

    # Ensure that alias is accounted for in error message
    with pytest.raises(
        DagsterInvalidInvocationError,
        match=(
            "Compute function of op 'aliased_solid_requires_resources' has context argument, but no"
            " context was provided when invoking."
        ),
    ):
        solid_requires_resources.alias("aliased_solid_requires_resources")()

    # Ensure that error is raised when we attempt to invoke with a None context
    with pytest.raises(
        DagsterInvalidInvocationError,
        match='op "solid_requires_resources" has required resources, but no context was provided.',
    ):
        solid_requires_resources(None)

    # Ensure that error is raised when we attempt to invoke with a context without the required
    # resource.
    context = build_op_context()
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'foo' required by op 'solid_requires_resources' was not provided",
    ):
        solid_requires_resources(context)

    context = build_op_context(resources={"foo": "bar"})
    assert solid_requires_resources(context) == "bar"


def test_solid_invocation_with_cm_resource():
    teardown_log = []

    @resource
    def cm_resource(_):
        try:
            yield "foo"
        finally:
            teardown_log.append("collected")

    @op(required_resource_keys={"cm_resource"})
    def solid_requires_cm_resource(context):
        return context.resources.cm_resource

    # Attempt to use solid context as fxn with cm resource should fail
    context = build_op_context(resources={"cm_resource": cm_resource})
    with pytest.raises(DagsterInvariantViolationError):
        solid_requires_cm_resource(context)

    del context
    assert teardown_log == ["collected"]

    # Attempt to use solid context as cm with cm resource should succeed
    with build_op_context(resources={"cm_resource": cm_resource}) as context:
        assert solid_requires_cm_resource(context) == "foo"

    assert teardown_log == ["collected", "collected"]


def test_solid_invocation_with_config():
    @op(config_schema={"foo": str})
    def solid_requires_config(context):
        assert context.op_config["foo"] == "bar"
        return 5

    # Ensure that error is raised when attempting to execute and no context is provided
    with pytest.raises(
        DagsterInvalidInvocationError,
        match=(
            "Compute function of op 'solid_requires_config' has context argument, but no "
            "context was provided when invoking."
        ),
    ):
        solid_requires_config()

    # Ensure that alias is accounted for in error message
    with pytest.raises(
        DagsterInvalidInvocationError,
        match=(
            "Compute function of op 'aliased_solid_requires_config' has context argument, but no "
            "context was provided when invoking."
        ),
    ):
        solid_requires_config.alias("aliased_solid_requires_config")()

    # Ensure that error is raised when we attempt to invoke with a None context
    with pytest.raises(
        DagsterInvalidInvocationError,
        match='op "solid_requires_config" has required config schema, but no context was provided.',
    ):
        solid_requires_config(None)

    # Ensure that error is raised when context does not have the required config.
    context = build_op_context()
    with pytest.raises(
        DagsterInvalidConfigError,
        match="Error in config for op",
    ):
        solid_requires_config(context)

    # Ensure that error is raised when attempting to execute and no context is provided, even when
    # configured
    with pytest.raises(
        DagsterInvalidInvocationError,
        match=(
            "Compute function of op 'configured_solid' has context argument, but no "
            "context was provided when invoking."
        ),
    ):
        solid_requires_config.configured({"foo": "bar"}, name="configured_solid")()

    # Ensure that if you configure the solid, you can provide a none-context.
    result = solid_requires_config.configured({"foo": "bar"}, name="configured_solid")(None)
    assert result == 5

    result = solid_requires_config(build_op_context(op_config={"foo": "bar"}))
    assert result == 5


def test_solid_invocation_default_config():
    @op(config_schema={"foo": Field(str, is_required=False, default_value="bar")})
    def solid_requires_config(context):
        assert context.op_config["foo"] == "bar"
        return context.op_config["foo"]

    assert solid_requires_config(None) == "bar"

    @op(config_schema=Field(str, is_required=False, default_value="bar"))
    def solid_requires_config_val(context):
        assert context.op_config == "bar"
        return context.op_config

    assert solid_requires_config_val(None) == "bar"

    @op(
        config_schema={
            "foo": Field(str, is_required=False, default_value="bar"),
            "baz": str,
        }
    )
    def solid_requires_config_partial(context):
        assert context.op_config["foo"] == "bar"
        assert context.op_config["baz"] == "bar"
        return context.op_config["foo"] + context.op_config["baz"]

    assert solid_requires_config_partial(build_op_context(op_config={"baz": "bar"})) == "barbar"


def test_solid_invocation_dict_config():
    @op(config_schema=dict)
    def solid_requires_dict(context):
        assert context.op_config == {"foo": "bar"}
        return context.op_config

    assert solid_requires_dict(build_op_context(op_config={"foo": "bar"})) == {"foo": "bar"}

    @op(config_schema=Noneable(dict))
    def solid_noneable_dict(context):
        return context.op_config

    assert solid_noneable_dict(build_op_context()) is None
    assert solid_noneable_dict(None) is None


def test_solid_invocation_kitchen_sink_config():
    @op(
        config_schema={
            "str_field": str,
            "int_field": int,
            "list_int": [int],
            "list_list_int": [[int]],
            "dict_field": {"a_string": str},
            "list_dict_field": [{"an_int": int}],
            "selector_of_things": Selector(
                {"select_list_dict_field": [{"an_int": int}], "select_int": int}
            ),
            "optional_list_of_optional_string": Noneable([Noneable(str)]),
        }
    )
    def kitchen_sink(context):
        return context.op_config

    solid_config_one = {
        "str_field": "kjf",
        "int_field": 2,
        "list_int": [3],
        "list_list_int": [[1], [2, 3]],
        "dict_field": {"a_string": "kdjfkd"},
        "list_dict_field": [{"an_int": 2}, {"an_int": 4}],
        "selector_of_things": {"select_int": 3},
        "optional_list_of_optional_string": ["foo", None],
    }

    assert kitchen_sink(build_op_context(op_config=solid_config_one)) == solid_config_one


def test_solid_with_inputs():
    @op
    def solid_with_inputs(x, y):
        assert x == 5
        assert y == 6
        return x + y

    assert solid_with_inputs(5, 6) == 11
    assert solid_with_inputs(x=5, y=6) == 11
    assert solid_with_inputs(5, y=6) == 11
    assert solid_with_inputs(y=6, x=5) == 11

    # Check for proper error when incorrect number of inputs is provided.
    with pytest.raises(
        DagsterInvalidInvocationError, match='No value provided for required input "y".'
    ):
        solid_with_inputs(5)

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Too many input arguments were provided for op 'solid_with_inputs'",
    ):
        solid_with_inputs(5, 6, 7)

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Too many input arguments were provided for op 'solid_with_inputs'",
    ):
        solid_with_inputs(5, 6, z=7)

    # Check for proper error when incorrect number of inputs is provided.
    with pytest.raises(
        DagsterInvalidInvocationError, match='No value provided for required input "y".'
    ):
        solid_with_inputs(5)


def test_failing_solid():
    @op
    def solid_fails():
        raise Exception("Oh no!")

    with pytest.raises(
        Exception,
        match="Oh no!",
    ):
        solid_fails()


def test_attempted_invocation_in_composition():
    @op
    def basic_solid(_x):
        pass

    msg = (
        "Must pass the output from previous node invocations or inputs to the composition "
        "function as inputs when invoking nodes during composition."
    )
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=msg,
    ):

        @pipeline
        def _pipeline_will_fail():
            basic_solid(5)

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=msg,
    ):

        @pipeline
        def _pipeline_will_fail_again():
            basic_solid(_x=5)


def test_async_solid():
    @op
    async def aio_solid():
        await asyncio.sleep(0.01)
        return "done"

    assert asyncio.run(aio_solid()) == "done"


def test_async_gen_invocation():
    @op
    async def aio_gen(_):
        await asyncio.sleep(0.01)
        yield Output("done")

    context = build_op_context()

    async def get_results():
        res = []
        async for output in aio_gen(context):
            res.append(output)
        return res

    output = asyncio.run(get_results())[0]
    assert output.value == "done"


def test_multiple_outputs_iterator():
    @op(out={"1": Out(int), "2": Out(int)})
    def solid_multiple_outputs():
        yield Output(2, output_name="2")
        yield Output(1, output_name="1")

    # Ensure that solid works both with execute_solid and invocation
    result = wrap_op_in_graph_and_execute(solid_multiple_outputs)
    assert result.success

    outputs = list(solid_multiple_outputs())
    assert outputs[0].value == 2
    assert outputs[1].value == 1


def test_wrong_output():
    @op
    def solid_wrong_output():
        return Output(5, output_name="wrong_name")

    with pytest.raises(
        DagsterInvariantViolationError,
        match="explicitly named 'wrong_name'",
    ):
        wrap_op_in_graph_and_execute(solid_wrong_output)

    with pytest.raises(
        DagsterInvariantViolationError,
        match="explicitly named 'wrong_name'",
    ):
        solid_wrong_output()


def test_optional_output_return():
    @op(
        out={
            "1": Out(int, is_required=False),
            "2": Out(int),
        }
    )
    def solid_multiple_outputs_not_sent():
        return Output(2, output_name="2")

    with pytest.raises(
        DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        solid_multiple_outputs_not_sent()

    with pytest.raises(
        DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        wrap_op_in_graph_and_execute(solid_multiple_outputs_not_sent)


def test_optional_output_yielded():
    @op(
        out={
            "1": Out(int, is_required=False),
            "2": Out(int),
        }
    )
    def solid_multiple_outputs_not_sent():
        yield Output(2, output_name="2")

    assert list(solid_multiple_outputs_not_sent())[0].value == 2


def test_optional_output_yielded_async():
    @op(
        out={
            "1": Out(int, is_required=False),
            "2": Out(int),
        }
    )
    async def solid_multiple_outputs_not_sent():
        yield Output(2, output_name="2")

    async def get_results():
        res = []
        async for output in solid_multiple_outputs_not_sent():
            res.append(output)
        return res

    output = asyncio.run(get_results())[0]
    assert output.value == 2


def test_missing_required_output_generator():
    # Test missing required output from a generator solid
    @op(
        out={
            "1": Out(int),
            "2": Out(int),
        }
    )
    def solid_multiple_outputs_not_sent():
        yield Output(2, output_name="2")

    with pytest.raises(
        DagsterStepOutputNotFoundError,
        match=(
            'Core compute for op "solid_multiple_outputs_not_sent" did not return an output '
            'for non-optional output "1"'
        ),
    ):
        wrap_op_in_graph_and_execute(solid_multiple_outputs_not_sent)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "Invocation of op 'solid_multiple_outputs_not_sent' did not return an output "
            "for non-optional output '1'"
        ),
    ):
        list(solid_multiple_outputs_not_sent())


def test_missing_required_output_generator_async():
    # Test missing required output from an async generator solid
    @op(
        out={
            "1": Out(int),
            "2": Out(int),
        }
    )
    async def solid_multiple_outputs_not_sent():
        yield Output(2, output_name="2")

    with pytest.raises(
        DagsterStepOutputNotFoundError,
        match=(
            'Core compute for op "solid_multiple_outputs_not_sent" did not return an output '
            'for non-optional output "1"'
        ),
    ):
        wrap_op_in_graph_and_execute(solid_multiple_outputs_not_sent)

    async def get_results():
        res = []
        async for output in solid_multiple_outputs_not_sent():
            res.append(output)
        return res

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "Invocation of op 'solid_multiple_outputs_not_sent' did not return an output "
            "for non-optional output '1'"
        ),
    ):
        asyncio.run(get_results())


def test_missing_required_output_return():
    @op(
        out={
            "1": Out(int),
            "2": Out(int),
        }
    )
    def solid_multiple_outputs_not_sent():
        return Output(2, output_name="2")

    with pytest.raises(
        DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        wrap_op_in_graph_and_execute(solid_multiple_outputs_not_sent)

    with pytest.raises(
        DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        solid_multiple_outputs_not_sent()


def test_output_sent_multiple_times():
    @op(
        out={
            "1": Out(int),
        }
    )
    def solid_yields_twice():
        yield Output(1, "1")
        yield Output(2, "1")

    with pytest.raises(
        DagsterInvariantViolationError,
        match='Compute for op "solid_yields_twice" returned an output "1" multiple times',
    ):
        wrap_op_in_graph_and_execute(solid_yields_twice)

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Invocation of op 'solid_yields_twice' yielded an output '1' multiple times",
    ):
        list(solid_yields_twice())


@pytest.mark.parametrize(
    "property_or_method_name,val_to_pass",
    [
        ("pipeline_run", None),
        ("step_launcher", None),
        ("pipeline_def", None),
        ("pipeline_name", None),
        ("mode_def", None),
        ("node_handle", None),
        ("solid", None),
        ("get_step_execution_context", None),
    ],
)
def test_invalid_properties_on_context(property_or_method_name, val_to_pass):
    @op
    def solid_fails_getting_property(context):
        result = getattr(context, property_or_method_name)
        # for the case where property_or_method_name is a method, getting an attribute won't cause
        # an error, but invoking the method should.
        result(val_to_pass) if val_to_pass else result()

    with pytest.raises(DagsterInvalidPropertyError):
        solid_fails_getting_property(None)


def test_solid_retry_requested():
    @op
    def solid_retries():
        raise RetryRequested()

    with pytest.raises(RetryRequested):
        solid_retries()


def test_solid_failure():
    @op
    def solid_fails():
        raise Failure("oops")

    with pytest.raises(Failure, match="oops"):
        solid_fails()


def test_yielded_asset_materialization():
    @op
    def solid_yields_materialization(_):
        yield AssetMaterialization(asset_key=AssetKey(["fake"]))
        yield Output(5)
        yield AssetMaterialization(asset_key=AssetKey(["fake2"]))

    events = list(solid_yields_materialization(None))
    outputs = [event for event in events if isinstance(event, Output)]
    assert outputs[0].value == 5
    materializations = [
        materialization
        for materialization in events
        if isinstance(materialization, AssetMaterialization)
    ]
    assert len(materializations) == 2


def test_input_type_check():
    @op(ins={"x": In(int)})
    def solid_takes_input(x):
        return x + 1

    assert solid_takes_input(5) == 6

    with pytest.raises(
        DagsterTypeCheckDidNotPass,
        match='Description: Value "foo" of python type "str" must be a int.',
    ):
        solid_takes_input("foo")


def test_output_type_check():
    @op(out=Out(dagster_type=int))
    def wrong_type():
        return "foo"

    with pytest.raises(
        DagsterTypeCheckDidNotPass,
        match='Description: Value "foo" of python type "str" must be a int.',
    ):
        wrong_type()


def test_pending_node_invocation():
    @op
    def basic_solid_to_hook():
        return 5

    assert basic_solid_to_hook.with_hooks(set())() == 5

    @op
    def basic_solid_with_tag(context):
        assert context.has_tag("foo")
        return context.get_tag("foo")

    assert basic_solid_with_tag.tag({"foo": "bar"})(None) == "bar"


def test_graph_invocation_out_of_composition():
    @op
    def basic_solid():
        return 5

    @graph
    def composite():
        basic_solid()

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "Attempted to call graph 'composite' outside of a composition function."
            " Invoking graphs is only valid in a function decorated with @job or"
            " @graph."
        ),
    ):
        composite()


def test_pipeline_invocation():
    @pipeline
    def basic_pipeline():
        pass

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Attempted to call pipeline "
        "'basic_pipeline' directly. Pipelines should be invoked by using an execution API function "
        r"\(e.g. `execute_pipeline`\).",
    ):
        basic_pipeline()


@op
async def foo_async() -> str:
    return "bar"


def test_coroutine_asyncio_invocation():
    async def my_coroutine_test():
        result = await foo_async()
        assert result == "bar"

    asyncio.run(my_coroutine_test())


def test_solid_invocation_nothing_deps():
    @op(ins={"start": In(Nothing)})
    def nothing_dep():
        return 5

    # Ensure that providing the Nothing-dependency input throws an error
    with pytest.raises(
        DagsterInvalidInvocationError,
        match=(
            "Attempted to provide value for nothing input 'start'. Nothing dependencies are ignored"
            " when directly invoking ops."
        ),
    ):
        nothing_dep(start="blah")

    with pytest.raises(
        DagsterInvalidInvocationError,
        match=(
            "Too many input arguments were provided for op 'nothing_dep'. This may be because "
            "you attempted to provide a value for a nothing dependency. Nothing dependencies are "
            "ignored when directly invoking ops."
        ),
    ):
        nothing_dep("blah")

    # Ensure that not providing nothing dependency also works.
    assert nothing_dep() == 5

    @op(
        ins={
            "x": In(),
            "y": In(Nothing),
            "z": In(),
        }
    )
    def sandwiched_nothing_dep(x, z):
        return x + z

    assert sandwiched_nothing_dep(5, 6) == 11

    with pytest.raises(
        DagsterInvalidInvocationError,
        match=(
            "Too many input arguments were provided for op 'sandwiched_nothing_dep'. This may "
            "be because you attempted to provide a value for a nothing dependency. Nothing "
            "dependencies are ignored when directly invoking ops."
        ),
    ):
        sandwiched_nothing_dep(5, 6, 7)


def test_dynamic_output_gen():
    @op(
        out={
            "a": DynamicOut(is_required=False),
            "b": Out(is_required=False),
        }
    )
    def my_dynamic():
        yield DynamicOutput(value=1, mapping_key="1", output_name="a")
        yield DynamicOutput(value=2, mapping_key="2", output_name="a")
        yield Output(value="foo", output_name="b")

    a1, a2, b = my_dynamic()
    assert a1.value == 1
    assert a1.mapping_key == "1"
    assert a2.value == 2
    assert a2.mapping_key == "2"

    assert b.value == "foo"


def test_dynamic_output_async_gen():
    @op(
        out={
            "a": DynamicOut(is_required=False),
            "b": Out(is_required=False),
        }
    )
    async def aio_gen():
        yield DynamicOutput(value=1, mapping_key="1", output_name="a")
        yield DynamicOutput(value=2, mapping_key="2", output_name="a")
        await asyncio.sleep(0.01)
        yield Output(value="foo", output_name="b")

    async def get_results():
        res = []
        async for output in aio_gen():
            res.append(output)
        return res

    a1, a2, b = asyncio.run(get_results())

    assert a1.value == 1
    assert a1.mapping_key == "1"
    assert a2.value == 2
    assert a2.mapping_key == "2"

    assert b.value == "foo"


def test_dynamic_output_non_gen():
    @op(
        out={
            "a": DynamicOut(is_required=False),
        }
    )
    def should_not_work():
        return DynamicOutput(value=1, mapping_key="1", output_name="a")

    with pytest.raises(
        DagsterInvariantViolationError,
        match="expected a list of DynamicOutput objects",
    ):
        should_not_work()

    with pytest.raises(
        DagsterInvariantViolationError,
        match="expected a list of DynamicOutput objects",
    ):
        wrap_op_in_graph_and_execute(should_not_work)


def test_dynamic_output_async_non_gen():
    @op(
        out={
            "a": DynamicOut(is_required=False),
        }
    )
    async def should_not_work():
        await asyncio.sleep(0.01)
        return DynamicOutput(value=1, mapping_key="1", output_name="a")

    with pytest.raises(
        DagsterInvariantViolationError,
        match="dynamic output 'a' expected a list of DynamicOutput objects",
    ):
        asyncio.run(should_not_work())

    with pytest.raises(Exception):
        wrap_op_in_graph_and_execute(should_not_work())


def test_solid_invocation_with_bad_resources(capsys):
    @resource
    def bad_resource(_):
        if 1 == 1:
            raise Exception("oopsy daisy")
        yield "foo"

    @op(required_resource_keys={"my_resource"})
    def solid_requires_resource(context):
        return context.resources.my_resource

    with pytest.raises(
        DagsterResourceFunctionError,
        match="Error executing resource_fn on ResourceDefinition my_resource",
    ):
        with build_op_context(resources={"my_resource": bad_resource}) as context:
            assert solid_requires_resource(context) == "foo"

    captured = capsys.readouterr()
    # make sure there are no exceptions in the context destructor (__del__)
    assert "Exception ignored in" not in captured.err


@pytest.mark.parametrize("context_builder", [build_op_context, build_op_context])
def test_build_context_with_resources_config(context_builder):
    @resource(config_schema=str)
    def my_resource(context):
        assert context.resource_config == "foo"

    @op(required_resource_keys={"my_resource"})
    def my_solid(context):
        assert context.run_config["resources"]["my_resource"] == {"config": "foo"}

    context = context_builder(
        resources={"my_resource": my_resource},
        resources_config={"my_resource": {"config": "foo"}},
    )

    my_solid(context)

    # bad resource config case

    with pytest.raises(
        DagsterInvalidConfigError,
        match='Received unexpected config entry "bad_resource" at the root.',
    ):
        context_builder(
            resources={"my_resource": my_resource},
            resources_config={"bad_resource": {"config": "foo"}},
        )


def test_logged_user_events():
    @op
    def logs_events(context):
        context.log_event(AssetMaterialization("first"))
        context.log_event(ExpectationResult(success=True))
        context.log_event(AssetObservation("fourth"))
        yield AssetMaterialization("fifth")
        yield Output("blah")

    context = build_op_context()
    list(logs_events(context))
    assert [type(event) for event in context.get_events()] == [
        AssetMaterialization,
        ExpectationResult,
        AssetObservation,
    ]


def test_add_output_metadata():
    @op(out={"out1": Out(), "out2": Out()})
    def the_op(context):
        context.add_output_metadata({"foo": "bar"}, output_name="out1")
        yield Output(value=1, output_name="out1")
        context.add_output_metadata({"bar": "baz"}, output_name="out2")
        yield Output(value=2, output_name="out2")

    context = build_op_context()
    events = list(the_op(context))
    assert len(events) == 2
    assert context.get_output_metadata("out1") == {"foo": "bar"}
    assert context.get_output_metadata("out2") == {"bar": "baz"}


def test_add_output_metadata_after_output():
    @op
    def the_op(context):
        yield Output(value=1)
        context.add_output_metadata({"foo": "bar"})

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "In op 'the_op', attempted to log output metadata for output 'result' which has already"
            " been yielded. Metadata must be logged before the output is yielded."
        ),
    ):
        list(the_op(build_op_context()))


def test_log_metadata_multiple_dynamic_outputs():
    @op(out={"out1": DynamicOut(), "out2": DynamicOut()})
    def the_op(context):
        context.add_output_metadata({"one": "one"}, output_name="out1", mapping_key="one")
        yield DynamicOutput(value=1, output_name="out1", mapping_key="one")
        context.add_output_metadata({"two": "two"}, output_name="out1", mapping_key="two")
        context.add_output_metadata({"three": "three"}, output_name="out2", mapping_key="three")
        yield DynamicOutput(value=2, output_name="out1", mapping_key="two")
        yield DynamicOutput(value=3, output_name="out2", mapping_key="three")
        context.add_output_metadata({"four": "four"}, output_name="out2", mapping_key="four")
        yield DynamicOutput(value=4, output_name="out2", mapping_key="four")

    context = build_op_context()

    events = list(the_op(context))
    assert len(events) == 4
    assert context.get_output_metadata("out1", mapping_key="one") == {"one": "one"}
    assert context.get_output_metadata("out1", mapping_key="two") == {"two": "two"}
    assert context.get_output_metadata("out2", mapping_key="three") == {"three": "three"}
    assert context.get_output_metadata("out2", mapping_key="four") == {"four": "four"}


def test_log_metadata_after_dynamic_output():
    @op(out=DynamicOut())
    def the_op(context):
        yield DynamicOutput(1, mapping_key="one")
        context.add_output_metadata({"foo": "bar"}, mapping_key="one")

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "In op 'the_op', attempted to log output metadata for output 'result' with mapping_key"
            " 'one' which has already been yielded. Metadata must be logged before the output is"
            " yielded."
        ),
    ):
        list(the_op(build_op_context()))


def test_kwarg_inputs():
    @op(ins={"the_in": In(str)})
    def the_op(**kwargs) -> str:
        return kwargs["the_in"] + "foo"

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="op 'the_op' has 0 positional inputs, but 1 positional inputs were provided.",
    ):
        the_op("bar")

    assert the_op(the_in="bar") == "barfoo"

    with pytest.raises(KeyError):
        the_op(bad_val="bar")

    @op(ins={"the_in": In(), "kwarg_in": In(), "kwarg_in_two": In()})
    def the_op_2(the_in, **kwargs):
        return the_in + kwargs["kwarg_in"] + kwargs["kwarg_in_two"]

    assert the_op_2("foo", kwarg_in="bar", kwarg_in_two="baz") == "foobarbaz"


def test_kwarg_inputs_context():
    context = build_op_context()

    @op(ins={"the_in": In(str)})
    def the_op(context, **kwargs) -> str:
        assert context
        return kwargs["the_in"] + "foo"

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="op 'the_op' has 0 positional inputs, but 1 positional inputs were provided.",
    ):
        the_op(context, "bar")

    assert the_op(context, the_in="bar") == "barfoo"

    with pytest.raises(KeyError):
        the_op(context, bad_val="bar")

    @op(ins={"the_in": In(), "kwarg_in": In(), "kwarg_in_two": In()})
    def the_op_2(context, the_in, **kwargs):
        assert context
        return the_in + kwargs["kwarg_in"] + kwargs["kwarg_in_two"]

    assert the_op_2(context, "foo", kwarg_in="bar", kwarg_in_two="baz") == "foobarbaz"


def test_default_kwarg_inputs():
    @op
    def the_op(x=1, y=2):
        return x + y

    assert the_op() == 3


def test_kwargs_via_partial_functools():
    def fake_func(foo, bar):
        return foo + bar

    new_func = partial(fake_func, foo=1, bar=2)

    new_op = op(name="new_func")(new_func)

    assert new_op() == 3


def test_get_mapping_key():
    context = build_op_context(mapping_key="the_key")

    assert context.get_mapping_key() == "the_key"  # Ensure unbound context has mapping key

    @op
    def basic_op(context):
        assert context.get_mapping_key() == "the_key"  # Ensure bound context has mapping key

    basic_op(context)


def test_required_resource_keys_no_context_invocation():
    @op(required_resource_keys={"foo"})
    def uses_resource_no_context():
        pass

    uses_resource_no_context()

    with pytest.raises(
        DagsterInvalidInvocationError,
        match=(
            "Too many input arguments were provided for op "
            "'uses_resource_no_context'. This may be because an argument was "
            "provided for the context parameter, but no context parameter was "
            "defined for the op."
        ),
    ):
        uses_resource_no_context(None)


def test_assets_def_invocation():
    @asset()
    def my_asset(context):
        assert context.assets_def == my_asset

    @op
    def non_asset_op(context):
        context.assets_def

    with build_op_context(
        partition_key="2023-02-02",
    ) as context:
        my_asset(context)

        with pytest.raises(DagsterInvalidPropertyError, match="does not have an assets definition"):
            non_asset_op(context)


def test_partitions_time_window_asset_invocation():
    partitions_def = DailyPartitionsDefinition(start_date=datetime(2023, 1, 1))

    @asset(
        partitions_def=partitions_def,
    )
    def partitioned_asset(context):
        start, end = context.asset_partitions_time_window_for_output()
        assert start == pendulum.instance(datetime(2023, 2, 2), tz=partitions_def.timezone)
        assert end == pendulum.instance(datetime(2023, 2, 3), tz=partitions_def.timezone)

    context = build_op_context(
        partition_key="2023-02-02",
    )
    partitioned_asset(context)


def test_multipartitioned_time_window_asset_invocation():
    partitions_def = MultiPartitionsDefinition(
        {
            "date": DailyPartitionsDefinition(start_date="2020-01-01"),
            "static": StaticPartitionsDefinition(["a", "b"]),
        }
    )

    @asset(partitions_def=partitions_def)
    def my_asset(context):
        time_window = TimeWindow(
            start=pendulum.instance(
                datetime(year=2020, month=1, day=1), tz=partitions_def.timezone
            ),
            end=pendulum.instance(datetime(year=2020, month=1, day=2), tz=partitions_def.timezone),
        )
        assert context.asset_partitions_time_window_for_output() == time_window
        return 1

    context = build_op_context(
        partition_key="2020-01-01|a",
    )
    my_asset(context)

    partitions_def = MultiPartitionsDefinition(
        {
            "static2": StaticPartitionsDefinition(["a", "b"]),
            "static": StaticPartitionsDefinition(["a", "b"]),
        }
    )

    @asset(partitions_def=partitions_def)
    def static_multipartitioned_asset(context):
        with pytest.raises(
            DagsterInvariantViolationError,
            match="with a single time dimension",
        ):
            context.asset_partitions_time_window_for_output()

    context = build_op_context(
        partition_key="a|a",
    )
    static_multipartitioned_asset(context)
