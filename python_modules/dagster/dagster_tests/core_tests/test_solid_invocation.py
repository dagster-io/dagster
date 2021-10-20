import asyncio
import re

import pytest
from dagster import (
    AssetKey,
    AssetMaterialization,
    DynamicOutput,
    DynamicOutputDefinition,
    Failure,
    Field,
    InputDefinition,
    Noneable,
    Nothing,
    Output,
    OutputDefinition,
    RetryRequested,
    Selector,
    build_op_context,
    build_solid_context,
    composite_solid,
    execute_solid,
    pipeline,
    resource,
    solid,
)
from dagster.core.errors import (
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvalidPropertyError,
    DagsterInvariantViolationError,
    DagsterResourceFunctionError,
    DagsterStepOutputNotFoundError,
    DagsterTypeCheckDidNotPass,
)


def test_solid_invocation_no_arg():
    @solid
    def basic_solid():
        return 5

    result = basic_solid()
    assert result == 5

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Compute function of solid 'basic_solid' has no context "
        "argument, but context was provided when invoking.",
    ):
        basic_solid(build_solid_context())

    # Ensure alias is accounted for in error message
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Compute function of solid 'aliased_basic_solid' has no context "
        "argument, but context was provided when invoking.",
    ):
        basic_solid.alias("aliased_basic_solid")(build_solid_context())

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Too many input arguments were provided for solid 'basic_solid'. This may be "
        "because an argument was provided for the context parameter, but no context parameter was "
        "defined for the solid.",
    ):
        basic_solid(None)

    # Ensure alias is accounted for in error message
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Too many input arguments were provided for solid 'aliased_basic_solid'. This may be "
        "because an argument was provided for the context parameter, but no context parameter was "
        "defined for the solid.",
    ):
        basic_solid.alias("aliased_basic_solid")(None)


def test_solid_invocation_none_arg():
    @solid
    def basic_solid(_):
        return 5

    result = basic_solid(None)
    assert result == 5


def test_solid_invocation_context_arg():
    @solid
    def basic_solid(context):
        context.log.info("yay")

    basic_solid(None)
    basic_solid(build_solid_context())
    basic_solid(context=None)
    basic_solid(context=build_solid_context())


def test_solid_invocation_empty_run_config():
    @solid
    def basic_solid(context):
        assert context.run_config is not None
        assert context.run_config == {"resources": {}}

    basic_solid(context=build_solid_context())


def test_solid_invocation_run_config_with_config():
    @solid(config_schema={"foo": str})
    def basic_solid(context):
        assert context.run_config
        assert context.run_config["solids"] == {"basic_solid": {"config": {"foo": "bar"}}}

    basic_solid(build_solid_context(solid_config={"foo": "bar"}))


def test_solid_invocation_out_of_order_input_defs():
    @solid(input_defs=[InputDefinition("x"), InputDefinition("y")])
    def check_correct_order(y, x):
        assert y == 6
        assert x == 5

    check_correct_order(6, 5)
    check_correct_order(x=5, y=6)
    check_correct_order(6, x=5)


def test_solid_invocation_with_resources():
    @solid(required_resource_keys={"foo"})
    def solid_requires_resources(context):
        assert context.resources.foo == "bar"
        return context.resources.foo

    # Ensure that a check invariant is raise when we attempt to invoke without context
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Compute function of solid 'solid_requires_resources' has context argument, but no "
        "context was provided when invoking.",
    ):
        solid_requires_resources()

    # Ensure that alias is accounted for in error message
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Compute function of solid 'aliased_solid_requires_resources' has context argument, but no "
        "context was provided when invoking.",
    ):
        solid_requires_resources.alias("aliased_solid_requires_resources")()

    # Ensure that error is raised when we attempt to invoke with a None context
    with pytest.raises(
        DagsterInvalidInvocationError,
        match='solid "solid_requires_resources" has required resources, but no context was '
        "provided.",
    ):
        solid_requires_resources(None)

    # Ensure that error is raised when we attempt to invoke with a context without the required
    # resource.
    context = build_solid_context()
    with pytest.raises(
        DagsterInvalidInvocationError,
        match='solid "solid_requires_resources" requires resource "foo", but no resource '
        "with that key was found on the context.",
    ):
        solid_requires_resources(context)

    context = build_solid_context(resources={"foo": "bar"})
    assert solid_requires_resources(context) == "bar"


