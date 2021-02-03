# pylint doesn't know about pytest fixtures
# pylint: disable=unused-argument

import os
import tempfile
from threading import Thread

import pytest
from dagster import (
    CompositeSolidExecutionResult,
    PipelineExecutionResult,
    SolidExecutionResult,
    execute_pipeline,
    execute_pipeline_iterator,
    seven,
)
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.errors import DagsterExecutionInterruptedError, DagsterSubprocessError
from dagster.core.events import DagsterEventType
from dagster.core.test_utils import instance_for_test, instance_for_test_tempdir
from dagster.utils import send_interrupt
from dagster_celery_tests.repo import COMPOSITE_DEPTH
from dagster_celery_tests.utils import start_celery_worker

from .utils import (  # isort:skip
    execute_eagerly_on_celery,
    execute_pipeline_on_celery,
    events_of_type,
    REPO_FILE,
)


def test_execute_on_celery_default(dagster_celery_worker):
    with execute_pipeline_on_celery("test_pipeline") as result:
        assert result.result_for_solid("simple").output_value() == 1
        assert len(result.step_event_list) == 4
        assert len(events_of_type(result, "STEP_START")) == 1
        assert len(events_of_type(result, "STEP_OUTPUT")) == 1
        assert len(events_of_type(result, "HANDLED_OUTPUT")) == 1
        assert len(events_of_type(result, "STEP_SUCCESS")) == 1


def test_execute_serial_on_celery(dagster_celery_worker):
    with execute_pipeline_on_celery("test_serial_pipeline") as result:
        assert result.result_for_solid("simple").output_value() == 1
        assert result.result_for_solid("add_one").output_value() == 2
        assert len(result.step_event_list) == 10
        assert len(events_of_type(result, "STEP_START")) == 2
        assert len(events_of_type(result, "STEP_INPUT")) == 1
        assert len(events_of_type(result, "STEP_OUTPUT")) == 2
        assert len(events_of_type(result, "HANDLED_OUTPUT")) == 2
        assert len(events_of_type(result, "LOADED_INPUT")) == 1
        assert len(events_of_type(result, "STEP_SUCCESS")) == 2


def test_execute_diamond_pipeline_on_celery(dagster_celery_worker):
    with execute_pipeline_on_celery("test_diamond_pipeline") as result:
        assert result.result_for_solid("emit_values").output_values == {
            "value_one": 1,
            "value_two": 2,
        }
        assert result.result_for_solid("add_one").output_value() == 2
        assert result.result_for_solid("renamed").output_value() == 3
        assert result.result_for_solid("subtract").output_value() == -1


def test_execute_parallel_pipeline_on_celery(dagster_celery_worker):
    with execute_pipeline_on_celery("test_parallel_pipeline") as result:
        assert len(result.solid_result_list) == 11


def test_execute_composite_pipeline_on_celery(dagster_celery_worker):
    with execute_pipeline_on_celery("composite_pipeline") as result:
        assert result.success
        assert isinstance(result, PipelineExecutionResult)
        assert len(result.solid_result_list) == 1
        composite_solid_result = result.solid_result_list[0]
        assert len(composite_solid_result.solid_result_list) == 2
        for r in composite_solid_result.solid_result_list:
            assert isinstance(r, CompositeSolidExecutionResult)
        composite_solid_results = composite_solid_result.solid_result_list
        for i in range(COMPOSITE_DEPTH):
            next_level = []
            assert len(composite_solid_results) == pow(2, i + 1)
            for res in composite_solid_results:
                assert isinstance(res, CompositeSolidExecutionResult)
                for r in res.solid_result_list:
                    next_level.append(r)
            composite_solid_results = next_level
        assert len(composite_solid_results) == pow(2, COMPOSITE_DEPTH + 1)
        assert all(
            (isinstance(r, SolidExecutionResult) and r.success for r in composite_solid_results)
        )


def test_execute_optional_outputs_pipeline_on_celery(dagster_celery_worker):
    with execute_pipeline_on_celery("test_optional_outputs") as result:
        assert len(result.solid_result_list) == 4
        assert sum([int(x.skipped) for x in result.solid_result_list]) == 2
        assert sum([int(x.success) for x in result.solid_result_list]) == 2


