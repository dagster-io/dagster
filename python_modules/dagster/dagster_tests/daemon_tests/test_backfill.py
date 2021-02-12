import os
import sys
import time
from collections import defaultdict
from contextlib import contextmanager

import pendulum
import pytest
from dagster import pipeline, repository, solid
from dagster.core.definitions import PartitionSetDefinition
from dagster.core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster.core.host_representation import ManagedGrpcPythonEnvRepositoryLocationOrigin
from dagster.core.storage.pipeline_run import PipelineRunStatus, PipelineRunsFilter
from dagster.core.storage.tags import BACKFILL_ID_TAG, PARTITION_NAME_TAG
from dagster.core.test_utils import instance_for_test
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.daemon import get_default_daemon_logger
from dagster.daemon.backfill import execute_backfill_iteration
from dagster.seven import get_system_temp_directory
from dagster.utils import touch_file


def _failure_flag_file():
    return os.path.join(get_system_temp_directory(), "conditionally_fail")


def _step_events(instance, run):
    events_by_step = defaultdict(set)
    logs = instance.all_logs(run.run_id)
    for record in logs:
        if not record.is_dagster_event or not record.step_key:
            continue
        events_by_step[record.step_key] = record.dagster_event.event_type_value
    return events_by_step


@solid
def always_succeed(_):
    return 1


@solid
def conditionally_fail(_, _input):
    if os.path.isfile(_failure_flag_file()):
        raise Exception("blah")

    return 1


@solid
def after_failure(_, _input):
    return 1


@pipeline
def the_pipeline():
    always_succeed()


@pipeline
def conditional_failure_pipeline():
    after_failure(conditionally_fail(always_succeed()))


@pipeline
def partial_pipeline():
    always_succeed.alias("step_one")()
    always_succeed.alias("step_two")()
    always_succeed.alias("step_three")()


simple_partition_set = PartitionSetDefinition(
    name="simple_partition_set",
    pipeline_name="the_pipeline",
    partition_fn=lambda: ["one", "two", "three"],
    run_config_fn_for_partition=lambda _partition: {"intermediate_storage": {"filesystem": {}}},
)

conditionally_fail_partition_set = PartitionSetDefinition(
    name="conditionally_fail_partition_set",
    pipeline_name="conditional_failure_pipeline",
    partition_fn=lambda: ["one", "two", "three"],
    run_config_fn_for_partition=lambda _partition: {"intermediate_storage": {"filesystem": {}}},
)

partial_partition_set = PartitionSetDefinition(
    name="partial_partition_set",
    pipeline_name="partial_pipeline",
    partition_fn=lambda: ["one", "two", "three"],
    run_config_fn_for_partition=lambda _partition: {"intermediate_storage": {"filesystem": {}}},
)


@repository
def the_repo():
    return [
        the_pipeline,
        conditional_failure_pipeline,
        partial_pipeline,
        simple_partition_set,
        conditionally_fail_partition_set,
        partial_partition_set,
    ]


@contextmanager
def default_repo():
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable,
        python_file=__file__,
        working_directory=os.getcwd(),
    )

    with ManagedGrpcPythonEnvRepositoryLocationOrigin(
        loadable_target_origin=loadable_target_origin,
        location_name="test_location",
    ).create_handle() as handle:
        yield handle.create_location().get_repository("the_repo")


def repos():
    return [default_repo]


@contextmanager
def instance_for_context(external_repo_context, overrides=None):
    with instance_for_test(overrides) as instance:
        with external_repo_context() as external_repo:
            yield (instance, external_repo)


def step_did_not_run(instance, run, step_name):
    step_events = _step_events(instance, run)[step_name]
    return len(step_events) == 0


def step_succeeded(instance, run, step_name):
    step_events = _step_events(instance, run)[step_name]
    return "STEP_SUCCESS" in step_events


def step_failed(instance, run, step_name):
    step_events = _step_events(instance, run)[step_name]
    return "STEP_FAILURE" in step_events


def wait_for_all_runs_to_start(instance, timeout=10):
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            raise Exception("Timed out waiting for runs to start")
        time.sleep(0.5)

        pending_states = [
            PipelineRunStatus.NOT_STARTED,
            PipelineRunStatus.STARTING,
            PipelineRunStatus.STARTED,
        ]
        pending_runs = [run for run in instance.get_runs() if run.status in pending_states]

        if len(pending_runs) == 0:
            break


