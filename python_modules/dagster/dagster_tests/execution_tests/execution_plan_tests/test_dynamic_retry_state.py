import time
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

import dagster as dg
import pytest
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.events import DagsterEventType
from dagster._core.execution.api import create_execution_plan, execute_plan
from dagster._core.execution.plan.handle import ResolvedFromDynamicStepHandle, StepHandle
from dagster._core.execution.plan.objects import StepFailureData, StepSuccessData
from dagster._core.execution.plan.outputs import StepOutputData, StepOutputHandle
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.storage.dagster_run import DagsterRunStatus


@pytest.fixture
def retry_instance() -> Iterator[dg.DagsterInstance]:
    with dg.DagsterInstance.ephemeral() as instance:
        yield instance


def _define_retry_job(with_optional_output: bool = False) -> dg.JobDefinition:
    @dg.op(out=dg.DynamicOut())
    def emit():
        for key in ["a", "b", "c"]:
            yield dg.DynamicOutput(key, mapping_key=key)

    @dg.op(out=dg.Out(is_required=False))
    def maybe_item(value):
        if value != "a":
            yield dg.Output(value)

    @dg.op
    def process_item(value):
        return value

    @dg.op
    def gather(values):
        return values

    @dg.job
    def retry_job():
        values = emit()
        if with_optional_output:
            values = values.map(maybe_item)
        gather(values.map(process_item).collect())

    return retry_job


def _event(
    job_name: str,
    step_key: str,
    event_type: DagsterEventType,
    *,
    mapping_key: str | None = None,
    output_name: str = "result",
) -> dg.DagsterEvent:
    """Create typed step events, including resolved handles for mapped siblings."""
    handle = StepHandle.parse_from_key(step_key)
    assert isinstance(handle, (StepHandle, ResolvedFromDynamicStepHandle))
    data = None
    if event_type == DagsterEventType.STEP_OUTPUT:
        data = StepOutputData(
            StepOutputHandle(step_key, output_name=output_name, mapping_key=mapping_key)
        )
    elif event_type == DagsterEventType.STEP_SUCCESS:
        data = StepSuccessData(duration_ms=1.0)
    elif event_type == DagsterEventType.STEP_FAILURE:
        data = StepFailureData(error=None, user_failure_data=None)
    return dg.DagsterEvent(
        event_type.value,
        job_name=job_name,
        step_handle=handle,
        node_handle=handle.node_handle,
        event_specific_data=data,
    )


def _successful_step_events(
    job_name: str,
    step_key: str,
    *,
    mapping_keys: Sequence[str] | None = None,
    emit_output: bool = True,
) -> list[dg.DagsterEvent]:
    events = [_event(job_name, step_key, DagsterEventType.STEP_START)]
    if emit_output:
        events.extend(
            _event(
                job_name,
                step_key,
                DagsterEventType.STEP_OUTPUT,
                mapping_key=mapping_key,
            )
            for mapping_key in (mapping_keys if mapping_keys is not None else [None])
        )
    events.append(_event(job_name, step_key, DagsterEventType.STEP_SUCCESS))
    return events


def _retry_state(
    instance: dg.DagsterInstance,
    job: dg.JobDefinition,
    events: Sequence[dg.DagsterEvent],
    **run_kwargs: Any,
) -> tuple[Sequence[str], KnownExecutionState]:
    """Store a real plan snapshot and a synthetic failed run's ordered event history."""
    run = instance.create_run_for_job(job, status=DagsterRunStatus.FAILURE, **run_kwargs)
    for index, event in enumerate(events):
        instance.event_log_storage.store_event(
            dg.EventLogEntry(
                error_info=None,
                user_message="",
                level="debug",
                run_id=run.run_id,
                timestamp=float(index),
                step_key=event.step_key,
                job_name=job.name,
                dagster_event=event,
            )
        )
    return KnownExecutionState.build_resume_retry_reexecution(instance, run)


@pytest.mark.parametrize(
    "completed_keys,interrupted_key",
    [([], None), (["a"], None), (["a"], "b")],
    ids=["before-mapping", "between-siblings", "during-sibling"],
)
def test_retry_state_includes_unstarted_dynamic_siblings(
    retry_instance: dg.DagsterInstance,
    completed_keys: list[str],
    interrupted_key: str | None,
) -> None:
    job = _define_retry_job()
    events = [
        *_successful_step_events(job.name, "emit", mapping_keys=["a", "b", "c"]),
    ]
    for key in completed_keys:
        events.extend(_successful_step_events(job.name, f"process_item[{key}]"))
    if interrupted_key:
        events.append(
            _event(job.name, f"process_item[{interrupted_key}]", DagsterEventType.STEP_START)
        )

    steps, state = _retry_state(retry_instance, job, events)

    assert set(steps) == {
        *(f"process_item[{key}]" for key in ["a", "b", "c"] if key not in completed_keys),
        "gather",
    }
    assert len(steps) == 4 - len(completed_keys)
    assert state.dynamic_mappings == {"emit": {"result": ["a", "b", "c"]}}
    assert state.parent_state is not None
    assert state.parent_state.produced_outputs == {
        *(StepOutputHandle("emit", mapping_key=key) for key in ["a", "b", "c"]),
        *(StepOutputHandle(f"process_item[{key}]") for key in completed_keys),
    }


