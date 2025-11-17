import asyncio
import inspect
from contextlib import contextmanager

import dagster as dg
import pytest
from dagster._core.definitions.output import OutputDefinition
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.context.compute import enter_execution_context
from dagster._core.execution.plan.compute import gen_from_async_gen
from dagster._core.execution.plan.compute_generator import (
    _check_output_object_name,
    _coerce_async_op_to_async_gen,
    _coerce_op_compute_fn_to_iterator,
    _filter_expected_output_defs,
    _get_annotation_for_output_position,
    _validate_multi_return,
    _zip_and_iterate_op_result,
    construct_config_from_context,
    create_op_compute_wrapper,
    invoke_compute_fn,
    validate_and_coerce_op_result_to_iterator,
)


class MyConfig(dg.Config):
    foo: str
    bar: int


@contextmanager
def _job_context(job_def: dg.JobDefinition, step_context_factory, step_key: str | None = None):
    with step_context_factory(job_def, step_key=step_key) as step_context:
        with enter_execution_context(step_context) as compute_context:
            yield step_context, compute_context


def test_create_op_compute_wrapper_sync_op_returns_iterator(step_context_factory):
    @dg.op
    def add(a: int, b: int) -> int:
        return a + b

    @dg.op
    def emit_one() -> int:
        return 1

    @dg.op
    def emit_two() -> int:
        return 2

    @dg.job
    def add_job():
        add(emit_one(), emit_two())

    with _job_context(add_job, step_context_factory, step_key="add") as (
        step_context,
        compute_context,
    ):
        core_gen = create_op_compute_wrapper(step_context.op_def)
        events = list(core_gen(compute_context, {"a": 1, "b": 2}))

    assert len(events) == 1
    assert isinstance(events[0], dg.Output)
    assert events[0].output_name == "result"
    assert events[0].value == 3


def test_create_op_compute_wrapper_async_op_returns_async_gen(step_context_factory):
    @dg.op
    async def async_op() -> int:
        return 5

    @dg.job
    def async_job():
        async_op()

    with _job_context(async_job, step_context_factory) as (step_context, compute_context):
        core_gen = create_op_compute_wrapper(step_context.op_def)
        user_gen = core_gen(compute_context, {})
        assert inspect.isasyncgen(user_gen)
        outputs = list(gen_from_async_gen(step_context, user_gen))

    assert len(outputs) == 1
    assert outputs[0].value == 5


def test_create_op_compute_wrapper_generator_op_passthrough(step_context_factory):
    @dg.op(out={"one": dg.Out(int), "two": dg.Out(int)})
    def emit_outputs():
        yield dg.Output(1, output_name="one")
        yield dg.Output(2, output_name="two")

    @dg.job
    def generator_job():
        emit_outputs()

    with _job_context(generator_job, step_context_factory) as (step_context, compute_context):
        core_gen = create_op_compute_wrapper(step_context.op_def)
        events = list(core_gen(compute_context, {}))

    assert [event.output_name for event in events] == ["one", "two"]
    assert [event.value for event in events] == [1, 2]


def test_coerce_async_op_to_async_gen_wraps_return_value(step_context_factory):
    @dg.op
    def base_op() -> int:
        return 0

    @dg.job
    def base_job():
        base_op()

    with _job_context(base_job, step_context_factory) as (step_context, compute_context):
        output_defs = step_context.op_def.output_defs

    async def coro():
        return 7

    async def consume():
        collected = []
        async for event in _coerce_async_op_to_async_gen(coro(), compute_context, output_defs):
            collected.append(event)
        return collected

    outputs = asyncio.run(consume())
    assert len(outputs) == 1
    assert outputs[0].value == 7


def test_invoke_compute_fn_with_config_class_uses_construct_config_from_context():
    ctx = dg.build_op_context(op_config={"foo": "x", "bar": 1, "extra": "ignore"})

    def fn(context, config: MyConfig):
        assert isinstance(config, MyConfig)
        assert config.foo == "x"
        assert config.bar == 1
        return "done"

    assert invoke_compute_fn(fn, ctx, {}, True, MyConfig) == "done"


def test_invoke_compute_fn_with_primitive_config_uses_op_config():
    ctx = dg.build_op_context(op_config="foo")

    def fn(config: str):
        return config

    assert invoke_compute_fn(fn, ctx, {}, False, str) == "foo"


