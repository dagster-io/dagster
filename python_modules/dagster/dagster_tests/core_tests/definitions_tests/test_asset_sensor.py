import logging
import time
from contextlib import contextmanager
from typing import List, Optional, cast

from dagster import (
    AssetKey,
    AssetMaterialization,
    DagsterEvent,
    DagsterInvariantViolationError,
    RunRequest,
    any_asset_sensor,
    build_sensor_context,
    check,
    job,
    multi_asset_sensor,
    op,
)
from dagster.check import CheckError
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.events.log import EventLogEntry
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.context_creation_pipeline import scoped_pipeline_context
from dagster.core.execution.plan.step import ExecutionStep
from dagster.core.test_utils import instance_for_test
from dagster.seven import json
from pytest import raises


@op
def foo_op():
    pass


@job
def foo_job():
    foo_op()


@multi_asset_sensor(asset_keys=[AssetKey("foo"), AssetKey("bar")], job=foo_job)
def foo_bar_multi_asset_sensor(_context, _event):
    return RunRequest("unique")


@any_asset_sensor(asset_keys=[AssetKey("foo"), AssetKey("bar")], job=foo_job)
def foo_bar_any_asset_sensor(_context, _event):
    return RunRequest("unique")


@multi_asset_sensor(asset_keys=[AssetKey("foo"), AssetKey("bar")], job=foo_job)
def foo_bar_multi_asset_sensor_yields(_context, _event):
    yield RunRequest("unique_0")
    yield RunRequest("unique_1")


@any_asset_sensor(asset_keys=[AssetKey("foo"), AssetKey("bar")], job=foo_job)
def foo_bar_any_asset_sensor_yields(_context, _event):
    yield RunRequest("unique_0")
    yield RunRequest("unique_1")


@multi_asset_sensor(asset_keys=[AssetKey("foo"), AssetKey("bar")], job=foo_job)
def foo_bar_multi_asset_sensor_errors(_context, _event):
    return "bad"


@any_asset_sensor(asset_keys=[AssetKey("foo"), AssetKey("bar")], job=foo_job)
def foo_bar_any_asset_sensor_errors(_context, _event):
    return "bad"


execution_plan = create_execution_plan(foo_job)


@contextmanager
def sensor_context_for_test(
    updated_asset_keys: List[AssetKey] = None, cursor: List[Optional[str]] = None
):
    updated_asset_keys = check.opt_list_param(
        updated_asset_keys, "updated_asset_keys", of_type=AssetKey
    )
    cursor = check.opt_list_param(cursor, "cursor", of_type=(str, type(None)))

    with instance_for_test() as instance:
        pipeline_run = instance.create_run_for_pipeline(foo_job)

        with scoped_pipeline_context(
            execution_plan, InMemoryPipeline(foo_job), {}, pipeline_run, instance
        ) as pipeline_context:
            step_context = pipeline_context.for_step(
                cast(ExecutionStep, execution_plan.get_step_by_key("foo_op"))
            )
            for updated_asset_key in updated_asset_keys:
                asset_event = DagsterEvent.asset_materialization(
                    step_context=step_context,
                    materialization=AssetMaterialization(asset_key=updated_asset_key),
                )
                event_record = EventLogEntry(
                    message="",
                    user_message="",
                    level=logging.INFO,
                    pipeline_name=pipeline_run.pipeline_name,
                    run_id=pipeline_run.run_id,
                    error_info=None,
                    timestamp=time.time(),
                    step_key=step_context.step.key,
                    dagster_event=asset_event,
                )
                instance.handle_new_event(event_record)

        with build_sensor_context(
            instance=instance,
            cursor=json.dumps(cursor),
        ) as sensor_context:
            yield sensor_context


def test_empty_multi_asset_sensor():
    with raises(CheckError):

        @multi_asset_sensor(asset_keys=[], job=foo_job)
        def _empty_multi_asset_sensor(_context, _event):
            return None


def test_empty_any_asset_sensor():
    with raises(CheckError):

        @any_asset_sensor(asset_keys=[], job=foo_job)
        def _empty_any_asset_sensor(_context, _event):
            return None


def test_multi_asset_sensor_no_match():
    with instance_for_test() as instance:

        with build_sensor_context(
            instance=instance,
            cursor=json.dumps([None, None]),
        ) as sensor_context:
            res = foo_bar_multi_asset_sensor.evaluate_tick(sensor_context)
            assert res.run_requests == []
            assert res.skip_message == None
            assert res.cursor == json.dumps([None, None])