def test_retry_state_skipped_sibling_does_not_hide_pending_siblings(
    retry_instance: dg.DagsterInstance,
) -> None:
    job = _define_retry_job(with_optional_output=True)
    events = [
        *_successful_step_events(job.name, "emit", mapping_keys=["a", "b", "c"]),
        *_successful_step_events(job.name, "maybe_item[a]", emit_output=False),
        _event(job.name, "process_item[a]", DagsterEventType.STEP_SKIPPED),
        *_successful_step_events(job.name, "maybe_item[b]"),
        _event(job.name, "process_item[b]", DagsterEventType.STEP_START),
        *_successful_step_events(job.name, "maybe_item[c]"),
    ]

    steps, state = _retry_state(retry_instance, job, events)

    assert set(steps) == {"process_item[b]", "process_item[c]", "gather"}
    assert len(steps) == 3
    assert state.dynamic_mappings == {"emit": {"result": ["a", "b", "c"]}}
    assert state.parent_state is not None
    assert StepOutputHandle("maybe_item[a]") not in state.parent_state.produced_outputs


@pytest.mark.parametrize("producer_failed", [True, False], ids=["failed", "interrupted"])
def test_retry_state_discards_partial_mappings_of_retried_producer(
    retry_instance: dg.DagsterInstance, producer_failed: bool
) -> None:
    job = _define_retry_job()
    events = [
        _event(job.name, "emit", DagsterEventType.STEP_START),
        _event(job.name, "emit", DagsterEventType.STEP_OUTPUT, mapping_key="a"),
    ]
    if producer_failed:
        events.append(_event(job.name, "emit", DagsterEventType.STEP_FAILURE))

    steps, state = _retry_state(retry_instance, job, events)

    # The new producer attempt must determine its own mapping keys.
    assert set(steps) == {"emit", "process_item[?]", "gather"}
    assert len(steps) == 3
    assert state.dynamic_mappings == {}


def test_retry_state_does_not_retry_completed_dynamic_siblings(
    retry_instance: dg.DagsterInstance,
) -> None:
    job = _define_retry_job()
    events = _successful_step_events(job.name, "emit", mapping_keys=["a", "b", "c"])
    for key in ["a", "b", "c"]:
        events.extend(_successful_step_events(job.name, f"process_item[{key}]"))
    events.extend(_successful_step_events(job.name, "gather"))

    # A run may fail during finalization after all its steps have succeeded.
    steps, state = _retry_state(retry_instance, job, events)

    assert steps == []
    assert state.dynamic_mappings == {"emit": {"result": ["a", "b", "c"]}}
    assert state.parent_state is not None
    assert state.parent_state.produced_outputs == {
        *(StepOutputHandle("emit", mapping_key=key) for key in ["a", "b", "c"]),
        *(StepOutputHandle(f"process_item[{key}]") for key in ["a", "b", "c"]),
        StepOutputHandle("gather"),
    }


def _define_two_output_retry_job() -> dg.JobDefinition:
    @dg.op(out={"left": dg.DynamicOut(), "right": dg.DynamicOut()})
    def emit_two():
        for output_name, keys in [("left", ["a", "b", "c"]), ("right", ["x", "y", "z"])]:
            for key in keys:
                yield dg.DynamicOutput(key, mapping_key=key, output_name=output_name)

    @dg.op
    def process_item(value):
        return value

    @dg.op
    def gather(values):
        return values

    @dg.job
    def two_output_job():
        left, right = emit_two()
        gather.alias("left_gather")(left.map(process_item.alias("left_item")).collect())
        gather.alias("right_gather")(right.map(process_item.alias("right_item")).collect())

    return two_output_job


