import asyncio
from datetime import datetime
from functools import partial

import dagster as dg
import pytest
from dagster._core.definitions.partitions.utils import get_time_partitions_def
from dagster._core.errors import DagsterInvalidPropertyError
from dagster._core.execution.context.compute import AssetExecutionContext, OpExecutionContext
from dagster._core.execution.context.invocation import DirectOpExecutionContext
from dagster._time import create_datetime
from dagster._utils.test import wrap_op_in_graph_and_execute


def test_op_invocation_no_arg():
    @dg.op
    def basic_op():
        return 5

    result = basic_op()
    assert result == 5

    basic_op(dg.build_op_context())

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            "Too many input arguments were provided for op 'basic_op'. This may be because an"
            " argument was provided for the context parameter, but no context parameter was defined"
            " for the op."
        ),
    ):
        basic_op(None)

    # Ensure alias is accounted for in error message
    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            "Too many input arguments were provided for op 'aliased_basic_op'. This may be because"
            " an argument was provided for the context parameter, but no context parameter was"
            " defined for the op."
        ),
    ):
        basic_op.alias("aliased_basic_op")(None)


def test_op_invocation_none_arg():
    @dg.op
    def basic_op(_):
        return 5

    result = basic_op(None)
    assert result == 5


def test_op_invocation_lifecycle():
    @dg.op
    def basic_op(context):
        return 5

    with dg.build_op_context() as context:
        pass

    # Verify dispose was called on the instance
    assert context.instance.run_storage._held_conn.closed  # noqa  # pyright: ignore[reportAttributeAccessIssue]


def test_op_invocation_context_arg():
    @dg.op
    def basic_op(context):
        context.log.info("yay")

    basic_op(None)
    basic_op(dg.build_op_context())
    basic_op(context=None)
    basic_op(context=dg.build_op_context())


def test_op_invocation_empty_run_config():
    @dg.op
    def basic_op(context):
        assert context.run_config is not None
        assert context.run_config == {"resources": {}}

    basic_op(context=dg.build_op_context())


def test_op_invocation_run_config_with_config():
    @dg.op(config_schema={"foo": str})
    def basic_op(context):
        assert context.run_config
        assert context.run_config["ops"] == {"basic_op": {"config": {"foo": "bar"}}}

    basic_op(dg.build_op_context(op_config={"foo": "bar"}))


def test_op_invocation_out_of_order_input_defs():
    @dg.op(ins={"x": dg.In(), "y": dg.In()})
    def check_correct_order(y, x):
        assert y == 6
        assert x == 5

    check_correct_order(6, 5)
    check_correct_order(x=5, y=6)
    check_correct_order(6, x=5)


def test_op_invocation_with_resources():
    @dg.op(required_resource_keys={"foo"})
    def op_requires_resources(context):
        assert context.resources.foo == "bar"
        return context.resources.foo

    # Ensure that a check invariant is raise when we attempt to invoke without context
    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            "Decorated function 'op_requires_resources' has context argument, but no "
            "context was provided when invoking."
        ),
    ):
        op_requires_resources()

    # alias still refers back to decorated function
    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            "Decorated function 'op_requires_resources' has context argument, but no "
            "context was provided when invoking."
        ),
    ):
        op_requires_resources.alias("aliased_op_requires_resources")()

    # Ensure that error is raised when we attempt to invoke with a context without the required
    # resource.
    context = dg.build_op_context()
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="resource with key 'foo' required by op 'op_requires_resources' was not provided",
    ):
        op_requires_resources(context)

    context = dg.build_op_context(resources={"foo": "bar"})
    assert op_requires_resources(context) == "bar"


def test_op_invocation_with_cm_resource():
    teardown_log = []

    @dg.resource
    def cm_resource(_):
        try:
            yield "foo"
        finally:
            teardown_log.append("collected")

    @dg.op(required_resource_keys={"cm_resource"})
    def op_requires_cm_resource(context):
        return context.resources.cm_resource

    # Attempt to use op context as fxn with cm resource should fail
    context = dg.build_op_context(resources={"cm_resource": cm_resource})
    with pytest.raises(dg.DagsterInvariantViolationError):
        op_requires_cm_resource(context)

    del context
    assert teardown_log == ["collected"]

    # Attempt to use op context as cm with cm resource should succeed
    with dg.build_op_context(resources={"cm_resource": cm_resource}) as context:
        assert op_requires_cm_resource(context) == "foo"

    assert teardown_log == ["collected", "collected"]


def test_op_invocation_with_config():
    @dg.op(config_schema={"foo": str})
    def op_requires_config(context):
        assert context.op_config["foo"] == "bar"
        return 5

    # Ensure that error is raised when attempting to execute and no context is provided
    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            "Decorated function 'op_requires_config' has context argument, but no "
            "context was provided when invoking."
        ),
    ):
        op_requires_config()

    # alias still refers back to decorated function
    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            "Decorated function 'op_requires_config' has context argument, but no "
            "context was provided when invoking."
        ),
    ):
        op_requires_config.alias("aliased_op_requires_config")()

    # Ensure that error is raised when we attempt to invoke with a None context
    with pytest.raises(
        dg.DagsterInvalidConfigError,
        match="Error in config for op",
    ):
        op_requires_config(None)

    # Ensure that error is raised when context does not have the required config.
    context = dg.build_op_context()
    with pytest.raises(
        dg.DagsterInvalidConfigError,
        match="Error in config for op",
    ):
        op_requires_config(context)

    # Ensure that error is raised when attempting to execute and no context is provided, even when
    # configured
    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            "Decorated function 'op_requires_config' has context argument, but no "
            "context was provided when invoking."
        ),
    ):
        op_requires_config.configured({"foo": "bar"}, name="configured_op")()

    # Ensure that if you configure the op, you can provide a none-context.
    result = op_requires_config.configured({"foo": "bar"}, name="configured_op")(None)
    assert result == 5

    result = op_requires_config(dg.build_op_context(op_config={"foo": "bar"}))
    assert result == 5


