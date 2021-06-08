import asyncio
import re

import pytest
from dagster import (
    AssetKey,
    AssetMaterialization,
    Failure,
    Field,
    InputDefinition,
    Noneable,
    Output,
    OutputDefinition,
    RetryRequested,
    Selector,
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
        match='Solid "solid_requires_resources" has required resources, but no context was '
        "provided.",
    ):
        solid_requires_resources(None)

    # Ensure that error is raised when we attempt to invoke with a context without the required
    # resource.
    context = build_solid_context()
    with pytest.raises(
        DagsterInvalidInvocationError,
        match='Solid "solid_requires_resources" requires resource "foo", but no resource '
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
        match='Solid "solid_requires_config" has required config schema, but no context was '
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

    result = solid_requires_config(build_solid_context(config={"foo": "bar"}))
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

    assert solid_requires_config_partial(build_solid_context(config={"baz": "bar"})) == "barbar"


def test_solid_invocation_dict_config():
    @solid(config_schema=dict)
    def solid_requires_dict(context):
        assert context.solid_config == {"foo": "bar"}
        return context.solid_config

    assert solid_requires_dict(build_solid_context(config={"foo": "bar"})) == {"foo": "bar"}

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

    assert kitchen_sink(build_solid_context(config=solid_config_one)) == solid_config_one


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
        "Must pass the output from previous solid invocations or inputs to the composition "
        "function as inputs when invoking solids during composition."
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

    assert aio_solid() == "done"


def test_async_gen_invocation():
    @solid
    async def aio_gen():
        await asyncio.sleep(0.01)
        yield Output("done")

    assert aio_gen() == "done"


def test_multiple_outputs_iterator():
    @solid(output_defs=[OutputDefinition(int, name="1"), OutputDefinition(int, name="2")])
    def solid_multiple_outputs():
        yield Output(2, output_name="2")
        yield Output(1, output_name="1")

    # Ensure that solid works both with execute_solid and invocation
    result = execute_solid(solid_multiple_outputs)
    assert result.success

    output_one, output_two = solid_multiple_outputs()
    assert output_one == 1
    assert output_two == 2


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
            'Solid "solid_wrong_output" returned an output "wrong_name" that does '
            "not exist. The available outputs are ['result']"
        ),
    ):
        solid_wrong_output()

    # Ensure alias is accounted for in error message
    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape(
            'Solid "aliased_solid_wrong_output" returned an output "wrong_name" that does '
            "not exist. The available outputs are ['result']"
        ),
    ):
        solid_wrong_output.alias("aliased_solid_wrong_output")()


def test_output_not_sent():
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
        match='Solid "solid_multiple_outputs_not_sent" did not return an output '
        'for non-optional output "1"',
    ):
        solid_multiple_outputs_not_sent()

    # Ensure alias is accounted for in error message
    with pytest.raises(
        DagsterInvariantViolationError,
        match='Solid "aliased_solid_multiple_outputs_not_sent" did not return an output '
        'for non-optional output "1"',
    ):
        solid_multiple_outputs_not_sent.alias("aliased_solid_multiple_outputs_not_sent")()


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
        match="Solid 'solid_yields_twice' returned an output '1' multiple times",
    ):
        solid_yields_twice()

    # Ensure alias is accounted for in error message
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Solid 'aliased_solid_yields_twice' returned an output '1' multiple times",
    ):
        solid_yields_twice.alias("aliased_solid_yields_twice")()


@pytest.mark.parametrize(
    "property_or_method_name,val_to_pass",
    [
        ("pipeline_run", None),
        ("step_launcher", None),
        ("run_config", None),
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

    # Ensure that running without context works, and that asset
    # materializations are just ignored in this case.
    assert solid_yields_materialization(None) == 5

    context = build_solid_context()
    assert solid_yields_materialization(context) == 5
    materializations = context.asset_materializations
    assert len(materializations) == 2


def test_input_type_check():
    @solid(input_defs=[InputDefinition("x", dagster_type=int)])
    def solid_takes_input(x):
        return x + 1

    assert solid_takes_input(5) == 6

    with pytest.raises(DagsterTypeCheckDidNotPass):
        solid_takes_input("foo")


def test_output_type_check():
    @solid(output_defs=[OutputDefinition(dagster_type=int)])
    def wrong_type():
        return "foo"

    with pytest.raises(DagsterTypeCheckDidNotPass):
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