def test_solid_invocation_with_cm_resource():
    teardown_log = []

    @resource
    def cm_resource(_):
        try:
            yield "foo"
        finally:
            teardown_log.append("collected")

    @solid(required_resource_keys={"cm_resource"})
    def solid_requires_cm_resource(context):
        return context.resources.cm_resource

    # Attempt to use solid context as fxn with cm resource should fail
    context = build_solid_context(resources={"cm_resource": cm_resource})
    with pytest.raises(DagsterInvariantViolationError):
        solid_requires_cm_resource(context)

    del context
    assert teardown_log == ["collected"]

    # Attempt to use solid context as cm with cm resource should succeed
    with build_solid_context(resources={"cm_resource": cm_resource}) as context:
        assert solid_requires_cm_resource(context) == "foo"

    assert teardown_log == ["collected", "collected"]


def test_solid_invocation_with_config():
    @solid(config_schema={"foo": str})
    def solid_requires_config(context):
        assert context.solid_config["foo"] == "bar"
        return 5

    # Ensure that error is raised when attempting to execute and no context is provided
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Compute function of solid 'solid_requires_config' has context argument, but no "
        "context was provided when invoking.",
    ):
        solid_requires_config()

    # Ensure that alias is accounted for in error message
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Compute function of solid 'aliased_solid_requires_config' has context argument, but no "
        "context was provided when invoking.",
    ):
        solid_requires_config.alias("aliased_solid_requires_config")()

    # Ensure that error is raised when we attempt to invoke with a None context
    with pytest.raises(
        DagsterInvalidInvocationError,
        match='solid "solid_requires_config" has required config schema, but no context was '
        "provided.",
    ):
        solid_requires_config(None)

    # Ensure that error is raised when context does not have the required config.
    context = build_solid_context()
    with pytest.raises(
        DagsterInvalidConfigError,
        match="Error in config for solid",
    ):
        solid_requires_config(context)

    # Ensure that error is raised when attempting to execute and no context is provided, even when
    # configured
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Compute function of solid 'configured_solid' has context argument, but no "
        "context was provided when invoking.",
    ):
        solid_requires_config.configured({"foo": "bar"}, name="configured_solid")()

    # Ensure that if you configure the solid, you can provide a none-context.
    result = solid_requires_config.configured({"foo": "bar"}, name="configured_solid")(None)
    assert result == 5

    result = solid_requires_config(build_solid_context(solid_config={"foo": "bar"}))
    assert result == 5


def test_solid_invocation_default_config():
    @solid(config_schema={"foo": Field(str, is_required=False, default_value="bar")})
    def solid_requires_config(context):
        assert context.solid_config["foo"] == "bar"
        return context.solid_config["foo"]

    assert solid_requires_config(None) == "bar"

    @solid(config_schema=Field(str, is_required=False, default_value="bar"))
    def solid_requires_config_val(context):
        assert context.solid_config == "bar"
        return context.solid_config

    assert solid_requires_config_val(None) == "bar"

    @solid(
        config_schema={
            "foo": Field(str, is_required=False, default_value="bar"),
            "baz": str,
        }
    )
    def solid_requires_config_partial(context):
        assert context.solid_config["foo"] == "bar"
        assert context.solid_config["baz"] == "bar"
        return context.solid_config["foo"] + context.solid_config["baz"]

    assert (
        solid_requires_config_partial(build_solid_context(solid_config={"baz": "bar"})) == "barbar"
    )


def test_solid_invocation_dict_config():
    @solid(config_schema=dict)
    def solid_requires_dict(context):
        assert context.solid_config == {"foo": "bar"}
        return context.solid_config

    assert solid_requires_dict(build_solid_context(solid_config={"foo": "bar"})) == {"foo": "bar"}

    @solid(config_schema=Noneable(dict))
    def solid_noneable_dict(context):
        return context.solid_config

    assert solid_noneable_dict(build_solid_context()) is None
    assert solid_noneable_dict(None) is None


