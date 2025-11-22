from collections.abc import Iterator
from contextlib import contextmanager

import dagster as dg
import pytest
from dagster._core.definitions import AssetCheckEvaluation, MetadataValue, OutputDefinition
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.assets.definition.asset_spec import AssetExecutionType
from dagster._core.definitions.data_version import CODE_VERSION_TAG, DATA_VERSION_TAG
from dagster._core.definitions.source_asset import SYSTEM_METADATA_KEY_SOURCE_ASSET_OBSERVATION
from dagster._core.definitions.utils import NoValueSentinel
from dagster._core.errors import (
    DagsterAssetCheckFailedError,
    DagsterInvariantViolationError,
    DagsterTypeCheckDidNotPass,
)
from dagster._core.events import DagsterEventType
from dagster._core.execution.context.compute import ExecutionContextTypes, enter_execution_context
from dagster._core.execution.context.system import StepExecutionContext
from dagster._core.execution.plan.aio.execute_step import (
    AssetResultOutput,
    _get_assets_def_for_step,
    _get_input_provenance_data,
    _get_output_asset_events,
    _log_materialization_or_observation_events_for_asset,
    _process_asset_results_to_events,
    _process_user_event,
    _resolve_asset_result_asset_key,
    _step_output_error_checked_user_event_sequence,
    _store_output,
    _type_check_output,
    core_dagster_event_sequence_for_step,
)
from dagster._core.execution.plan.outputs import StepOutputHandle

from dagster_tests.execution_tests.async_tests.helpers import StepContextFactory


@contextmanager
def _job_context(
    job_def: dg.JobDefinition,
    step_context_factory: StepContextFactory,
    step_key: str | None = None,
) -> Iterator[StepExecutionContext]:
    with step_context_factory(job_def, step_key) as step_context:
        yield step_context


@contextmanager
def _job_compute_context(
    job_def: dg.JobDefinition,
    step_context_factory: StepContextFactory,
    step_key: str | None = None,
) -> Iterator[tuple[StepExecutionContext, ExecutionContextTypes]]:
    with step_context_factory(job_def, step_key=step_key) as step_context:
        with enter_execution_context(step_context) as compute_context:
            yield step_context, compute_context


@pytest.mark.anyio
async def test_process_materialize_result_to_asset_result_output(
    asset_step_context: StepExecutionContext,
) -> None:
    asset_layer = asset_step_context.job_def.asset_layer
    asset_key = asset_layer.get_asset_key_for_node(asset_step_context.node_handle)
    metadata = {"label": MetadataValue.text("value")}
    tags = {"alpha": "beta"}

    async def fake_user_events():
        yield dg.MaterializeResult(
            asset_key=asset_key,
            metadata=metadata,
            tags=tags,
        )

    events = []
    async for event in _process_asset_results_to_events(asset_step_context, fake_user_events()):
        events.append(event)
    assert len(events) == 1
    output_event = events[0]
    assert isinstance(output_event, AssetResultOutput)
    assets_def = asset_step_context.job_def.asset_layer.get_assets_def_for_node(
        asset_step_context.node_handle
    )
    assert assets_def is not None
    assert output_event.output_name == assets_def.get_output_name_for_asset_key(asset_key)
    assert output_event.metadata == metadata
    assert output_event.tags == tags


@pytest.mark.anyio
async def test_process_asset_check_result_yields_output_and_evaluation(
    asset_step_context: StepExecutionContext,
) -> None:
    asset_key = asset_step_context.job_def.asset_layer.get_asset_key_for_node(
        asset_step_context.node_handle
    )
    check_key = AssetCheckKey(asset_key, "asset_check")
    check_result = dg.AssetCheckResult(
        asset_key=asset_key,
        check_name=check_key.name,
        passed=True,
    )

    events = []
    async for event in _process_user_event(asset_step_context, check_result):
        events.append(event)
    assert isinstance(events[0], dg.Output)
    expected_output_name = asset_step_context.job_def.asset_layer.get_op_output_name(check_key)
    assert events[0].output_name == expected_output_name
    assert isinstance(events[1], AssetCheckEvaluation)
    assert events[1].asset_check_key == check_key