@pytest.mark.parametrize("external_repo_context", repos())
def test_simple_backfill(external_repo_context):
    with instance_for_context(external_repo_context) as (instance, external_repo):
        external_partition_set = external_repo.get_external_partition_set("simple_partition_set")
        instance.add_backfill(
            PartitionBackfill(
                backfill_id="simple",
                partition_set_origin=external_partition_set.get_external_origin(),
                status=BulkActionStatus.REQUESTED,
                partition_names=["one", "two", "three"],
                from_failure=False,
                reexecution_steps=None,
                tags=None,
                backfill_timestamp=pendulum.now().timestamp(),
            )
        )
        assert instance.get_runs_count() == 0

        list(execute_backfill_iteration(instance, get_default_daemon_logger("BackfillDaemon")))

        assert instance.get_runs_count() == 3
        runs = instance.get_runs()
        three, two, one = runs
        assert one.tags[BACKFILL_ID_TAG] == "simple"
        assert one.tags[PARTITION_NAME_TAG] == "one"
        assert two.tags[BACKFILL_ID_TAG] == "simple"
        assert two.tags[PARTITION_NAME_TAG] == "two"
        assert three.tags[BACKFILL_ID_TAG] == "simple"
        assert three.tags[PARTITION_NAME_TAG] == "three"


@pytest.mark.parametrize("external_repo_context", repos())
def test_failure_backfill(external_repo_context):
    output_file = _failure_flag_file()
    with instance_for_context(external_repo_context) as (instance, external_repo):
        external_partition_set = external_repo.get_external_partition_set(
            "conditionally_fail_partition_set"
        )
        instance.add_backfill(
            PartitionBackfill(
                backfill_id="shouldfail",
                partition_set_origin=external_partition_set.get_external_origin(),
                status=BulkActionStatus.REQUESTED,
                partition_names=["one", "two", "three"],
                from_failure=False,
                reexecution_steps=None,
                tags=None,
                backfill_timestamp=pendulum.now().timestamp(),
            )
        )
        assert instance.get_runs_count() == 0

        try:
            touch_file(output_file)
            list(execute_backfill_iteration(instance, get_default_daemon_logger("BackfillDaemon")))
            wait_for_all_runs_to_start(instance)
        finally:
            os.remove(output_file)

        assert instance.get_runs_count() == 3
        runs = instance.get_runs()
        three, two, one = runs
        assert one.tags[BACKFILL_ID_TAG] == "shouldfail"
        assert one.tags[PARTITION_NAME_TAG] == "one"
        assert one.status == PipelineRunStatus.FAILURE
        assert step_succeeded(instance, one, "always_succeed")
        assert step_failed(instance, one, "conditionally_fail")
        assert step_did_not_run(instance, one, "after_failure")

        assert two.tags[BACKFILL_ID_TAG] == "shouldfail"
        assert two.tags[PARTITION_NAME_TAG] == "two"
        assert two.status == PipelineRunStatus.FAILURE
        assert step_succeeded(instance, two, "always_succeed")
        assert step_failed(instance, two, "conditionally_fail")
        assert step_did_not_run(instance, two, "after_failure")

        assert three.tags[BACKFILL_ID_TAG] == "shouldfail"
        assert three.tags[PARTITION_NAME_TAG] == "three"
        assert three.status == PipelineRunStatus.FAILURE
        assert step_succeeded(instance, three, "always_succeed")
        assert step_failed(instance, three, "conditionally_fail")
        assert step_did_not_run(instance, three, "after_failure")

        instance.add_backfill(
            PartitionBackfill(
                backfill_id="fromfailure",
                partition_set_origin=external_partition_set.get_external_origin(),
                status=BulkActionStatus.REQUESTED,
                partition_names=["one", "two", "three"],
                from_failure=True,
                reexecution_steps=None,
                tags=None,
                backfill_timestamp=pendulum.now().timestamp(),
            )
        )

        assert not os.path.isfile(_failure_flag_file())
        list(execute_backfill_iteration(instance, get_default_daemon_logger("BackfillDaemon")))
        wait_for_all_runs_to_start(instance)

        assert instance.get_runs_count() == 6
        from_failure_filter = PipelineRunsFilter(tags={BACKFILL_ID_TAG: "fromfailure"})
        assert instance.get_runs_count(filters=from_failure_filter) == 3

        runs = instance.get_runs(filters=from_failure_filter)
        three, two, one = runs

        assert one.tags[BACKFILL_ID_TAG] == "fromfailure"
        assert one.tags[PARTITION_NAME_TAG] == "one"
        assert one.status == PipelineRunStatus.SUCCESS
        assert step_did_not_run(instance, one, "always_succeed")
        assert step_succeeded(instance, one, "conditionally_fail")
        assert step_succeeded(instance, one, "after_failure")

        assert two.tags[BACKFILL_ID_TAG] == "fromfailure"
        assert two.tags[PARTITION_NAME_TAG] == "two"
        assert two.status == PipelineRunStatus.SUCCESS
        assert step_did_not_run(instance, one, "always_succeed")
        assert step_succeeded(instance, one, "conditionally_fail")
        assert step_succeeded(instance, one, "after_failure")

        assert three.tags[BACKFILL_ID_TAG] == "fromfailure"
        assert three.tags[PARTITION_NAME_TAG] == "three"
        assert three.status == PipelineRunStatus.SUCCESS
        assert step_did_not_run(instance, one, "always_succeed")
        assert step_succeeded(instance, one, "conditionally_fail")
        assert step_succeeded(instance, one, "after_failure")