def test_solid_invocation_kitchen_sink_config():
    @solid(
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
        return context.solid_config

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

    assert kitchen_sink(build_solid_context(solid_config=solid_config_one)) == solid_config_one


def test_solid_with_inputs():
    @solid
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
        match="Too many input arguments were provided for solid 'solid_with_inputs'",
    ):
        solid_with_inputs(5, 6, 7)

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Too many input arguments were provided for solid 'solid_with_inputs'",
    ):
        solid_with_inputs(5, 6, z=7)

    # Check for proper error when incorrect number of inputs is provided.
    with pytest.raises(
        DagsterInvalidInvocationError, match='No value provided for required input "y".'
    ):
        solid_with_inputs(5, x=5)


def test_failing_solid():
    @solid
    def solid_fails():
        raise Exception("Oh no!")

    with pytest.raises(
        Exception,
        match="Oh no!",
    ):
        solid_fails()


def test_attempted_invocation_in_composition():
    @solid
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
    @solid
    async def aio_solid():
        await asyncio.sleep(0.01)
        return "done"

    loop = asyncio.get_event_loop()
    assert loop.run_until_complete(aio_solid()) == "done"


def test_async_gen_invocation():
    @solid
    async def aio_gen():
        await asyncio.sleep(0.01)
        yield Output("done")

    async def get_results():
        res = []
        async for output in aio_gen():
            res.append(output)
        return res

    loop = asyncio.get_event_loop()
    output = loop.run_until_complete(get_results())[0]
    assert output.value == "done"


def test_multiple_outputs_iterator():
    @solid(output_defs=[OutputDefinition(int, name="1"), OutputDefinition(int, name="2")])
    def solid_multiple_outputs():
        yield Output(2, output_name="2")
        yield Output(1, output_name="1")

    # Ensure that solid works both with execute_solid and invocation
    result = execute_solid(solid_multiple_outputs)
    assert result.success

    outputs = list(solid_multiple_outputs())
    assert outputs[0].value == 2
    assert outputs[1].value == 1


def test_wrong_output():
    @solid
    def solid_wrong_output():
        return Output(5, output_name="wrong_name")

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            'Core compute for solid "solid_wrong_output" returned an output "wrong_name" that does '
            "not exist. The available outputs are ['result']"
        ),
    ):
        execute_solid(solid_wrong_output)

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            'Invocation of solid "solid_wrong_output" returned an output "wrong_name" that does '
            "not exist. The available outputs are ['result']"
        ),
    ):
        solid_wrong_output()


def test_optional_output_return():
    @solid(
        output_defs=[
            OutputDefinition(int, name="1", is_required=False),
            OutputDefinition(int, name="2"),
        ]
    )
    def solid_multiple_outputs_not_sent():
        return Output(2, output_name="2")

    assert solid_multiple_outputs_not_sent().value == 2


def test_optional_output_yielded():
    @solid(
        output_defs=[
            OutputDefinition(int, name="1", is_required=False),
            OutputDefinition(int, name="2"),
        ]
    )
    def solid_multiple_outputs_not_sent():
        yield Output(2, output_name="2")

    assert list(solid_multiple_outputs_not_sent())[0].value == 2


def test_optional_output_yielded_async():
    @solid(
        output_defs=[
            OutputDefinition(int, name="1", is_required=False),
            OutputDefinition(int, name="2"),
        ]
    )
    async def solid_multiple_outputs_not_sent():
        yield Output(2, output_name="2")

    async def get_results():
        res = []
        async for output in solid_multiple_outputs_not_sent():
            res.append(output)
        return res

    loop = asyncio.get_event_loop()
    output = loop.run_until_complete(get_results())[0]
    assert output.value == 2


def test_missing_required_output_generator():
    # Test missing required output from a generator solid
    @solid(output_defs=[OutputDefinition(int, name="1"), OutputDefinition(int, name="2")])
    def solid_multiple_outputs_not_sent():
        yield Output(2, output_name="2")

    with pytest.raises(
        DagsterStepOutputNotFoundError,
        match='Core compute for solid "solid_multiple_outputs_not_sent" did not return an output '
        'for non-optional output "1"',
    ):
        execute_solid(solid_multiple_outputs_not_sent)

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Invocation of solid 'solid_multiple_outputs_not_sent' did not return an output "
        "for non-optional output '1'",
    ):
        list(solid_multiple_outputs_not_sent())