def test_any_asset_sensor_no_match():
    with instance_for_test() as instance:

        with build_sensor_context(
            instance=instance,
            cursor=json.dumps([None, None]),
        ) as sensor_context:
            res = foo_bar_any_asset_sensor.evaluate_tick(sensor_context)
            assert res.run_requests == []
            assert res.skip_message == None
            assert res.cursor == json.dumps([None, None])


def test_multi_asset_sensor_partial_match():
    with sensor_context_for_test(
        updated_asset_keys=[AssetKey("foo")], cursor=[None, None]
    ) as sensor_context:
        res = foo_bar_multi_asset_sensor.evaluate_tick(sensor_context)
        assert res.run_requests == []
        assert res.skip_message == None
        assert res.cursor == json.dumps([None, None])


def test_multi_asset_sensor_match():
    with sensor_context_for_test(
        updated_asset_keys=[AssetKey("foo"), AssetKey("bar")], cursor=[None, None]
    ) as sensor_context:
        res = foo_bar_multi_asset_sensor.evaluate_tick(sensor_context)
        assert isinstance(res.run_requests, list)
        assert len(res.run_requests) == 1
        assert res.run_requests[0] == RunRequest(run_key="unique", run_config={}, tags={})
        assert res.skip_message == None
        assert res.cursor == json.dumps([2, 4])


def test_any_asset_sensor_partial_match():
    with sensor_context_for_test(
        updated_asset_keys=[AssetKey("foo")], cursor=[None, None]
    ) as sensor_context:
        res = foo_bar_any_asset_sensor.evaluate_tick(sensor_context)
        assert isinstance(res.run_requests, list)
        assert len(res.run_requests) == 1
        assert res.run_requests[0] == RunRequest(run_key="unique", run_config={}, tags={})
        assert res.skip_message == None
        assert res.cursor == json.dumps([2, None])


def test_any_asset_sensor_match():
    with sensor_context_for_test(
        updated_asset_keys=[AssetKey("foo"), AssetKey("bar")], cursor=[None, None]
    ) as sensor_context:
        res = foo_bar_any_asset_sensor.evaluate_tick(sensor_context)
        assert isinstance(res.run_requests, list)
        assert len(res.run_requests) == 1
        assert res.run_requests[0] == RunRequest(run_key="unique", run_config={}, tags={})
        assert res.skip_message == None
        assert res.cursor == json.dumps([2, 4])


def test_multi_asset_sensor_yields_match():
    with sensor_context_for_test(
        updated_asset_keys=[AssetKey("foo"), AssetKey("bar")], cursor=[None, None]
    ) as sensor_context:
        res = foo_bar_multi_asset_sensor_yields.evaluate_tick(sensor_context)
        assert isinstance(res.run_requests, list)
        assert len(res.run_requests) == 2
        assert res.run_requests[0] == RunRequest(run_key="unique_0", run_config={}, tags={})
        assert res.run_requests[1] == RunRequest(run_key="unique_1", run_config={}, tags={})
        assert res.skip_message == None
        assert res.cursor == json.dumps([2, 4])


def test_any_asset_sensor_yields_match():
    with sensor_context_for_test(
        updated_asset_keys=[AssetKey("foo"), AssetKey("bar")], cursor=[None, None]
    ) as sensor_context:
        res = foo_bar_any_asset_sensor_yields.evaluate_tick(sensor_context)
        assert isinstance(res.run_requests, list)
        assert len(res.run_requests) == 2
        assert res.run_requests[0] == RunRequest(run_key="unique_0", run_config={}, tags={})
        assert res.run_requests[1] == RunRequest(run_key="unique_1", run_config={}, tags={})
        assert res.skip_message == None
        assert res.cursor == json.dumps([2, 4])


def test_multi_asset_sensor_errors_match():
    with sensor_context_for_test(
        updated_asset_keys=[AssetKey("foo"), AssetKey("bar")], cursor=[None, None]
    ) as sensor_context:
        with raises(DagsterInvariantViolationError, match="Sensor unexpectedly returned output"):
            foo_bar_multi_asset_sensor_errors.evaluate_tick(sensor_context)


def test_any_asset_sensor_errors_match():
    with sensor_context_for_test(
        updated_asset_keys=[AssetKey("foo"), AssetKey("bar")], cursor=[None, None]
    ) as sensor_context:
        with raises(DagsterInvariantViolationError, match="Sensor unexpectedly returned output"):
            foo_bar_any_asset_sensor_errors.evaluate_tick(sensor_context)