def test_execute_fails_pipeline_on_celery(dagster_celery_worker):
    with execute_pipeline_on_celery("test_fails") as result:
        assert len(result.solid_result_list) == 2  # fail & skip
        assert not result.result_for_solid("fails").success
        assert (
            result.result_for_solid("fails").failure_data.error.message == "Exception: argjhgjh\n"
        )
        assert result.result_for_solid("should_never_execute").skipped


def test_terminate_pipeline_on_celery(rabbitmq):
    with start_celery_worker():
        with tempfile.TemporaryDirectory() as tempdir:
            pipeline_def = ReconstructablePipeline.for_file(REPO_FILE, "interrupt_pipeline")

            with instance_for_test_tempdir(tempdir) as instance:
                run_config = {
                    "intermediate_storage": {"filesystem": {"config": {"base_dir": tempdir}}},
                    "execution": {"celery": {}},
                }

                results = []
                result_types = []
                interrupt_thread = None
                received_interrupt = False

                try:
                    for result in execute_pipeline_iterator(
                        pipeline=pipeline_def,
                        run_config=run_config,
                        instance=instance,
                    ):
                        # Interrupt once the first step starts
                        if (
                            result.event_type == DagsterEventType.STEP_START
                            and not interrupt_thread
                        ):
                            interrupt_thread = Thread(target=send_interrupt, args=())
                            interrupt_thread.start()

                        results.append(result)
                        result_types.append(result.event_type)

                    assert False
                except DagsterExecutionInterruptedError:
                    received_interrupt = True

                interrupt_thread.join()

                assert received_interrupt

                # At least one step succeeded (the one that was running when the interrupt fired)
                assert DagsterEventType.STEP_SUCCESS in result_types

                # At least one step was revoked (and there were no step failure events)
                revoke_steps = [
                    result
                    for result in results
                    if result.event_type == DagsterEventType.ENGINE_EVENT
                    and "was revoked." in result.message
                ]

                assert len(revoke_steps) > 0

            # The overall pipeline failed
            assert DagsterEventType.PIPELINE_FAILURE in result_types


def test_execute_eagerly_on_celery():
    with instance_for_test() as instance:
        with execute_eagerly_on_celery("test_pipeline", instance=instance) as result:
            assert result.result_for_solid("simple").output_value() == 1
            assert len(result.step_event_list) == 4
            assert len(events_of_type(result, "STEP_START")) == 1
            assert len(events_of_type(result, "STEP_OUTPUT")) == 1
            assert len(events_of_type(result, "HANDLED_OUTPUT")) == 1
            assert len(events_of_type(result, "STEP_SUCCESS")) == 1

            events = instance.all_logs(result.run_id)
            start_markers = {}
            end_markers = {}
            for event in events:
                dagster_event = event.dagster_event
                if dagster_event and dagster_event.is_engine_event:
                    if dagster_event.engine_event_data.marker_start:
                        key = "{step}.{marker}".format(
                            step=event.step_key, marker=dagster_event.engine_event_data.marker_start
                        )
                        start_markers[key] = event.timestamp
                    if dagster_event.engine_event_data.marker_end:
                        key = "{step}.{marker}".format(
                            step=event.step_key, marker=dagster_event.engine_event_data.marker_end
                        )
                        end_markers[key] = event.timestamp

            seen = set()
            assert set(start_markers.keys()) == set(end_markers.keys())
            for key in end_markers:
                assert end_markers[key] - start_markers[key] > 0
                seen.add(key)


def test_execute_eagerly_serial_on_celery():
    with execute_eagerly_on_celery("test_serial_pipeline") as result:
        assert result.result_for_solid("simple").output_value() == 1
        assert result.result_for_solid("add_one").output_value() == 2
        assert len(result.step_event_list) == 10
        assert len(events_of_type(result, "STEP_START")) == 2
        assert len(events_of_type(result, "STEP_INPUT")) == 1
        assert len(events_of_type(result, "STEP_OUTPUT")) == 2
        assert len(events_of_type(result, "HANDLED_OUTPUT")) == 2
        assert len(events_of_type(result, "LOADED_INPUT")) == 1
        assert len(events_of_type(result, "STEP_SUCCESS")) == 2