def test_op_invocation_default_config():
    @dg.op(config_schema={"foo": dg.Field(str, is_required=False, default_value="bar")})
    def op_requires_config(context):
        assert context.op_config["foo"] == "bar"
        return context.op_config["foo"]

    assert op_requires_config(None) == "bar"

    @dg.op(config_schema=dg.Field(str, is_required=False, default_value="bar"))
    def op_requires_config_val(context):
        assert context.op_config == "bar"
        return context.op_config

    assert op_requires_config_val(None) == "bar"

    @dg.op(
        config_schema={
            "foo": dg.Field(str, is_required=False, default_value="bar"),
            "baz": str,
        }
    )
    def op_requires_config_partial(context):
        assert context.op_config["foo"] == "bar"
        assert context.op_config["baz"] == "bar"
        return context.op_config["foo"] + context.op_config["baz"]

    assert op_requires_config_partial(dg.build_op_context(op_config={"baz": "bar"})) == "barbar"


def test_op_invocation_dict_config():
    @dg.op(config_schema=dict)
    def op_requires_dict(context):
        assert context.op_config == {"foo": "bar"}
        return context.op_config

    assert op_requires_dict(dg.build_op_context(op_config={"foo": "bar"})) == {"foo": "bar"}

    @dg.op(config_schema=dg.Noneable(dict))
    def op_noneable_dict(context):
        return context.op_config

    assert op_noneable_dict(dg.build_op_context()) is None
    assert op_noneable_dict(None) is None


def test_op_invocation_kitchen_sink_config():
    @dg.op(
        config_schema={
            "str_field": str,
            "int_field": int,
            "list_int": [int],
            "list_list_int": [[int]],
            "dict_field": {"a_string": str},
            "list_dict_field": [{"an_int": int}],
            "selector_of_things": dg.Selector(
                {"select_list_dict_field": [{"an_int": int}], "select_int": int}
            ),
            "optional_list_of_optional_string": dg.Noneable([dg.Noneable(str)]),
        }
    )
    def kitchen_sink(context):
        return context.op_config

    op_config_one = {
        "str_field": "kjf",
        "int_field": 2,
        "list_int": [3],
        "list_list_int": [[1], [2, 3]],
        "dict_field": {"a_string": "kdjfkd"},
        "list_dict_field": [{"an_int": 2}, {"an_int": 4}],
        "selector_of_things": {"select_int": 3},
        "optional_list_of_optional_string": ["foo", None],
    }

    assert kitchen_sink(dg.build_op_context(op_config=op_config_one)) == op_config_one


def test_op_with_inputs():
    @dg.op
    def op_with_inputs(x, y):
        assert x == 5
        assert y == 6
        return x + y

    assert op_with_inputs(5, 6) == 11
    assert op_with_inputs(x=5, y=6) == 11
    assert op_with_inputs(5, y=6) == 11
    assert op_with_inputs(y=6, x=5) == 11

    # Check for proper error when incorrect number of inputs is provided.
    with pytest.raises(
        dg.DagsterInvalidInvocationError, match='No value provided for required input "y".'
    ):
        op_with_inputs(5)

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match="Too many input arguments were provided for op 'op_with_inputs'",
    ):
        op_with_inputs(5, 6, 7)

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match="Too many input arguments were provided for op 'op_with_inputs'",
    ):
        op_with_inputs(5, 6, z=7)

    # Check for proper error when input missing.
    with pytest.raises(
        dg.DagsterInvalidInvocationError, match='No value provided for required input "y".'
    ):
        op_with_inputs(5, z=5)


def test_failing_op():
    @dg.op
    def op_fails():
        raise Exception("Oh no!")

    with pytest.raises(
        Exception,
        match="Oh no!",
    ):
        op_fails()


def test_attempted_invocation_in_composition():
    @dg.op
    def basic_op(_x):
        pass

    msg = (
        "Must pass the output from previous node invocations or inputs to the composition "
        "function as inputs when invoking nodes during composition."
    )
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=msg,
    ):

        @dg.job
        def _job_will_fail():
            basic_op(5)

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=msg,
    ):

        @dg.job
        def _job_will_fail_again():
            basic_op(_x=5)


def test_async_op():
    @dg.op
    async def aio_op():
        await asyncio.sleep(0.01)
        return "done"

    assert asyncio.run(aio_op()) == "done"


