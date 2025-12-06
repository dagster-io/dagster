import inspect
from collections.abc import Iterator
from contextlib import contextmanager

import dagster as dg
import pytest
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.context.compute import ExecutionContextTypes, enter_execution_context
from dagster._core.execution.context.system import StepExecutionContext
from dagster._core.execution.plan.aio.compute_generator import (
    _coerce_async_op_to_async_gen,
    _coerce_op_compute_fn_to_iterator,
    _filter_expected_output_defs,
    _validate_multi_return,
    _zip_and_iterate_op_result,
    create_op_compute_wrapper,
    invoke_compute_fn,
    validate_and_coerce_op_result_to_iterator,
)

from dagster_tests.execution_tests.async_tests.helpers import StepContextFactory


class MyConfig(dg.Config):
    foo: str
    bar: int


@contextmanager
def _job_context(
    job_def: dg.JobDefinition,
    step_context_factory: StepContextFactory,
    step_key: str | None = None,
) -> Iterator[tuple[StepExecutionContext, ExecutionContextTypes]]:
    with step_context_factory(job_def, step_key=step_key) as step_context:
        with enter_execution_context(step_context) as compute_context:
            yield step_context, compute_context


@pytest.mark.anyio
async def test_create_op_compute_wrapper_sync_op_returns_iterator(
    step_context_factory: StepContextFactory,
) -> None:
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
        core_gen = await create_op_compute_wrapper(step_context.op_def)
        user_gen = await core_gen(compute_context, {"a": 1, "b": 2})
        assert inspect.isasyncgen(user_gen)
        events = [event async for event in user_gen]

    assert len(events) == 1
    assert isinstance(events[0], dg.Output)
    assert events[0].output_name == "result"
    assert events[0].value == 3


@pytest.mark.anyio
async def test_create_op_compute_wrapper_async_op_returns_async_gen(
    step_context_factory: StepContextFactory,
) -> None:
    @dg.op
    async def async_op() -> int:
        return 5

    @dg.job
    def async_job():
        async_op()

    with _job_context(async_job, step_context_factory) as (step_context, compute_context):
        core_gen = await create_op_compute_wrapper(step_context.op_def)
        user_gen = await core_gen(compute_context, {})
        assert inspect.isasyncgen(user_gen)
        outputs = [event async for event in user_gen]

    assert len(outputs) == 1
    assert outputs[0].value == 5


@pytest.mark.anyio
async def test_coerce_async_op_to_async_gen_wraps_return_value(
    step_context_factory: StepContextFactory,
) -> None:
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

    outputs = []
    async for event in _coerce_async_op_to_async_gen(coro(), compute_context, output_defs):
        outputs.append(event)
    assert len(outputs) == 1
    assert outputs[0].value == 7


@pytest.mark.anyio
async def test_invoke_compute_fn_with_config_class_uses_construct_config_from_context() -> None:
    ctx = dg.build_op_context(op_config={"foo": "x", "bar": 1, "extra": "ignore"})

    def fn(context, config: MyConfig):
        assert isinstance(config, MyConfig)
        assert config.foo == "x"
        assert config.bar == 1
        return "done"

    assert await invoke_compute_fn(fn, ctx, {}, True, MyConfig) == "done"


@pytest.mark.anyio
async def test_invoke_compute_fn_with_primitive_config_uses_op_config() -> None:
    ctx = dg.build_op_context(op_config="foo")

    def fn(config: str):
        return config

    assert await invoke_compute_fn(fn, ctx, {}, False, str) == "foo"


@pytest.mark.anyio
async def test_invoke_compute_fn_injects_resources() -> None:
    resource_value = object()
    ctx = dg.build_op_context(resources={"my_resource": resource_value})

    def fn(my_arg):
        return my_arg

    result = await invoke_compute_fn(
        fn,
        ctx,
        {},
        False,
        None,
        resource_args={"my_resource": "my_arg"},
    )
    assert result is ctx.resources.my_resource


@pytest.mark.anyio
async def test_coerce_op_compute_fn_to_iterator_wraps_value_into_output(
    step_context_factory: StepContextFactory,
) -> None:
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

        events = []
        async for event in _coerce_op_compute_fn_to_iterator(
            compute_fn,
            output_defs,
            compute_context,
            True,
            {},
            None,
            None,
        ):
            events.append(event)

    assert len(events) == 1
    assert events[0].value == 10


@pytest.mark.anyio
async def test_zip_and_iterate_single_output(step_context_factory: StepContextFactory) -> None:
    @dg.op
    def only_output() -> int:
        return 1

    @dg.job
    def single_output_job():
        only_output()

    with _job_context(single_output_job, step_context_factory) as (step_context, compute_context):
        output_defs = step_context.op_def.output_defs
        zipped = []
        async for z in _zip_and_iterate_op_result(42, compute_context, output_defs):
            zipped.append(z)

    assert zipped[0][0] == 0
    assert zipped[0][1] == 42
    assert zipped[0][2] == output_defs[0]


