from contextlib import contextmanager

import dagster as dg
import pytest
from dagster._core.definitions import AssetCheckEvaluation, MetadataValue, OutputDefinition
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.assets.definition.asset_spec import AssetExecutionType
from dagster._core.definitions.data_version import (
    CODE_VERSION_TAG,
    DATA_VERSION_IS_USER_PROVIDED_TAG,
    DATA_VERSION_TAG,
    NULL_EVENT_POINTER,
    DataVersion,
    get_input_data_version_tag,
    get_input_event_pointer_tag,
)
from dagster._core.definitions.source_asset import SYSTEM_METADATA_KEY_SOURCE_ASSET_OBSERVATION
from dagster._core.definitions.utils import NoValueSentinel
from dagster._core.errors import (
    DagsterAssetCheckFailedError,
    DagsterInvariantViolationError,
    DagsterTypeCheckDidNotPass,
)
from dagster._core.events import DagsterEventType
from dagster._core.execution.context.compute import enter_execution_context
from dagster._core.execution.plan.execute_step import (
    AssetResultOutput,
    _build_data_version_observation_tags,
    _build_data_version_tags,
    _dagster_event_for_asset_event,
    _get_assets_def_for_step,
    _get_code_version,
    _get_input_provenance_data,
    _get_output_asset_events,
    _InputProvenanceData,
    _log_materialization_or_observation_events_for_asset,
    _process_asset_results_to_events,
    _process_user_event,
    _resolve_asset_result_asset_key,
    _step_output_error_checked_user_event_sequence,
    _store_output,
    _type_check_and_store_output,
    _type_check_output,
    _type_checked_event_sequence_for_input,
    core_dagster_event_sequence_for_step,
    do_type_check,
)
from dagster._core.execution.plan.outputs import StepOutputHandle


@contextmanager
def _job_context(job_def: dg.JobDefinition, step_context_factory, step_key: str | None = None):
    with step_context_factory(job_def, step_key=step_key) as step_context:
        yield step_context


@contextmanager
def _job_compute_context(
    job_def: dg.JobDefinition, step_context_factory, step_key: str | None = None
):
    with step_context_factory(job_def, step_key=step_key) as step_context:
        with enter_execution_context(step_context) as compute_context:
            yield step_context, compute_context


def test_process_materialize_result_to_asset_result_output(asset_step_context):
    asset_key = asset_step_context.job_def.asset_layer.get_asset_key_for_node(
        asset_step_context.node_handle
    )
    metadata = {"label": MetadataValue.text("value")}
    tags = {"alpha": "beta"}
    materialize_result = dg.MaterializeResult(
        asset_key=asset_key,
        metadata=metadata,
        tags=tags,
    )
    events = list(_process_asset_results_to_events(asset_step_context, iter([materialize_result])))
    assert len(events) == 1
    output_event = events[0]
    assert isinstance(output_event, AssetResultOutput)
    assets_def = asset_step_context.job_def.asset_layer.get_assets_def_for_node(
        asset_step_context.node_handle
    )
    assert output_event.output_name == assets_def.get_output_name_for_asset_key(asset_key)
    assert output_event.metadata == metadata
    assert output_event.tags == tags


def test_process_asset_check_result_yields_output_and_evaluation(asset_step_context):
    asset_key = asset_step_context.job_def.asset_layer.get_asset_key_for_node(
        asset_step_context.node_handle
    )
    check_key = AssetCheckKey(asset_key, "asset_check")
    check_result = dg.AssetCheckResult(
        asset_key=asset_key,
        check_name=check_key.name,
        passed=True,
    )

    events = list(_process_user_event(asset_step_context, check_result))
    assert isinstance(events[0], dg.Output)
    expected_output_name = asset_step_context.job_def.asset_layer.get_op_output_name(check_key)
    assert events[0].output_name == expected_output_name
    assert isinstance(events[1], AssetCheckEvaluation)
    assert events[1].asset_check_key == check_key


def test_get_assets_def_for_step_non_asset_step_raises(simple_step_context):
    with pytest.raises(
        DagsterInvariantViolationError, match="only valid within asset computations"
    ):
        _get_assets_def_for_step(
            simple_step_context, dg.MaterializeResult(asset_key=dg.AssetKey("a"))
        )


def test_resolve_asset_result_asset_key_uses_asset_result_key_if_present(asset_step_context):
    assets_def = asset_step_context.job_def.asset_layer.get_assets_def_for_node(
        asset_step_context.node_handle
    )
    asset_key = assets_def.key
    materialize_result = dg.MaterializeResult(asset_key=asset_key)
    assert _resolve_asset_result_asset_key(materialize_result, assets_def) == asset_key


def test_resolve_asset_result_asset_key_multiple_keys_without_key_raises(
    multi_asset_step_context,
):
    assets_def = multi_asset_step_context.job_def.asset_layer.get_assets_def_for_node(
        multi_asset_step_context.node_handle
    )
    with pytest.raises(DagsterInvariantViolationError, match="did not include asset_key"):
        _resolve_asset_result_asset_key(dg.MaterializeResult(), assets_def)