@pytest.mark.anyio
async def test_get_assets_def_for_step_non_asset_step_raises(
    simple_step_context: StepExecutionContext,
) -> None:
    with pytest.raises(
        DagsterInvariantViolationError, match="only valid within asset computations"
    ):
        await _get_assets_def_for_step(
            simple_step_context, dg.MaterializeResult(asset_key=dg.AssetKey("a"))
        )


@pytest.mark.anyio
async def test_resolve_asset_result_asset_key_uses_asset_result_key_if_present(
    asset_step_context: StepExecutionContext,
) -> None:
    assets_def = asset_step_context.job_def.asset_layer.get_assets_def_for_node(
        asset_step_context.node_handle
    )
    assert assets_def is not None
    asset_key = assets_def.key
    materialize_result = dg.MaterializeResult(asset_key=asset_key)
    assert await _resolve_asset_result_asset_key(materialize_result, assets_def) == asset_key


@pytest.mark.anyio
async def test_resolve_asset_result_asset_key_multiple_keys_without_key_raises(
    multi_asset_step_context: StepExecutionContext,
) -> None:
    assets_def = multi_asset_step_context.job_def.asset_layer.get_assets_def_for_node(
        multi_asset_step_context.node_handle
    )
    assert assets_def is not None
    with pytest.raises(DagsterInvariantViolationError, match="did not include asset_key"):
        await _resolve_asset_result_asset_key(dg.MaterializeResult(), assets_def)


@pytest.mark.anyio
async def test_log_materialization_skips_source_asset_observation_marker(
    simple_step_context: StepExecutionContext,
) -> None:
    handle = StepOutputHandle(simple_step_context.step.key, "result")
    output = dg.Output(
        output_name="result",
        value=None,
        metadata={SYSTEM_METADATA_KEY_SOURCE_ASSET_OBSERVATION: "1"},
    )
    output_context = simple_step_context.get_output_context(handle, output.metadata)
    output_def: OutputDefinition = simple_step_context.op_def.output_def_named("result")

    events_iter = _log_materialization_or_observation_events_for_asset(
        simple_step_context,
        output_context,
        output,
        output_def,
        {},
    )
    events = []
    async for event in events_iter:
        events.append(event)

    assert events == []


@pytest.mark.anyio
async def test_step_output_sequence_emits_implicit_nothing_output(
    step_context_factory: StepContextFactory,
) -> None:
    @dg.op(out={"nothing": dg.Out(dg.Nothing)})
    def make_nothing():
        pass

    @dg.job
    def nothing_job():
        make_nothing()

    async def empty_async_iterator():
        return
        yield

    with _job_context(nothing_job, step_context_factory) as step_context:
        events_iter = _step_output_error_checked_user_event_sequence(
            step_context, empty_async_iterator()
        )

        events = []
        async for event in events_iter:
            events.append(event)

    assert len(events) == 1
    assert isinstance(events[0], dg.Output)
    assert events[0].output_name == "nothing"
    assert events[0].value is None


@pytest.mark.anyio
async def test_step_output_sequence_raises_for_unknown_output_name(
    simple_step_context: StepExecutionContext,
) -> None:
    with pytest.raises(DagsterInvariantViolationError, match="does not exist"):

        async def _async_bogus():
            yield dg.Output(1, output_name="bogus")

        events_iter = _step_output_error_checked_user_event_sequence(
            simple_step_context, _async_bogus()
        )
        events = []
        async for event in events_iter:
            events.append(event)


@pytest.mark.anyio
async def test_type_check_output_success_and_failure(
    simple_step_context: StepExecutionContext,
) -> None:
    handle = StepOutputHandle(simple_step_context.step.key, "result")
    success_output = dg.Output(1, output_name="result")
    events = [
        event async for event in _type_check_output(simple_step_context, handle, success_output)
    ]
    assert events[0].event_type == DagsterEventType.STEP_OUTPUT
    assert events[0].event_specific_data.type_check_data.success  # type: ignore  # event_specific_data is StepOutputData for STEP_OUTPUT events

    failure_output = dg.Output("bad", output_name="result")
    gen = _type_check_output(simple_step_context, handle, failure_output)
    failure_event = await anext(gen)
    assert failure_event.event_specific_data.type_check_data.success is False  # type: ignore  # event_specific_data is StepOutputData for STEP_OUTPUT events
    with pytest.raises(DagsterTypeCheckDidNotPass):
        await anext(gen)