@pytest.mark.anyio
async def test_zip_and_iterate_multi_output_valid_tuple(
    step_context_factory: StepContextFactory,
) -> None:
    @dg.op(out={"left": dg.Out(int), "right": dg.Out(int)})
    def multi():
        return (1, 2)

    @dg.job
    def multi_job():
        multi()

    with _job_context(multi_job, step_context_factory) as (step_context, compute_context):
        output_defs = step_context.op_def.output_defs
        zipped = []
        async for z in _zip_and_iterate_op_result((1, 2), compute_context, output_defs):
            zipped.append(z)

    assert zipped[0] == (0, 1, output_defs[0])
    assert zipped[1] == (1, 2, output_defs[1])


@pytest.mark.anyio
async def test_filter_expected_output_defs_no_asset_results_returns_all(
    step_context_factory: StepContextFactory,
) -> None:
    @dg.op
    def single_output() -> int:
        return 1

    @dg.job
    def single_job():
        single_output()

    with _job_context(single_job, step_context_factory) as (step_context, compute_context):
        output_defs = step_context.op_def.output_defs
        filtered = await _filter_expected_output_defs(5, compute_context, output_defs)

    assert filtered == output_defs


@pytest.mark.anyio
async def test_filter_expected_output_defs_omits_check_outputs_embedded_in_asset_results(
    asset_step_context: StepExecutionContext,
    asset_compute_context: ExecutionContextTypes,
) -> None:
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

    filtered = await _filter_expected_output_defs(
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


@pytest.mark.anyio
async def test_validate_multi_return_all_nothing_outputs_and_none_returns_list_of_nones(
    step_context_factory: StepContextFactory,
) -> None:
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
        result = await _validate_multi_return(compute_context, None, output_defs)

    assert result == [None, None]


@pytest.mark.anyio
async def test_validate_multi_return_non_tuple_with_multiple_outputs_raises(
    step_context_factory: StepContextFactory,
) -> None:
    @dg.op(out={"left": dg.Out(int), "right": dg.Out(int)})
    def multi_op():
        return (1, 2)

    @dg.job
    def multi_job():
        multi_op()

    with _job_context(multi_job, step_context_factory) as (step_context, compute_context):
        output_defs = step_context.op_def.output_defs
        with pytest.raises(DagsterInvariantViolationError):
            _ = await _validate_multi_return(compute_context, 5, output_defs)


@pytest.mark.anyio
async def test_validate_multi_return_length_mismatch_raises(
    step_context_factory: StepContextFactory,
) -> None:
    @dg.op(out={"left": dg.Out(int), "right": dg.Out(int)})
    def multi_op():
        return (1, 2)

    @dg.job
    def multi_job():
        multi_op()

    with _job_context(multi_job, step_context_factory) as (step_context, compute_context):
        output_defs = step_context.op_def.output_defs
        with pytest.raises(DagsterInvariantViolationError):
            _ = await _validate_multi_return(compute_context, (1,), output_defs)


@pytest.mark.anyio
async def test_validate_and_coerce_rejects_returned_asset_materialization(
    step_context_factory: StepContextFactory,
) -> None:
    @dg.op
    def base_op() -> int:
        return 1

    @dg.job
    def job_def():
        base_op()

    with _job_context(job_def, step_context_factory) as (step_context, compute_context):
        output_defs = step_context.op_def.output_defs
        with pytest.raises(DagsterInvariantViolationError):
            async for result in validate_and_coerce_op_result_to_iterator(
                dg.AssetMaterialization("foo"),
                compute_context,
                output_defs,
            ):
                pass


@pytest.mark.anyio
async def test_validate_and_coerce_wraps_single_value_in_output(
    step_context_factory: StepContextFactory,
) -> None:
    @dg.op
    def base_op() -> int:
        return 1

    @dg.job
    def job_def():
        base_op()

    with _job_context(job_def, step_context_factory) as (step_context, compute_context):
        output_defs = step_context.op_def.output_defs
        events = []
        async for event in validate_and_coerce_op_result_to_iterator(
            3, compute_context, output_defs
        ):
            events.append(event)

    assert len(events) == 1
    assert events[0].value == 3


@pytest.mark.anyio
async def test_validate_and_coerce_respects_requires_typed_event_stream(
    asset_step_context: StepExecutionContext,
) -> None:
    asset_step_context.set_requires_typed_event_stream()
    with enter_execution_context(asset_step_context) as compute_context:
        output_defs = asset_step_context.op_def.output_defs
        events = []
        async for event in validate_and_coerce_op_result_to_iterator(
            5, compute_context, output_defs
        ):
            events.append(event)

    assert events == [5]