def test_dagster_event_for_asset_materialization_and_observation(simple_step_context):
    materialization = dg.AssetMaterialization("asset")
    observation = dg.AssetObservation("asset")
    mat_event = _dagster_event_for_asset_event(simple_step_context, materialization, None)
    obs_event = _dagster_event_for_asset_event(simple_step_context, observation, None)
    assert mat_event.event_type == DagsterEventType.ASSET_MATERIALIZATION
    assert obs_event.event_type == DagsterEventType.ASSET_OBSERVATION


def test_log_materialization_skips_source_asset_observation_marker(simple_step_context):
    handle = StepOutputHandle(simple_step_context.step.key, "result")
    output = dg.Output(
        output_name="result",
        value=None,
        metadata={SYSTEM_METADATA_KEY_SOURCE_ASSET_OBSERVATION: "1"},
    )
    output_context = simple_step_context.get_output_context(handle, output.metadata)
    output_def: OutputDefinition = simple_step_context.op_def.output_def_named("result")
    events = list(
        _log_materialization_or_observation_events_for_asset(
            simple_step_context,
            output_context,
            output,
            output_def,
            {},
        )
    )
    assert events == []


def test_step_output_sequence_emits_implicit_nothing_output(step_context_factory):
    @dg.op(out={"nothing": dg.Out(dg.Nothing)})
    def make_nothing():
        pass

    @dg.job
    def nothing_job():
        make_nothing()

    with _job_context(nothing_job, step_context_factory) as step_context:
        events = list(_step_output_error_checked_user_event_sequence(step_context, iter([])))

    assert len(events) == 1
    assert isinstance(events[0], dg.Output)
    assert events[0].output_name == "nothing"
    assert events[0].value is None


def test_step_output_sequence_raises_for_unknown_output_name(simple_step_context):
    with pytest.raises(DagsterInvariantViolationError, match="does not exist"):
        list(
            _step_output_error_checked_user_event_sequence(
                simple_step_context, iter([dg.Output(1, output_name="bogus")])
            )
        )


def test_do_type_check_delegates_to_dagster_type(simple_step_context):
    dagster_type = simple_step_context.op_def.output_defs[0].dagster_type
    context = simple_step_context.for_type(dagster_type)
    type_check = do_type_check(context, dagster_type, 5)
    assert type_check.success


def test_type_checked_event_sequence_for_input_success_and_failure(step_context_factory):
    @dg.op
    def takes_input(x: int) -> int:
        return x

    @dg.op
    def emit_value() -> int:
        return 1

    @dg.job
    def input_job():
        takes_input(emit_value())

    with _job_context(input_job, step_context_factory, step_key="takes_input") as step_context:
        success_gen = _type_checked_event_sequence_for_input(step_context, "x", 5)
        success_event = next(success_gen)
        assert success_event.event_type == DagsterEventType.STEP_INPUT
        assert success_event.event_specific_data.type_check_data.success  # type: ignore  # event_specific_data has type_check_data for STEP_INPUT events

        failure_gen = _type_checked_event_sequence_for_input(step_context, "x", "bad")
        failure_event = next(failure_gen)
        assert failure_event.event_specific_data.type_check_data.success is False  # type: ignore  # event_specific_data has type_check_data for STEP_INPUT events
        with pytest.raises(DagsterTypeCheckDidNotPass):
            next(failure_gen)


def test_type_check_output_success_and_failure(simple_step_context):
    handle = StepOutputHandle(simple_step_context.step.key, "result")
    success_output = dg.Output(1, output_name="result")
    events = list(_type_check_output(simple_step_context, handle, success_output))
    assert events[0].event_type == DagsterEventType.STEP_OUTPUT
    assert events[0].event_specific_data.type_check_data.success  # type: ignore  # event_specific_data is StepOutputData for STEP_OUTPUT events

    failure_output = dg.Output("bad", output_name="result")
    gen = _type_check_output(simple_step_context, handle, failure_output)
    failure_event = next(gen)
    assert failure_event.event_specific_data.type_check_data.success is False  # type: ignore  # event_specific_data is StepOutputData for STEP_OUTPUT events
    with pytest.raises(DagsterTypeCheckDidNotPass):
        next(gen)


def test_type_check_and_store_output_calls_io_manager_and_emits_handled_output(
    step_context_factory,
):
    calls: list[tuple[str, object]] = []

    @dg.io_manager
    def recording_io_manager(_context):
        class RecordingIOManager(dg.IOManager):
            def handle_output(self, context, obj):
                calls.append((context.name, obj))

            def load_input(self, context):
                raise NotImplementedError()

        return RecordingIOManager()

    @dg.op
    def produce() -> int:
        return 5

    @dg.job(resource_defs={"io_manager": recording_io_manager})
    def job_def():
        produce()

    with _job_context(job_def, step_context_factory) as step_context:
        events = list(_type_check_and_store_output(step_context, dg.Output(5)))

    assert len(calls) == 1
    assert calls[0][0] == "result"
    assert calls[0][1] == 5
    event_types = [event.event_type for event in events]
    assert DagsterEventType.STEP_OUTPUT in event_types
    assert DagsterEventType.HANDLED_OUTPUT in event_types