def test_async_gen_invocation():
    async def make_outputs():
        await asyncio.sleep(0.01)
        yield dg.Output("first", output_name="first")
        await asyncio.sleep(0.01)
        yield dg.Output("second", output_name="second")

    @dg.op(out={"first": dg.Out(), "second": dg.Out()})
    async def aio_gen(_):
        async for v in make_outputs():
            yield v

    context = dg.build_op_context()

    async def get_results():
        res = []
        async for output in aio_gen(context):
            res.append(output)
        return res

    results = asyncio.run(get_results())
    assert results[0].value == "first"
    assert results[1].value == "second"

    @dg.graph
    def aio():
        aio_gen()

    result = aio.execute_in_process()
    assert result.success
    assert result.output_for_node("aio_gen", "first") == "first"
    assert result.output_for_node("aio_gen", "second") == "second"


def test_multiple_outputs_iterator():
    @dg.op(
        out={
            "1": dg.Out(
                int,
            ),
            "2": dg.Out(
                int,
            ),
        }
    )
    def op_multiple_outputs():
        yield dg.Output(2, output_name="2")
        yield dg.Output(1, output_name="1")

    # Ensure that op works both with wrap_op_in_graph_and_execute and invocation
    result = wrap_op_in_graph_and_execute(op_multiple_outputs)
    assert result.success

    outputs = list(op_multiple_outputs())
    assert outputs[0].value == 2
    assert outputs[1].value == 1


def test_wrong_output():
    @dg.op
    def op_wrong_output():
        return dg.Output(5, output_name="wrong_name")

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="explicitly named 'wrong_name'",
    ):
        wrap_op_in_graph_and_execute(op_wrong_output)

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="explicitly named 'wrong_name'",
    ):
        op_wrong_output()


def test_optional_output_return():
    @dg.op(
        out={
            "1": dg.Out(int, is_required=False),
            "2": dg.Out(
                int,
            ),
        }
    )
    def op_multiple_outputs_not_sent():
        return dg.Output(2, output_name="2")

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        op_multiple_outputs_not_sent()

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        wrap_op_in_graph_and_execute(op_multiple_outputs_not_sent)


def test_optional_output_yielded():
    @dg.op(
        out={
            "1": dg.Out(int, is_required=False),
            "2": dg.Out(
                int,
            ),
        }
    )
    def op_multiple_outputs_not_sent():
        yield dg.Output(2, output_name="2")

    assert next(iter(op_multiple_outputs_not_sent())).value == 2


def test_optional_output_yielded_async():
    @dg.op(
        out={
            "1": dg.Out(int, is_required=False),
            "2": dg.Out(
                int,
            ),
        }
    )
    async def op_multiple_outputs_not_sent():
        yield dg.Output(2, output_name="2")

    async def get_results():
        res = []
        async for output in op_multiple_outputs_not_sent():
            res.append(output)
        return res

    output = asyncio.run(get_results())[0]
    assert output.value == 2


def test_missing_required_output_generator():
    # Test missing required output from a generator op
    @dg.op(
        out={
            "1": dg.Out(
                int,
            ),
            "2": dg.Out(
                int,
            ),
        }
    )
    def op_multiple_outputs_not_sent():
        yield dg.Output(2, output_name="2")

    with pytest.raises(
        dg.DagsterStepOutputNotFoundError,
        match=(
            'Core compute for op "op_multiple_outputs_not_sent" did not return an output '
            'for non-optional output "1"'
        ),
    ):
        wrap_op_in_graph_and_execute(op_multiple_outputs_not_sent)

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=(
            'Invocation of op "op_multiple_outputs_not_sent" did not return an output '
            'for non-optional output "1"'
        ),
    ):
        list(op_multiple_outputs_not_sent())


def test_missing_required_output_generator_async():
    # Test missing required output from an async generator op
    @dg.op(
        out={
            "1": dg.Out(
                int,
            ),
            "2": dg.Out(
                int,
            ),
        }
    )
    async def op_multiple_outputs_not_sent():
        yield dg.Output(2, output_name="2")

    with pytest.raises(
        dg.DagsterStepOutputNotFoundError,
        match=(
            'Core compute for op "op_multiple_outputs_not_sent" did not return an output '
            'for non-optional output "1"'
        ),
    ):
        wrap_op_in_graph_and_execute(op_multiple_outputs_not_sent)

    async def get_results():
        res = []
        async for output in op_multiple_outputs_not_sent():
            res.append(output)
        return res

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=(
            "Invocation of op 'op_multiple_outputs_not_sent' did not return an output "
            "for non-optional output '1'"
        ),
    ):
        asyncio.run(get_results())


def test_missing_required_output_return():
    @dg.op(
        out={
            "1": dg.Out(int),
            "2": dg.Out(int),
        }
    )
    def op_multiple_outputs_not_sent():
        return dg.Output(2, output_name="2")

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        wrap_op_in_graph_and_execute(op_multiple_outputs_not_sent)

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="has multiple outputs, but only one output was returned",
    ):
        op_multiple_outputs_not_sent()


def test_output_sent_multiple_times():
    @dg.op(
        out={
            "1": dg.Out(int),
        }
    )
    def op_yields_twice():
        yield dg.Output(1, "1")
        yield dg.Output(2, "1")

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match='Compute for op "op_yields_twice" returned an output "1" multiple times',
    ):
        wrap_op_in_graph_and_execute(op_yields_twice)

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="Invocation of op 'op_yields_twice' yielded an output '1' multiple times",
    ):
        list(op_yields_twice())