@pytest.mark.parametrize("pending_output", ["left", "right"])
def test_retry_state_uses_mapping_keys_from_the_matching_dynamic_output(
    retry_instance: dg.DagsterInstance, pending_output: str
) -> None:
    job = _define_two_output_retry_job()
    mappings = {"left": ["a", "b", "c"], "right": ["x", "y", "z"]}
    events = [_event(job.name, "emit_two", DagsterEventType.STEP_START)]
    for output_name, keys in mappings.items():
        events.extend(
            _event(
                job.name,
                "emit_two",
                DagsterEventType.STEP_OUTPUT,
                output_name=output_name,
                mapping_key=key,
            )
            for key in keys
        )
    events.append(_event(job.name, "emit_two", DagsterEventType.STEP_SUCCESS))
    for output_name, keys in mappings.items():
        if output_name == pending_output:
            events.extend(_successful_step_events(job.name, f"{output_name}_item[{keys[0]}]"))
            events.append(
                _event(job.name, f"{output_name}_item[{keys[1]}]", DagsterEventType.STEP_START)
            )
        else:
            for key in keys:
                events.extend(_successful_step_events(job.name, f"{output_name}_item[{key}]"))
            events.extend(_successful_step_events(job.name, f"{output_name}_gather"))

    steps, state = _retry_state(retry_instance, job, events)

    assert set(steps) == {
        *(f"{pending_output}_item[{key}]" for key in mappings[pending_output][1:]),
        f"{pending_output}_gather",
    }
    assert len(steps) == 3
    assert state.dynamic_mappings == {"emit_two": mappings}


def _define_empty_dynamic_job(is_required: bool) -> dg.JobDefinition:
    @dg.op(out=dg.DynamicOut(is_required=is_required))
    def emit():
        yield from ()

    @dg.op
    def process_item(value):
        return value

    @dg.op
    def gather(values):
        return values

    @dg.job
    def empty_dynamic_job():
        gather(emit().map(process_item).collect())

    return empty_dynamic_job


@pytest.mark.parametrize("is_required", [True, False], ids=["empty", "omitted"])
def test_retry_state_does_not_invent_steps_for_empty_or_omitted_mappings(
    retry_instance: dg.DagsterInstance, is_required: bool
) -> None:
    job = _define_empty_dynamic_job(is_required)
    events = _successful_step_events(job.name, "emit", emit_output=False)
    if is_required:
        # A required output with zero values collects to an empty list.
        events.extend(_successful_step_events(job.name, "gather"))
    else:
        # An omitted optional dynamic output propagates a skip to the collector.
        events.append(_event(job.name, "gather", DagsterEventType.STEP_SKIPPED))

    steps, state = _retry_state(retry_instance, job, events)

    assert steps == []
    assert state.dynamic_mappings == {"emit": {"result": [] if is_required else None}}


def _define_static_dependency_retry_job() -> dg.JobDefinition:
    @dg.op(out=dg.DynamicOut())
    def emit():
        for key in ["a", "b", "c"]:
            yield dg.DynamicOutput(key, mapping_key=key)

    @dg.op
    def static_value():
        return "static"

    @dg.op
    def process_item(value, shared):
        return (value, shared)

    @dg.op
    def gather(values):
        return values

    @dg.job
    def static_dependency_job():
        shared = static_value()
        gather(emit().map(lambda value: process_item(value, shared)).collect())

    return static_dependency_job


def test_retry_state_does_not_mix_resolved_and_unresolved_steps_for_static_retry(
    retry_instance: dg.DagsterInstance,
) -> None:
    job = _define_static_dependency_retry_job()
    events = [
        *_successful_step_events(job.name, "emit", mapping_keys=["a", "b", "c"]),
        _event(job.name, "static_value", DagsterEventType.STEP_START),
        _event(job.name, "static_value", DagsterEventType.STEP_FAILURE),
    ]

    steps, state = _retry_state(retry_instance, job, events)

    assert set(steps) == {"static_value", "process_item[?]", "gather"}
    assert len(steps) == 3
    assert state.dynamic_mappings == {"emit": {"result": ["a", "b", "c"]}}


def test_retry_state_uses_inherited_mappings_after_retrying_a_static_dependency(
    retry_instance: dg.DagsterInstance,
) -> None:
    job = _define_static_dependency_retry_job()
    first_events = [
        *_successful_step_events(job.name, "emit", mapping_keys=["a", "b", "c"]),
        _event(job.name, "static_value", DagsterEventType.STEP_START),
        _event(job.name, "static_value", DagsterEventType.STEP_FAILURE),
    ]
    first_steps, first_state = _retry_state(retry_instance, job, first_events)
    assert set(first_steps) == {"static_value", "process_item[?]", "gather"}
    assert first_state.parent_state is not None
    first_run_id = first_state.parent_state.run_id

    retry_plan = create_execution_plan(
        job,
        step_keys_to_execute=first_steps,
        known_state=first_state,
    )
    assert "process_item[?]" in retry_plan.step_keys_to_execute
    assert "emit" not in retry_plan.step_keys_to_execute
    second_events = [
        *_successful_step_events(job.name, "static_value"),
        *_successful_step_events(job.name, "process_item[a]"),
        _event(job.name, "process_item[b]", DagsterEventType.STEP_START),
    ]

    steps, state = _retry_state(
        retry_instance,
        job,
        second_events,
        execution_plan=retry_plan,
        parent_run_id=first_run_id,
        root_run_id=first_run_id,
    )

    assert state.parent_state is not None
    second_run = retry_instance.get_run_by_id(state.parent_state.run_id)
    assert second_run is not None
    assert second_run.execution_plan_snapshot_id is not None
    snapshot = retry_instance.get_execution_plan_snapshot(second_run.execution_plan_snapshot_id)
    assert snapshot is not None
    assert snapshot.initial_known_state is not None
    assert snapshot.initial_known_state.dynamic_mappings == {"emit": {"result": ["a", "b", "c"]}}
    # The second history has no emitter events: its plan must supply the pending mapping key.
    assert set(steps) == {"process_item[b]", "process_item[c]", "gather"}
    assert len(steps) == 3
    assert state.dynamic_mappings == {"emit": {"result": ["a", "b", "c"]}}
    assert state.parent_state.get_parent_state() == first_state.parent_state