def test_invoke_compute_fn_injects_resources():
    resource_value = object()
    ctx = dg.build_op_context(resources={"my_resource": resource_value})

    def fn(my_arg):
        return my_arg

    result = invoke_compute_fn(
        fn,
        ctx,
        {},
        False,
        None,
        resource_args={"my_resource": "my_arg"},
    )
    assert result is ctx.resources.my_resource


def test_construct_config_from_context_builds_config_from_op_config():
    ctx = dg.build_op_context(op_config={"foo": "x", "bar": 2})
    config = construct_config_from_context(MyConfig, ctx)
    assert isinstance(config, MyConfig)
    assert config.foo == "x"
    assert config.bar == 2


def test_coerce_op_compute_fn_to_iterator_wraps_value_into_output(step_context_factory):
    @dg.op
    def base_op() -> int:
        return 0

    @dg.job
    def job_def():
        base_op()

    with _job_context(job_def, step_context_factory) as (step_context, compute_context):
        output_defs = step_context.op_def.output_defs

        def compute_fn(_context):
            return 10

        iterator = _coerce_op_compute_fn_to_iterator(
            compute_fn,
            output_defs,
            compute_context,
            True,
            {},
            None,
            None,
        )

        events = list(iterator)

    assert len(events) == 1
    assert events[0].value == 10


def test_zip_and_iterate_single_output(step_context_factory):
    @dg.op
    def only_output() -> int:
        return 1

    @dg.job
    def single_output_job():
        only_output()

    with _job_context(single_output_job, step_context_factory) as (step_context, compute_context):
        output_defs = step_context.op_def.output_defs
        zipped = list(_zip_and_iterate_op_result(42, compute_context, output_defs))

    assert zipped[0][0] == 0
    assert zipped[0][1] == output_defs[0]
    assert zipped[0][2] == 42


def test_zip_and_iterate_multi_output_valid_tuple(step_context_factory):
    @dg.op(out={"left": dg.Out(int), "right": dg.Out(int)})
    def multi():
        return (1, 2)

    @dg.job
    def multi_job():
        multi()

    with _job_context(multi_job, step_context_factory) as (step_context, compute_context):
        output_defs = step_context.op_def.output_defs
        zipped = list(_zip_and_iterate_op_result((1, 2), compute_context, output_defs))

    assert zipped[0] == (0, output_defs[0], 1)
    assert zipped[1] == (1, output_defs[1], 2)


def test_filter_expected_output_defs_no_asset_results_returns_all(step_context_factory):
    @dg.op
    def single_output() -> int:
        return 1

    @dg.job
    def single_job():
        single_output()

    with _job_context(single_job, step_context_factory) as (step_context, compute_context):
        output_defs = step_context.op_def.output_defs
        filtered = _filter_expected_output_defs(5, compute_context, output_defs)

    assert filtered == output_defs


def test_filter_expected_output_defs_omits_check_outputs_embedded_in_asset_results(
    asset_step_context, asset_compute_context
):
    output_defs = asset_step_context.op_def.output_defs
    asset_key = asset_step_context.job_def.asset_layer.get_asset_key_for_node(
        asset_step_context.node_handle
    )
    selected_check_keys = list(asset_compute_context.op_execution_context.selected_asset_check_keys)
    assert selected_check_keys
    check_key = selected_check_keys[0]
    materialize_result = dg.MaterializeResult(
        asset_key=asset_key,
        check_results=[
            dg.AssetCheckResult(asset_key=asset_key, check_name=check_key.name, passed=True)
        ],
    )

    filtered = _filter_expected_output_defs(
        materialize_result,
        asset_compute_context,
        output_defs,
    )

    check_output_name = (
        asset_compute_context.op_execution_context.assets_def.get_output_name_for_asset_check_key(
            check_key
        )
    )
    assert check_output_name not in [output_def.name for output_def in filtered]


def test_validate_multi_return_all_nothing_outputs_and_none_returns_list_of_nones(
    step_context_factory,
):
    @dg.op(
        out={
            "first": dg.Out(dg.Nothing, is_required=True),
            "second": dg.Out(dg.Nothing, is_required=True),
        }
    )
    def nothing_op():
        pass

    @dg.job
    def nothing_job():
        nothing_op()

    with _job_context(nothing_job, step_context_factory) as (step_context, compute_context):
        output_defs = step_context.op_def.output_defs
        result = _validate_multi_return(compute_context, None, output_defs)

    assert result == [None, None]