def test_store_output_skips_io_manager_for_nothing_output(step_context_factory):
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
        events = list(
            _store_output(
                step_context,
                handle,
                AssetResultOutput(output_name="nothing", value=NoValueSentinel),
            )
        )

    assert calls == []
    assert events == []


def test_get_output_asset_events_materialization_adds_data_version_tags(asset_step_context):
    asset_key = asset_step_context.job_def.asset_layer.get_asset_key_for_node(
        asset_step_context.node_handle
    )
    asset_step_context.fetch_external_input_asset_version_info()
    output_def = asset_step_context.op_def.output_def_named(
        asset_step_context.step.step_outputs[0].name
    )
    output = dg.Output(output_name=output_def.name, value=1, metadata={"a": MetadataValue.int(1)})
    manager_metadata = {"extra": MetadataValue.text("x")}
    events = list(
        _get_output_asset_events(
            asset_key,
            [],
            output,
            output_def,
            manager_metadata,
            asset_step_context,
            AssetExecutionType.MATERIALIZATION,
        )
    )
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, dg.AssetMaterialization)
    assert event.tags
    assert DATA_VERSION_TAG in event.tags
    assert CODE_VERSION_TAG in event.tags
    assert asset_step_context.has_data_version(asset_key)
    assert asset_step_context.get_data_version(asset_key).value == event.tags[DATA_VERSION_TAG]


def test_get_code_version_prefers_asset_code_version(step_context_factory):
    @dg.asset(code_version="abc")
    def coded_asset():
        return 1

    defs = dg.Definitions(assets=[coded_asset], jobs=[dg.define_asset_job("coded_job")])
    job_def = defs.get_job_def("coded_job")

    with _job_context(job_def, step_context_factory) as step_context:
        asset_key = step_context.job_def.asset_layer.get_asset_key_for_node(
            step_context.node_handle
        )
        assert _get_code_version(asset_key, step_context) == "abc"


def test_get_code_version_falls_back_to_run_id(asset_step_context):
    asset_key = asset_step_context.job_def.asset_layer.get_asset_key_for_node(
        asset_step_context.node_handle
    )
    assert _get_code_version(asset_key, asset_step_context) == asset_step_context.dagster_run.run_id


def test_get_input_provenance_data_no_dependencies_returns_empty(asset_step_context):
    asset_key = asset_step_context.job_def.asset_layer.get_asset_key_for_node(
        asset_step_context.node_handle
    )
    assert _get_input_provenance_data(asset_key, asset_step_context) == {}


def test_build_data_version_tags_populates_expected_keys():
    dv = DataVersion("1")
    code_version = "abc"
    key1 = dg.AssetKey("a")
    key2 = dg.AssetKey("b")
    input_provenance: dict[dg.AssetKey, _InputProvenanceData] = {
        key1: _InputProvenanceData(data_version=DataVersion("2"), storage_id=10),
        key2: _InputProvenanceData(data_version=DataVersion("3"), storage_id=None),
    }
    tags = _build_data_version_tags(dv, code_version, input_provenance, False)
    assert tags[CODE_VERSION_TAG] == "abc"
    assert tags[get_input_data_version_tag(key1)] == "2"
    assert tags[get_input_event_pointer_tag(key1)] == "10"
    assert tags[get_input_event_pointer_tag(key2)] == NULL_EVENT_POINTER
    assert tags[DATA_VERSION_TAG] == "1"
    assert DATA_VERSION_IS_USER_PROVIDED_TAG not in tags


def test_build_data_version_observation_tags_marks_user_provided():
    tags = _build_data_version_observation_tags(DataVersion("1"))
    assert tags[DATA_VERSION_TAG] == "1"
    assert tags[DATA_VERSION_IS_USER_PROVIDED_TAG] == "true"


def test_core_dagster_event_sequence_for_step_happy_path(simple_step_context):
    events = list(core_dagster_event_sequence_for_step(simple_step_context))
    event_types = [event.event_type for event in events]
    assert DagsterEventType.STEP_START in event_types
    assert DagsterEventType.STEP_SUCCESS in event_types
    assert (
        DagsterEventType.STEP_OUTPUT in event_types
        or DagsterEventType.HANDLED_OUTPUT in event_types
    )


def test_core_dagster_event_sequence_for_step_raises_on_blocking_failed_asset_check(
    step_context_factory,
):
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
            list(core_dagster_event_sequence_for_step(step_context))

    message = str(excinfo.value)
    assert "fail_check" in message
    assert asset_key.to_user_string() in message