def test_execute_eagerly_diamond_pipeline_on_celery():
    with execute_eagerly_on_celery("test_diamond_pipeline") as result:
        assert result.result_for_solid("emit_values").output_values == {
            "value_one": 1,
            "value_two": 2,
        }
        assert result.result_for_solid("add_one").output_value() == 2
        assert result.result_for_solid("renamed").output_value() == 3
        assert result.result_for_solid("subtract").output_value() == -1


def test_execute_eagerly_diamond_pipeline_subset_on_celery():
    with execute_eagerly_on_celery("test_diamond_pipeline", subset=["emit_values"]) as result:
        assert result.result_for_solid("emit_values").output_values == {
            "value_one": 1,
            "value_two": 2,
        }
        assert len(result.solid_result_list) == 1


def test_execute_eagerly_parallel_pipeline_on_celery():
    with execute_eagerly_on_celery("test_parallel_pipeline") as result:
        assert len(result.solid_result_list) == 11


def test_execute_eagerly_composite_pipeline_on_celery():
    with execute_eagerly_on_celery("composite_pipeline") as result:
        assert result.success
        assert isinstance(result, PipelineExecutionResult)
        assert len(result.solid_result_list) == 1
        composite_solid_result = result.solid_result_list[0]
        assert len(composite_solid_result.solid_result_list) == 2
        for r in composite_solid_result.solid_result_list:
            assert isinstance(r, CompositeSolidExecutionResult)
        composite_solid_results = composite_solid_result.solid_result_list
        for i in range(COMPOSITE_DEPTH):
            next_level = []
            assert len(composite_solid_results) == pow(2, i + 1)
            for res in composite_solid_results:
                assert isinstance(res, CompositeSolidExecutionResult)
                for r in res.solid_result_list:
                    next_level.append(r)
            composite_solid_results = next_level
        assert len(composite_solid_results) == pow(2, COMPOSITE_DEPTH + 1)
        assert all(
            (isinstance(r, SolidExecutionResult) and r.success for r in composite_solid_results)
        )


def test_execute_eagerly_optional_outputs_pipeline_on_celery():
    with execute_eagerly_on_celery("test_optional_outputs") as result:
        assert len(result.solid_result_list) == 4
        assert sum([int(x.skipped) for x in result.solid_result_list]) == 2
        assert sum([int(x.success) for x in result.solid_result_list]) == 2


def test_execute_eagerly_resources_limit_pipeline_on_celery():
    with execute_eagerly_on_celery("test_resources_limit") as result:
        assert result.result_for_solid("resource_req_solid").success
        assert result.success


def test_execute_eagerly_fails_pipeline_on_celery():
    with execute_eagerly_on_celery("test_fails") as result:
        assert len(result.solid_result_list) == 2
        assert not result.result_for_solid("fails").success
        assert (
            result.result_for_solid("fails").failure_data.error.message == "Exception: argjhgjh\n"
        )
        assert result.result_for_solid("should_never_execute").skipped


def test_execute_eagerly_retries_pipeline_on_celery():
    with execute_eagerly_on_celery("test_retries") as result:
        assert len(events_of_type(result, "STEP_START")) == 1
        assert len(events_of_type(result, "STEP_UP_FOR_RETRY")) == 1
        assert len(events_of_type(result, "STEP_RESTARTED")) == 1
        assert len(events_of_type(result, "STEP_FAILURE")) == 1


def test_engine_error():
    with seven.mock.patch(
        "dagster.core.execution.context.system.SystemExecutionContextData.raise_on_error",
        return_value=True,
    ):
        with pytest.raises(DagsterSubprocessError):
            with tempfile.TemporaryDirectory() as tempdir:
                with instance_for_test_tempdir(tempdir) as instance:
                    storage = os.path.join(tempdir, "flakey_storage")
                    execute_pipeline(
                        ReconstructablePipeline.for_file(REPO_FILE, "engine_error"),
                        run_config={
                            "intermediate_storage": {
                                "filesystem": {"config": {"base_dir": storage}}
                            },
                            "execution": {
                                "celery": {"config": {"config_source": {"task_always_eager": True}}}
                            },
                            "solids": {"destroy": {"config": storage}},
                        },
                        instance=instance,
                    )