def test_validate_multi_return_non_tuple_with_multiple_outputs_raises(step_context_factory):
    @dg.op(out={"left": dg.Out(int), "right": dg.Out(int)})
    def multi_op():
        return (1, 2)

    @dg.job
    def multi_job():
        multi_op()

    with _job_context(multi_job, step_context_factory) as (step_context, compute_context):
        output_defs = step_context.op_def.output_defs
        with pytest.raises(DagsterInvariantViolationError):
            _validate_multi_return(compute_context, 5, output_defs)


def test_validate_multi_return_length_mismatch_raises(step_context_factory):
    @dg.op(out={"left": dg.Out(int), "right": dg.Out(int)})
    def multi_op():
        return (1, 2)

    @dg.job
    def multi_job():
        multi_op()

    with _job_context(multi_job, step_context_factory) as (step_context, compute_context):
        output_defs = step_context.op_def.output_defs
        with pytest.raises(DagsterInvariantViolationError):
            _validate_multi_return(compute_context, (1,), output_defs)


def test_get_annotation_for_output_position_multiple_outputs_tuple_annotation():
    @dg.op(out={"a": dg.Out(int), "b": dg.Out(str)})
    def op_multi() -> tuple[int, str]:
        return (1, "x")

    assert _get_annotation_for_output_position(0, op_multi, op_multi.output_defs) is int
    assert _get_annotation_for_output_position(1, op_multi, op_multi.output_defs) is str


def test_get_annotation_for_output_position_single_output_returns_annotation():
    @dg.op
    def op_single() -> int:
        return 1

    assert _get_annotation_for_output_position(0, op_single, op_single.output_defs) is int


def test_check_output_object_name_passes_for_matching_name():
    output_def = OutputDefinition(name="result", dagster_type=int)
    _check_output_object_name(dg.Output(1, output_name="result"), output_def, 0)


def test_check_output_object_name_raises_for_mismatched_name():
    output_def = OutputDefinition(name="result", dagster_type=int)
    with pytest.raises(DagsterInvariantViolationError):
        _check_output_object_name(dg.Output(1, output_name="other"), output_def, 0)


def test_validate_and_coerce_generator_passthrough(step_context_factory):
    @dg.op
    def base_op() -> int:
        return 1

    @dg.job
    def job_def():
        base_op()

    with _job_context(job_def, step_context_factory) as (step_context, compute_context):
        output_defs = step_context.op_def.output_defs

        def generator():
            yield dg.Output(1)

        events = list(
            validate_and_coerce_op_result_to_iterator(generator(), compute_context, output_defs)
        )

    assert len(events) == 1
    assert events[0].value == 1


def test_validate_and_coerce_rejects_returned_asset_materialization(step_context_factory):
    @dg.op
    def base_op() -> int:
        return 1

    @dg.job
    def job_def():
        base_op()

    with _job_context(job_def, step_context_factory) as (step_context, compute_context):
        output_defs = step_context.op_def.output_defs
        with pytest.raises(DagsterInvariantViolationError):
            list(
                validate_and_coerce_op_result_to_iterator(
                    dg.AssetMaterialization("foo"),
                    compute_context,
                    output_defs,
                )
            )


def test_validate_and_coerce_wraps_single_value_in_output(step_context_factory):
    @dg.op
    def base_op() -> int:
        return 1

    @dg.job
    def job_def():
        base_op()

    with _job_context(job_def, step_context_factory) as (step_context, compute_context):
        output_defs = step_context.op_def.output_defs
        events = list(validate_and_coerce_op_result_to_iterator(3, compute_context, output_defs))

    assert len(events) == 1
    assert events[0].value == 3


def test_validate_and_coerce_respects_requires_typed_event_stream(asset_step_context):
    asset_step_context.set_requires_typed_event_stream()
    with enter_execution_context(asset_step_context) as compute_context:
        output_defs = asset_step_context.op_def.output_defs
        events = list(validate_and_coerce_op_result_to_iterator(5, compute_context, output_defs))

    assert events == [5]