_invalid_on_bound = [
    ("dagster_run", None),
    ("step_launcher", None),
    ("job_def", None),
    ("job_name", None),
    ("node_handle", None),
    ("op", None),
    ("get_step_execution_context", None),
]


@pytest.mark.parametrize(
    "property_or_method_name,val_to_pass",
    _invalid_on_bound,
)
def test_invalid_properties_on_bound_context(property_or_method_name: str, val_to_pass: object):
    @dg.op
    def op_fails_getting_property(context):
        result = getattr(context, property_or_method_name)
        (  # for the case where property_or_method_name is a method, getting an attribute won't cause
            # an error, but invoking the method should.
            result(val_to_pass) if val_to_pass else result()
        )

    with pytest.raises(DagsterInvalidPropertyError):
        op_fails_getting_property(dg.build_op_context())


def test_bound_context():
    @dg.op
    def access_bound_details(context: OpExecutionContext):
        assert context.op_def

    access_bound_details(dg.build_op_context())


@pytest.mark.parametrize(
    "property_or_method_name,val_to_pass",
    [
        *_invalid_on_bound,
        ("op_def", None),
        ("assets_def", None),
    ],
)
def test_invalid_properties_on_unbound_context(property_or_method_name: str, val_to_pass: object):
    context = dg.build_op_context()

    with pytest.raises(DagsterInvalidPropertyError):
        result = getattr(context, property_or_method_name)
        result(val_to_pass) if val_to_pass else result()


def test_op_retry_requested():
    @dg.op
    def op_retries():
        raise dg.RetryRequested()

    with pytest.raises(dg.RetryRequested):
        op_retries()


def test_op_failure():
    @dg.op
    def op_fails():
        raise dg.Failure("oops")

    with pytest.raises(dg.Failure, match="oops"):
        op_fails()


def test_yielded_asset_materialization():
    @dg.op
    def op_yields_materialization(_):
        yield dg.AssetMaterialization(asset_key=dg.AssetKey(["fake"]))
        yield dg.Output(5)
        yield dg.AssetMaterialization(asset_key=dg.AssetKey(["fake2"]))

    events = list(op_yields_materialization(None))
    outputs = [event for event in events if isinstance(event, dg.Output)]
    assert outputs[0].value == 5
    materializations = [
        materialization
        for materialization in events
        if isinstance(materialization, dg.AssetMaterialization)
    ]
    assert len(materializations) == 2


def test_input_type_check():
    @dg.op(ins={"x": dg.In(dagster_type=int)})
    def op_takes_input(x):
        return x + 1

    assert op_takes_input(5) == 6

    with pytest.raises(
        dg.DagsterTypeCheckDidNotPass,
        match='Description: Value "foo" of python type "str" must be a int.',
    ):
        op_takes_input("foo")


def test_output_type_check():
    @dg.op(out=dg.Out(dagster_type=int))
    def wrong_type():
        return "foo"

    with pytest.raises(
        dg.DagsterTypeCheckDidNotPass,
        match='Description: Value "foo" of python type "str" must be a int.',
    ):
        wrong_type()


def test_graph_invocation_out_of_composition():
    @dg.op
    def basic_op():
        return 5

    @dg.graph
    def the_graph():
        basic_op()

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=(
            "Attempted to call graph "
            "'the_graph' outside of a composition function. Invoking graphs is only valid in a "
            "function decorated with @job or @graph."
        ),
    ):
        the_graph()


def test_job_invocation():
    @dg.job
    def basic_job():
        pass

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="Attempted to call job "
        "'basic_job' directly. Jobs should be invoked by using an execution API function "
        r"\(e.g. `job.execute_in_process`\).",
    ):
        basic_job()


@dg.op
async def foo_async() -> str:
    return "bar"


def test_coroutine_asyncio_invocation():
    async def my_coroutine_test():
        result = await foo_async()
        assert result == "bar"

    asyncio.run(my_coroutine_test())


def test_op_invocation_nothing_deps():
    @dg.op(ins={"start": dg.In(dg.Nothing)})
    def nothing_dep():
        return 5

    # Ensure that providing the Nothing-dependency input throws an error
    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            "Attempted to provide value for nothing input 'start'. Nothing dependencies are ignored"
            " when directly invoking ops."
        ),
    ):
        nothing_dep(start="blah")

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            "Too many input arguments were provided for op 'nothing_dep'. This may be because "
            "you attempted to provide a value for a nothing dependency. Nothing dependencies are "
            "ignored when directly invoking ops."
        ),
    ):
        nothing_dep("blah")

    # Ensure that not providing nothing dependency also works.
    assert nothing_dep() == 5

    @dg.op(ins={"x": dg.In(), "y": dg.In(dg.Nothing), "z": dg.In()})
    def sandwiched_nothing_dep(x, z):
        return x + z

    assert sandwiched_nothing_dep(5, 6) == 11

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            "Too many input arguments were provided for op 'sandwiched_nothing_dep'. This may "
            "be because you attempted to provide a value for a nothing dependency. Nothing "
            "dependencies are ignored when directly invoking ops."
        ),
    ):
        sandwiched_nothing_dep(5, 6, 7)