def test_missing_required_output_generator_async():
    # Test missing required output from an async generator solid
    @solid(output_defs=[OutputDefinition(int, name="1"), OutputDefinition(int, name="2")])
    async def solid_multiple_outputs_not_sent():
        yield Output(2, output_name="2")

    with pytest.raises(
        DagsterStepOutputNotFoundError,
        match='Core compute for solid "solid_multiple_outputs_not_sent" did not return an output '
        'for non-optional output "1"',
    ):
        execute_solid(solid_multiple_outputs_not_sent)

    async def get_results():
        res = []
        async for output in solid_multiple_outputs_not_sent():
            res.append(output)
        return res

    loop = asyncio.get_event_loop()
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Invocation of solid 'solid_multiple_outputs_not_sent' did not return an output "
        "for non-optional output '1'",
    ):
        loop.run_until_complete(get_results())


def test_missing_required_output_return():
    @solid(output_defs=[OutputDefinition(int, name="1"), OutputDefinition(int, name="2")])
    def solid_multiple_outputs_not_sent():
        return Output(2, output_name="2")

    with pytest.raises(
        DagsterStepOutputNotFoundError,
        match='Core compute for solid "solid_multiple_outputs_not_sent" did not return an output '
        'for non-optional output "1"',
    ):
        execute_solid(solid_multiple_outputs_not_sent)

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Invocation of solid 'solid_multiple_outputs_not_sent' did not return an output "
        "for non-optional output '1'",
    ):
        solid_multiple_outputs_not_sent()


def test_output_sent_multiple_times():
    @solid(output_defs=[OutputDefinition(int, name="1")])
    def solid_yields_twice():
        yield Output(1, "1")
        yield Output(2, "1")

    with pytest.raises(
        DagsterInvariantViolationError,
        match='Compute for solid "solid_yields_twice" returned an output "1" multiple times',
    ):
        execute_solid(solid_yields_twice)

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Invocation of solid 'solid_yields_twice' yielded an output '1' multiple times",
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
        ("solid_handle", None),
        ("solid", None),
        ("get_step_execution_context", None),
    ],
)
def test_invalid_properties_on_context(property_or_method_name, val_to_pass):
    @solid
    def solid_fails_getting_property(context):
        result = getattr(context, property_or_method_name)
        # for the case where property_or_method_name is a method, getting an attribute won't cause
        # an error, but invoking the method should.
        result(val_to_pass) if val_to_pass else result()  # pylint: disable=expression-not-assigned

    with pytest.raises(DagsterInvalidPropertyError):
        solid_fails_getting_property(None)


def test_solid_retry_requested():
    @solid
    def solid_retries():
        raise RetryRequested()

    with pytest.raises(RetryRequested):
        solid_retries()


def test_solid_failure():
    @solid
    def solid_fails():
        raise Failure("oops")

    with pytest.raises(Failure, match="oops"):
        solid_fails()


def test_yielded_asset_materialization():
    @solid
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
    @solid(input_defs=[InputDefinition("x", dagster_type=int)])
    def solid_takes_input(x):
        return x + 1

    assert solid_takes_input(5) == 6

    with pytest.raises(
        DagsterTypeCheckDidNotPass,
        match='Description: Value "foo" of python type "str" must be a int.',
    ):
        solid_takes_input("foo")


def test_output_type_check():
    @solid(output_defs=[OutputDefinition(dagster_type=int)])
    def wrong_type():
        return "foo"

    with pytest.raises(
        DagsterTypeCheckDidNotPass,
        match='Description: Value "foo" of python type "str" must be a int.',
    ):
        wrong_type()


def test_pending_node_invocation():
    @solid
    def basic_solid_to_hook():
        return 5

    assert basic_solid_to_hook.with_hooks(set())() == 5

    @solid
    def basic_solid_with_tag(context):
        assert context.has_tag("foo")
        return context.get_tag("foo")

    assert basic_solid_with_tag.tag({"foo": "bar"})(None) == "bar"