def define_dynamic_retry_e2e_job() -> dg.JobDefinition:
    @dg.op(out=dg.DynamicOut())
    def emit():
        for key in ["a", "b", "c"]:
            yield dg.DynamicOutput(key, mapping_key=key)

    @dg.op
    def process_item(value):
        return value

    @dg.op
    def gather(values):
        return values

    @dg.job(
        executor_def=dg.in_process_executor,
        resource_defs={"io_manager": dg.fs_io_manager},
    )
    def dynamic_retry_e2e_job():
        gather(emit().map(process_item).collect())

    return dynamic_retry_e2e_job


def test_retry_executes_pending_dynamic_sibling_and_reuses_completed_output(tmp_path: Path) -> None:
    job = define_dynamic_retry_e2e_job()
    run_config = {"resources": {"io_manager": {"config": {"base_dir": str(tmp_path)}}}}
    full_plan = create_execution_plan(job, run_config=run_config)

    with dg.instance_for_test() as instance:
        # Keep the complete original selection in the persisted run snapshot.
        parent = instance.create_run_for_job(
            job,
            execution_plan=full_plan,
            run_config=run_config,
            status=DagsterRunStatus.STARTED,
        )
        emit_plan = create_execution_plan(job, run_config=run_config, step_keys_to_execute=["emit"])
        emit_events = execute_plan(
            emit_plan,
            InMemoryJob(job),
            instance,
            parent,
            run_config=run_config,
        )
        assert {event.step_key for event in emit_events if event.is_step_success} == {"emit"}
        assert not any(event.is_step_failure for event in emit_events)

        producer_state = KnownExecutionState.build_for_reexecution(instance, parent)
        assert producer_state.dynamic_mappings == {"emit": {"result": ["a", "b", "c"]}}
        first_item_plan = create_execution_plan(
            job,
            run_config=run_config,
            step_keys_to_execute=["process_item[a]"],
            known_state=producer_state,
        )
        first_item_events = execute_plan(
            first_item_plan,
            InMemoryJob(job),
            instance,
            parent,
            run_config=run_config,
        )
        assert {event.step_key for event in first_item_events if event.is_step_success} == {
            "process_item[a]"
        }
        assert not any(event.is_step_failure for event in first_item_events)
        assert parent.execution_plan_snapshot_id is not None
        snapshot = instance.get_execution_plan_snapshot(parent.execution_plan_snapshot_id)
        assert snapshot is not None
        assert set(snapshot.step_keys_to_execute) == {"emit", "process_item[?]", "gather"}

        # Model the event history of an unfinished b; no operation is interrupted.
        unfinished_handle = StepHandle.parse_from_key("process_item[b]")
        assert isinstance(unfinished_handle, ResolvedFromDynamicStepHandle)
        instance.event_log_storage.store_event(
            dg.EventLogEntry(
                error_info=None,
                user_message="",
                level="debug",
                run_id=parent.run_id,
                timestamp=time.time(),
                step_key="process_item[b]",
                job_name=job.name,
                dagster_event=dg.DagsterEvent(
                    DagsterEventType.STEP_START.value,
                    job_name=job.name,
                    step_handle=unfinished_handle,
                    node_handle=unfinished_handle.node_handle,
                ),
            )
        )
        instance.report_run_failed(parent)
        options = dg.ReexecutionOptions.from_failure(parent.run_id, instance)

        with dg.execute_job(
            dg.reconstructable(define_dynamic_retry_e2e_job),
            instance=instance,
            run_config=run_config,
            reexecution_options=options,
            raise_on_error=True,
        ) as result:
            assert result.success
            assert result.output_for_node("gather") == ["a", "b", "c"]
            retry_started = [event.step_key for event in result.all_events if event.is_step_start]
            assert set(retry_started) == {"process_item[b]", "process_item[c]", "gather"}
            assert len(retry_started) == 3
            assert {event.step_key for event in result.all_events if event.is_step_success} == {
                "process_item[b]",
                "process_item[c]",
                "gather",
            }