def test_dynamic_output_gen():
    @dg.op(out={"a": dg.DynamicOut(is_required=False), "b": dg.Out(is_required=False)})
    def my_dynamic():
        yield dg.DynamicOutput(value=1, mapping_key="1", output_name="a")
        yield dg.DynamicOutput(value=2, mapping_key="2", output_name="a")
        yield dg.Output(value="foo", output_name="b")

    a1, a2, b = my_dynamic()
    assert a1.value == 1
    assert a1.mapping_key == "1"
    assert a2.value == 2
    assert a2.mapping_key == "2"

    assert b.value == "foo"


def test_dynamic_output_async_gen():
    @dg.op(out={"a": dg.DynamicOut(is_required=False), "b": dg.Out(is_required=False)})
    async def aio_gen():
        yield dg.DynamicOutput(value=1, mapping_key="1", output_name="a")
        yield dg.DynamicOutput(value=2, mapping_key="2", output_name="a")
        await asyncio.sleep(0.01)
        yield dg.Output(value="foo", output_name="b")

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
    @dg.op(out={"a": dg.DynamicOut(is_required=False)})
    def should_not_work():
        return dg.DynamicOutput(value=1, mapping_key="1", output_name="a")

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="expected a list of DynamicOutput objects",
    ):
        should_not_work()

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="expected a list of DynamicOutput objects",
    ):
        wrap_op_in_graph_and_execute(should_not_work)


def test_dynamic_output_async_non_gen():
    @dg.op(
        out={
            "a": dg.DynamicOut(is_required=False),
        }
    )
    async def should_not_work():
        await asyncio.sleep(0.01)
        return dg.DynamicOutput(value=1, mapping_key="1", output_name="a")

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="dynamic output 'a' expected a list of DynamicOutput objects",
    ):
        asyncio.run(should_not_work())

    with pytest.raises(Exception):
        wrap_op_in_graph_and_execute(should_not_work())


def test_op_invocation_with_bad_resources(capsys):
    @dg.resource
    def bad_resource(_):
        if 1 == 1:
            raise Exception("oopsy daisy")
        yield "foo"

    @dg.op(required_resource_keys={"my_resource"})
    def op_requires_resource(context):
        return context.resources.my_resource

    with pytest.raises(
        dg.DagsterResourceFunctionError,
        match="Error executing resource_fn on ResourceDefinition my_resource",
    ):
        with dg.build_op_context(resources={"my_resource": bad_resource}) as context:
            assert op_requires_resource(context) == "foo"

    captured = capsys.readouterr()
    # make sure there are no exceptions in the context destructor (__del__)
    assert "Exception ignored in" not in captured.err


@pytest.mark.parametrize("context_builder", [dg.build_op_context, dg.build_op_context])
def test_build_context_with_resources_config(context_builder):
    @dg.resource(config_schema=str)
    def my_resource(context):
        assert context.resource_config == "foo"

    @dg.op(required_resource_keys={"my_resource"})
    def my_op(context):
        assert context.run_config["resources"]["my_resource"] == {"config": "foo"}

    context = context_builder(
        resources={"my_resource": my_resource},
        resources_config={"my_resource": {"config": "foo"}},
    )

    my_op(context)

    # bad resource config case

    with pytest.raises(
        dg.DagsterInvalidConfigError,
        match='Received unexpected config entry "bad_resource" at the root.',
    ):
        context_builder(
            resources={"my_resource": my_resource},
            resources_config={"bad_resource": {"config": "foo"}},
        )


def test_logged_user_events():
    @dg.op
    def logs_events(context):
        context.log_event(dg.AssetMaterialization("first"))
        context.log_event(dg.ExpectationResult(success=True))
        context.log_event(dg.AssetObservation("fourth"))
        yield dg.AssetMaterialization("fifth")
        yield dg.Output("blah")

    context = dg.build_op_context()
    list(logs_events(context))
    assert [type(event) for event in context.get_events()] == [
        dg.AssetMaterialization,
        dg.ExpectationResult,
        dg.AssetObservation,
    ]


def test_add_output_metadata():
    @dg.op(out={"out1": dg.Out(), "out2": dg.Out()})
    def the_op(context):
        context.add_output_metadata({"foo": "bar"}, output_name="out1")
        yield dg.Output(value=1, output_name="out1")
        context.add_output_metadata({"bar": "baz"}, output_name="out2")
        yield dg.Output(value=2, output_name="out2")

    context = dg.build_op_context()
    events = list(the_op(context))
    assert len(events) == 2
    assert context.get_output_metadata("out1") == {"foo": "bar"}
    assert context.get_output_metadata("out2") == {"bar": "baz"}


def test_add_output_metadata_after_output():
    @dg.op
    def the_op(context):
        yield dg.Output(value=1)
        context.add_output_metadata({"foo": "bar"})

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=(
            "In op 'the_op', attempted to log output metadata for output 'result' which has already"
            " been yielded. Metadata must be logged before the output is yielded."
        ),
    ):
        list(the_op(dg.build_op_context()))