@pytest.mark.parametrize("external_repo_context", repos())
def test_partial_backfill(external_repo_context):
    with instance_for_context(external_repo_context) as (instance, external_repo):
        external_partition_set = external_repo.get_external_partition_set("partial_partition_set")

        # create full runs, where every step is executed
        instance.add_backfill(
            PartitionBackfill(
                backfill_id="full",
                partition_set_origin=external_partition_set.get_external_origin(),
                status=BulkActionStatus.REQUESTED,
                partition_names=["one", "two", "three"],
                from_failure=False,
                reexecution_steps=None,
                tags=None,
                backfill_timestamp=pendulum.now().timestamp(),
            )
        )
        assert instance.get_runs_count() == 0
        list(execute_backfill_iteration(instance, get_default_daemon_logger("BackfillDaemon")))
        wait_for_all_runs_to_start(instance)

        assert instance.get_runs_count() == 3
        runs = instance.get_runs()
        three, two, one = runs

        assert one.tags[BACKFILL_ID_TAG] == "full"
        assert one.tags[PARTITION_NAME_TAG] == "one"
        assert one.status == PipelineRunStatus.SUCCESS
        assert step_succeeded(instance, one, "step_one")
        assert step_succeeded(instance, one, "step_two")
        assert step_succeeded(instance, one, "step_three")

        assert two.tags[BACKFILL_ID_TAG] == "full"
        assert two.tags[PARTITION_NAME_TAG] == "two"
        assert two.status == PipelineRunStatus.SUCCESS
        assert step_succeeded(instance, two, "step_one")
        assert step_succeeded(instance, two, "step_two")
        assert step_succeeded(instance, two, "step_three")

        assert three.tags[BACKFILL_ID_TAG] == "full"
        assert three.tags[PARTITION_NAME_TAG] == "three"
        assert three.status == PipelineRunStatus.SUCCESS
        assert step_succeeded(instance, three, "step_one")
        assert step_succeeded(instance, three, "step_two")
        assert step_succeeded(instance, three, "step_three")

        # create partial runs
        instance.add_backfill(
            PartitionBackfill(
                backfill_id="partial",
                partition_set_origin=external_partition_set.get_external_origin(),
                status=BulkActionStatus.REQUESTED,
                partition_names=["one", "two", "three"],
                from_failure=False,
                reexecution_steps=["step_one"],
                tags=None,
                backfill_timestamp=pendulum.now().timestamp(),
            )
        )
        list(execute_backfill_iteration(instance, get_default_daemon_logger("BackfillDaemon")))
        wait_for_all_runs_to_start(instance)

        assert instance.get_runs_count() == 6
        partial_filter = PipelineRunsFilter(tags={BACKFILL_ID_TAG: "partial"})
        assert instance.get_runs_count(filters=partial_filter) == 3
        runs = instance.get_runs(filters=partial_filter)
        three, two, one = runs

        assert one.status == PipelineRunStatus.SUCCESS
        assert step_succeeded(instance, one, "step_one")
        assert step_did_not_run(instance, one, "step_two")
        assert step_did_not_run(instance, one, "step_three")

        assert two.status == PipelineRunStatus.SUCCESS
        assert step_succeeded(instance, two, "step_one")
        assert step_did_not_run(instance, two, "step_two")
        assert step_did_not_run(instance, two, "step_three")

        assert three.status == PipelineRunStatus.SUCCESS
        assert step_succeeded(instance, three, "step_one")
        assert step_did_not_run(instance, three, "step_two")
        assert step_did_not_run(instance, three, "step_three")