@pytest.mark.anyio
async def test_store_output_skips_io_manager_for_nothing_output(
    step_context_factory: StepContextFactory,
) -> None:
    calls: list[object] = []

    @dg.io_manager
    def recording_io_manager(_context):
        class RecordingIOManager(dg.IOManager):
            def handle_output(self, context, obj):
                calls.append((context, obj))

            def load_input(self, context):
                raise NotImplementedError()

        return RecordingIOManager()

    @dg.op(out={"nothing": dg.Out(dg.Nothing)})
    def nothing_op():
        pass

    @dg.job(resource_defs={"io_manager": recording_io_manager})
    def job_def():
        nothing_op()

    with _job_context(job_def, step_context_factory) as step_context:
        handle = StepOutputHandle(step_context.step.key, "nothing")
        events = [
            event
            async for event in _store_output(
                step_context,
                handle,
                AssetResultOutput(output_name="nothing", value=NoValueSentinel),
            )
        ]

    assert calls == []
    assert events == []


@pytest.mark.anyio
async def test_get_output_asset_events_materialization_adds_data_version_tags(
    asset_step_context: StepExecutionContext,
) -> None:
    asset_key = asset_step_context.job_def.asset_layer.get_asset_key_for_node(
        asset_step_context.node_handle
    )
    asset_step_context.fetch_external_input_asset_version_info()
    output_def = asset_step_context.op_def.output_def_named(
        asset_step_context.step.step_outputs[0].name
    )
    output = dg.Output(output_name=output_def.name, value=1, metadata={"a": MetadataValue.int(1)})
    manager_metadata = {"extra": MetadataValue.text("x")}
    events = [
        event
        async for event in _get_output_asset_events(
            asset_key,
            [],
            output,
            output_def,
            manager_metadata,
            asset_step_context,
            AssetExecutionType.MATERIALIZATION,
        )
    ]
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, dg.AssetMaterialization)
    assert event.tags
    assert DATA_VERSION_TAG in event.tags
    assert CODE_VERSION_TAG in event.tags
    assert asset_step_context.has_data_version(asset_key)
    assert asset_step_context.get_data_version(asset_key).value == event.tags[DATA_VERSION_TAG]


@pytest.mark.anyio
async def test_get_input_provenance_data_no_dependencies_returns_empty(
    asset_step_context: StepExecutionContext,
) -> None:
    asset_key = asset_step_context.job_def.asset_layer.get_asset_key_for_node(
        asset_step_context.node_handle
    )
    assert await _get_input_provenance_data(asset_key, asset_step_context) == {}


@pytest.mark.anyio
async def test_core_dagster_event_sequence_for_step_happy_path(
    simple_step_context: StepExecutionContext,
) -> None:
    events = [event async for event in core_dagster_event_sequence_for_step(simple_step_context)]
    event_types = [event.event_type for event in events]
    assert DagsterEventType.STEP_START in event_types
    assert DagsterEventType.STEP_SUCCESS in event_types
    assert (
        DagsterEventType.STEP_OUTPUT in event_types
        or DagsterEventType.HANDLED_OUTPUT in event_types
    )


@pytest.mark.anyio
async def test_core_dagster_event_sequence_for_step_raises_on_blocking_failed_asset_check(
    step_context_factory: StepContextFactory,
) -> None:
    asset_key = dg.AssetKey("failing_asset")
    check_spec = dg.AssetCheckSpec(
        name="fail_check",
        asset=asset_key,
        blocking=True,
    )

    @dg.asset(name="failing_asset", check_specs=[check_spec])
    def failing_asset():
        yield dg.MaterializeResult(
            asset_key=asset_key,
            check_results=[
                dg.AssetCheckResult(
                    asset_key=asset_key,
                    check_name=check_spec.name,
                    passed=False,
                    severity=dg.AssetCheckSeverity.ERROR,
                )
            ],
        )

    defs = dg.Definitions(assets=[failing_asset], jobs=[dg.define_asset_job("failing_job")])
    job_def = defs.get_job_def("failing_job")

    with _job_context(job_def, step_context_factory) as step_context:
        with pytest.raises(DagsterAssetCheckFailedError) as excinfo:
            _ = [event async for event in core_dagster_event_sequence_for_step(step_context)]

    message = str(excinfo.value)
    assert "fail_check" in message
    assert asset_key.to_user_string() in message