def test_log_metadata_multiple_dynamic_outputs():
    @dg.op(out={"out1": dg.DynamicOut(), "out2": dg.DynamicOut()})
    def the_op(context):
        context.add_output_metadata({"one": "one"}, output_name="out1", mapping_key="one")
        yield dg.DynamicOutput(value=1, output_name="out1", mapping_key="one")
        context.add_output_metadata({"two": "two"}, output_name="out1", mapping_key="two")
        context.add_output_metadata({"three": "three"}, output_name="out2", mapping_key="three")
        yield dg.DynamicOutput(value=2, output_name="out1", mapping_key="two")
        yield dg.DynamicOutput(value=3, output_name="out2", mapping_key="three")
        context.add_output_metadata({"four": "four"}, output_name="out2", mapping_key="four")
        yield dg.DynamicOutput(value=4, output_name="out2", mapping_key="four")

    context = dg.build_op_context()

    events = list(the_op(context))
    assert len(events) == 4
    assert context.get_output_metadata("out1", mapping_key="one") == {"one": "one"}
    assert context.get_output_metadata("out1", mapping_key="two") == {"two": "two"}
    assert context.get_output_metadata("out2", mapping_key="three") == {"three": "three"}
    assert context.get_output_metadata("out2", mapping_key="four") == {"four": "four"}


def test_log_metadata_after_dynamic_output():
    @dg.op(out=dg.DynamicOut())
    def the_op(context):
        yield dg.DynamicOutput(1, mapping_key="one")
        context.add_output_metadata({"foo": "bar"}, mapping_key="one")

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match=(
            "In op 'the_op', attempted to log output metadata for output 'result' with mapping_key"
            " 'one' which has already been yielded. Metadata must be logged before the output is"
            " yielded."
        ),
    ):
        list(the_op(dg.build_op_context()))


def test_kwarg_inputs():
    @dg.op(ins={"the_in": dg.In(str)})
    def the_op(**kwargs) -> str:
        return kwargs["the_in"] + "foo"

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match="'the_op' has 0 positional inputs, but 1 positional inputs were provided.",
    ):
        the_op("bar")

    assert the_op(the_in="bar") == "barfoo"

    with pytest.raises(KeyError):
        the_op(bad_val="bar")

    @dg.op(ins={"the_in": dg.In(), "kwarg_in": dg.In(), "kwarg_in_two": dg.In()})
    def the_op_2(the_in, **kwargs):
        return the_in + kwargs["kwarg_in"] + kwargs["kwarg_in_two"]

    assert the_op_2("foo", kwarg_in="bar", kwarg_in_two="baz") == "foobarbaz"


def test_kwarg_inputs_context():
    context = dg.build_op_context()

    @dg.op(ins={"the_in": dg.In(str)})
    def the_op(context, **kwargs) -> str:
        assert context
        return kwargs["the_in"] + "foo"

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match="'the_op' has 0 positional inputs, but 1 positional inputs were provided.",
    ):
        the_op(context, "bar")

    assert the_op(context, the_in="bar") == "barfoo"

    with pytest.raises(KeyError):
        the_op(context, bad_val="bar")

    @dg.op(ins={"the_in": dg.In(), "kwarg_in": dg.In(), "kwarg_in_two": dg.In()})
    def the_op_2(context, the_in, **kwargs):
        assert context
        return the_in + kwargs["kwarg_in"] + kwargs["kwarg_in_two"]

    assert the_op_2(context, "foo", kwarg_in="bar", kwarg_in_two="baz") == "foobarbaz"


def test_default_kwarg_inputs():
    @dg.op
    def the_op(x=1, y=2):
        return x + y

    assert the_op() == 3


def test_kwargs_via_partial_functools():
    def fake_func(foo, bar):
        return foo + bar

    new_func = partial(fake_func, foo=1, bar=2)

    new_op = dg.op(name="new_func")(new_func)

    assert new_op() == 3


def test_get_mapping_key():
    context = dg.build_op_context(mapping_key="the_key")

    assert context.get_mapping_key() == "the_key"  # Ensure unbound context has mapping key

    @dg.op
    def basic_op(context):
        assert context.get_mapping_key() == "the_key"  # Ensure bound context has mapping key

    basic_op(context)


def test_required_resource_keys_no_context_invocation():
    @dg.op(required_resource_keys={"foo"})
    def uses_resource_no_context():
        pass

    uses_resource_no_context()

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            "Too many input arguments were provided for op "
            "'uses_resource_no_context'. This may be because an argument was "
            "provided for the context parameter, but no context parameter was "
            "defined for the op."
        ),
    ):
        uses_resource_no_context(None)


def test_assets_def_invocation():
    @dg.asset()
    def my_asset(context):
        assert context.assets_def == my_asset

    @dg.op
    def non_asset_op(context):
        context.assets_def  # noqa: B018

    with dg.build_asset_context(
        partition_key="2023-02-02",
    ) as context:
        my_asset(context)

    with dg.build_op_context(
        partition_key="2023-02-02",
    ) as context:
        with pytest.raises(DagsterInvalidPropertyError, match="does not have an assets definition"):
            non_asset_op(context)


def test_partitions_time_window_asset_invocation():
    partitions_def = dg.DailyPartitionsDefinition(start_date=datetime(2023, 1, 1))

    @dg.asset(
        partitions_def=partitions_def,
    )
    def partitioned_asset(context: AssetExecutionContext):
        start, end = context.partition_time_window
        assert start == create_datetime(2023, 2, 2, tz=partitions_def.timezone)
        assert end == create_datetime(2023, 2, 3, tz=partitions_def.timezone)

    context = dg.build_asset_context(
        partition_key="2023-02-02",
    )
    partitioned_asset(context)