def test_composite_solid_invocation_out_of_composition():
    @solid
    def basic_solid():
        return 5

    @composite_solid
    def composite():
        basic_solid()

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Attempted to call composite solid "
        "'composite' outside of a composition function. Invoking composite solids is only valid in a "
        "function decorated with @pipeline or @composite_solid.",
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


@solid
async def foo_async() -> str:
    return "bar"


def test_coroutine_asyncio_invocation():
    async def my_coroutine_test():
        result = await foo_async()
        assert result == "bar"

    loop = asyncio.get_event_loop()
    loop.run_until_complete(my_coroutine_test())


def test_solid_invocation_nothing_deps():
    @solid(input_defs=[InputDefinition("start", Nothing)])
    def nothing_dep():
        return 5

    # Ensure that providing the Nothing-dependency input throws an error
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Attempted to provide value for nothing input 'start'. Nothing dependencies are ignored "
        "when directly invoking solids.",
    ):
        nothing_dep(start="blah")

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Too many input arguments were provided for solid 'nothing_dep'. This may be because "
        "you attempted to provide a value for a nothing dependency. Nothing dependencies are "
        "ignored when directly invoking solids.",
    ):
        nothing_dep("blah")

    # Ensure that not providing nothing dependency also works.
    assert nothing_dep() == 5

    @solid(input_defs=[InputDefinition("x"), InputDefinition("y", Nothing), InputDefinition("z")])
    def sandwiched_nothing_dep(x, z):
        return x + z

    assert sandwiched_nothing_dep(5, 6) == 11

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Too many input arguments were provided for solid 'sandwiched_nothing_dep'. This may "
        "be because you attempted to provide a value for a nothing dependency. Nothing "
        "dependencies are ignored when directly invoking solids.",
    ):
        sandwiched_nothing_dep(5, 6, 7)


def test_dynamic_output_gen():
    @solid(
        output_defs=[
            DynamicOutputDefinition(name="a", is_required=False),
            OutputDefinition(name="b", is_required=False),
        ]
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
    @solid(
        output_defs=[
            DynamicOutputDefinition(name="a", is_required=False),
            OutputDefinition(name="b", is_required=False),
        ]
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

    loop = asyncio.get_event_loop()
    a1, a2, b = loop.run_until_complete(get_results())

    assert a1.value == 1
    assert a1.mapping_key == "1"
    assert a2.value == 2
    assert a2.mapping_key == "2"

    assert b.value == "foo"


def test_dynamic_output_non_gen():
    @solid(output_defs=[DynamicOutputDefinition(name="a", is_required=False)])
    def should_not_work():
        return DynamicOutput(value=1, mapping_key="1", output_name="a")

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Attempted to return a DynamicOutput from solid. DynamicOuts are only supported "
        "using yield syntax.",
    ):
        should_not_work()


def test_dynamic_output_async_non_gen():
    @solid(output_defs=[DynamicOutputDefinition(name="a", is_required=False)])
    def should_not_work():
        asyncio.sleep(0.01)
        return DynamicOutput(value=1, mapping_key="1", output_name="a")

    loop = asyncio.get_event_loop()
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Attempted to return a DynamicOutput from solid. DynamicOuts are only supported "
        "using yield syntax.",
    ):
        loop.run_until_complete(should_not_work())


def test_solid_invocation_with_bad_resources(capsys):
    @resource
    def bad_resource(_):
        if 1 == 1:
            raise Exception("oopsy daisy")
        yield "foo"

    @solid(required_resource_keys={"my_resource"})
    def solid_requires_resource(context):
        return context.resources.my_resource

    with pytest.raises(
        DagsterResourceFunctionError,
        match="Error executing resource_fn on ResourceDefinition my_resource",
    ):
        with build_solid_context(resources={"my_resource": bad_resource}) as context:
            assert solid_requires_resource(context) == "foo"

    captured = capsys.readouterr()
    # make sure there are no exceptions in the context destructor (__del__)
    assert "Exception ignored in" not in captured.err


@pytest.mark.parametrize("context_builder", [build_solid_context, build_op_context])
def test_build_context_with_resources_config(context_builder):
    @resource(config_schema=str)
    def my_resource(context):
        assert context.resource_config == "foo"

    @solid(required_resource_keys={"my_resource"})
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