def test_multipartitioned_time_window_asset_invocation():
    partitions_def = dg.MultiPartitionsDefinition(
        {
            "date": dg.DailyPartitionsDefinition(start_date="2020-01-01"),
            "static": dg.StaticPartitionsDefinition(["a", "b"]),
        }
    )

    @dg.asset(partitions_def=partitions_def)
    def my_asset(context: AssetExecutionContext):
        time_partition = get_time_partitions_def(partitions_def)
        if time_partition is None:
            assert False, "partitions def does not have a time component"
        time_window = dg.TimeWindow(
            start=create_datetime(year=2020, month=1, day=1, tz=time_partition.timezone),
            end=create_datetime(year=2020, month=1, day=2, tz=time_partition.timezone),
        )
        assert context.partition_time_window == time_window
        return 1

    context = dg.build_asset_context(
        partition_key="2020-01-01|a",
    )
    my_asset(context)

    partitions_def = dg.MultiPartitionsDefinition(
        {
            "static2": dg.StaticPartitionsDefinition(["a", "b"]),
            "static": dg.StaticPartitionsDefinition(["a", "b"]),
        }
    )

    @dg.asset(partitions_def=partitions_def)
    def static_multipartitioned_asset(context: AssetExecutionContext):
        with pytest.raises(
            dg.DagsterInvariantViolationError,
            match="with a single time dimension",
        ):
            _ = context.partition_time_window

    context = dg.build_asset_context(
        partition_key="a|a",
    )
    static_multipartitioned_asset(context)


def test_partition_range_asset_invocation():
    partitions_def = dg.DailyPartitionsDefinition(start_date=datetime(2023, 1, 1))

    @dg.asset(partitions_def=partitions_def)
    def foo(context: AssetExecutionContext):
        keys1 = partitions_def.get_partition_keys_in_range(context.partition_key_range)
        keys2 = context.partition_keys
        assert keys1 == keys2
        return {k: True for k in keys1}

    context = dg.build_asset_context(
        partition_key_range=dg.PartitionKeyRange("2023-01-01", "2023-01-02"),
    )
    assert foo(context) == {"2023-01-01": True, "2023-01-02": True}

    context = dg.build_asset_context(
        partition_key_range=dg.PartitionKeyRange("2023-01-01", "2023-01-02"),
    )
    assert foo(context) == {"2023-01-01": True, "2023-01-02": True}


def test_direct_invocation_output_metadata():
    @dg.asset
    def my_asset(context):
        context.add_output_metadata({"foo": "bar"})

    @dg.asset
    def my_other_asset(context):
        context.add_output_metadata({"baz": "qux"})

    ctx = dg.build_asset_context()

    my_asset(ctx)
    assert ctx.get_output_metadata("result") == {"foo": "bar"}

    # context is unbound when used in another invocation. This allows the metadata to be
    # added in my_other_asset
    my_other_asset(ctx)


def test_async_assets_with_shared_context():
    @dg.asset
    async def async_asset_one(context):
        assert context.asset_key.to_user_string() == "async_asset_one"
        await asyncio.sleep(0.01)
        return "one"

    @dg.asset
    async def async_asset_two(context):
        assert context.asset_key.to_user_string() == "async_asset_two"
        await asyncio.sleep(0.01)
        return "two"

    # test that we can run two ops/assets with the same context at the same time without
    # overriding op/asset specific attributes
    ctx = dg.build_asset_context()

    async def main():
        return await asyncio.gather(
            async_asset_one(ctx),  # type: ignore
            async_asset_two(ctx),  # type: ignore
        )

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=r"This context is currently being used to execute .* The context"
        r" cannot be used to execute another asset until .* has finished executing",
    ):
        asyncio.run(main())


def assert_context_unbound(context: DirectOpExecutionContext):
    # to assert that the context is correctly unbound after op invocation
    assert not context.is_bound


def assert_context_bound(context: DirectOpExecutionContext):
    # to assert that the context is correctly bound during op invocation
    assert context.is_bound


def assert_execution_properties_cleared(context: DirectOpExecutionContext):
    # to assert that the invocation properties are reset at the beginning of op invocation
    assert len(context.execution_properties.output_metadata.keys()) == 0


def assert_execution_properties_exist(context: DirectOpExecutionContext):
    # to assert that the invocation properties remain accessible after op invocation
    assert len(context.execution_properties.output_metadata.keys()) > 0


def test_context_bound_state_non_generator():
    @dg.asset
    def my_asset(context):
        assert_context_bound(context)
        assert_execution_properties_cleared(context)
        context.add_output_metadata({"foo": "bar"})

    ctx = dg.build_op_context()
    assert_context_unbound(ctx)

    my_asset(ctx)
    assert_context_unbound(ctx)
    assert_execution_properties_exist(ctx)

    my_asset(ctx)
    assert_context_unbound(ctx)
    assert_execution_properties_exist(ctx)


def test_context_bound_state_generator():
    @dg.op(out={"first": dg.Out(), "second": dg.Out()})
    def generator(context):
        assert_context_bound(context)
        assert_execution_properties_cleared(context)
        context.add_output_metadata({"foo": "bar"}, output_name="first")
        yield dg.Output("one", output_name="first")
        yield dg.Output("two", output_name="second")

    ctx = dg.build_op_context()

    result = list(generator(ctx))
    assert result[0].value == "one"
    assert result[1].value == "two"
    assert_context_unbound(ctx)
    assert_execution_properties_exist(ctx)

    result = list(generator(ctx))
    assert result[0].value == "one"
    assert result[1].value == "two"
    assert_context_unbound(ctx)
    assert_execution_properties_exist(ctx)


def test_context_bound_state_async():
    @dg.asset
    async def async_asset(context):
        assert_context_bound(context)
        assert_execution_properties_cleared(context)
        assert context.asset_key.to_user_string() == "async_asset"
        context.add_output_metadata({"foo": "bar"})
        await asyncio.sleep(0.01)
        return "one"

    ctx = dg.build_asset_context()

    result = asyncio.run(async_asset(ctx))  # pyright: ignore[reportArgumentType]
    assert result == "one"
    assert_context_unbound(ctx)  # pyright: ignore[reportArgumentType]
    assert_execution_properties_exist(ctx)  # pyright: ignore[reportArgumentType]

    result = asyncio.run(async_asset(ctx))  # pyright: ignore[reportArgumentType]
    assert result == "one"
    assert_context_unbound(ctx)  # pyright: ignore[reportArgumentType]
    assert_execution_properties_exist(ctx)  # pyright: ignore[reportArgumentType]


def test_context_bound_state_async_generator():
    @dg.op(out={"first": dg.Out(), "second": dg.Out()})
    async def async_generator(context):
        assert_context_bound(context)
        assert_execution_properties_cleared(context)
        context.add_output_metadata({"foo": "bar"}, output_name="first")
        yield dg.Output("one", output_name="first")
        await asyncio.sleep(0.01)
        yield dg.Output("two", output_name="second")

    ctx = dg.build_op_context()

    async def get_results():
        res = []
        async for output in async_generator(ctx):
            res.append(output)
        return res

    result = asyncio.run(get_results())
    assert result[0].value == "one"
    assert result[1].value == "two"
    assert_context_unbound(ctx)
    assert_execution_properties_exist(ctx)

    result = asyncio.run(get_results())
    assert result[0].value == "one"
    assert result[1].value == "two"
    assert_context_unbound(ctx)
    assert_execution_properties_exist(ctx)


def test_bound_state_with_error_assets():
    @dg.asset
    def throws_error(context):
        assert context.asset_key.to_user_string() == "throws_error"
        raise dg.Failure("something bad happened!")

    ctx = dg.build_asset_context()

    with pytest.raises(dg.Failure):
        throws_error(ctx)

    assert_context_unbound(ctx)  # pyright: ignore[reportArgumentType]

    @dg.asset
    def no_error(context):
        assert context.asset_key.to_user_string() == "no_error"

    no_error(ctx)


def test_context_bound_state_with_error_ops():
    @dg.op(out={"first": dg.Out(), "second": dg.Out()})
    def throws_error(context):
        assert_context_bound(ctx)
        raise dg.Failure("something bad happened!")

    ctx = dg.build_op_context()

    with pytest.raises(dg.Failure):
        throws_error(ctx)

    assert_context_unbound(ctx)


def test_context_bound_state_with_error_generator():
    @dg.op(out={"first": dg.Out(), "second": dg.Out()})
    def generator(context):
        assert_context_bound(ctx)
        yield dg.Output("one", output_name="first")
        raise dg.Failure("something bad happened!")

    ctx = dg.build_op_context()

    with pytest.raises(dg.Failure):
        list(generator(ctx))

    assert_context_unbound(ctx)


def test_context_bound_state_with_error_async():
    @dg.asset
    async def async_asset(context):
        assert_context_bound(ctx)  # pyright: ignore[reportArgumentType]
        await asyncio.sleep(0.01)
        raise dg.Failure("something bad happened!")

    ctx = dg.build_asset_context()

    with pytest.raises(dg.Failure):
        asyncio.run(async_asset(ctx))  # pyright: ignore[reportArgumentType]

    assert_context_unbound(ctx)  # pyright: ignore[reportArgumentType]


def test_context_bound_state_with_error_async_generator():
    @dg.op(out={"first": dg.Out(), "second": dg.Out()})
    async def async_generator(context):
        assert_context_bound(ctx)
        yield dg.Output("one", output_name="first")
        await asyncio.sleep(0.01)
        raise dg.Failure("something bad happened!")

    ctx = dg.build_op_context()

    async def get_results():
        res = []
        async for output in async_generator(ctx):
            res.append(output)
        return res

    with pytest.raises(dg.Failure):
        asyncio.run(get_results())

    assert_context_unbound(ctx)


def test_run_tags():
    @dg.op
    def basic_op(context):
        assert context.run_tags["foo"] == "bar"
        assert context.has_tag("foo")
        assert not context.has_tag("ffdoo")
        assert context.get_tag("foo") == "bar"

    basic_op(dg.build_op_context(run_tags={"foo": "bar"}))

    @dg.asset
    def basic_asset(context):
        assert context.run_tags["foo"] == "bar"
        assert context.has_tag("foo")
        assert not context.has_tag("ffdoo")
        assert context.get_tag("foo") == "bar"

    basic_asset(dg.build_asset_context(run_tags={"foo": "bar"}))
