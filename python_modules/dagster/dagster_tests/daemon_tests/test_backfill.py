import os
import random
import string
import sys
import time

import pendulum
import pytest

from dagster import (
    Any,
    AssetKey,
    AssetsDefinition,
    Field,
    In,
    Nothing,
    Out,
    asset,
    daily_partitioned_config,
    define_asset_job,
    fs_io_manager,
    graph,
    op,
    repository,
)
from dagster._core.definitions import Partition, PartitionSetDefinition, StaticPartitionsDefinition
from dagster._core.execution.api import execute_pipeline
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.host_representation import (
    ExternalRepositoryOrigin,
    InProcessRepositoryLocationOrigin,
)
from dagster._core.storage.pipeline_run import PipelineRunStatus, RunsFilter
from dagster._core.storage.tags import BACKFILL_ID_TAG, PARTITION_NAME_TAG, PARTITION_SET_TAG
from dagster._core.test_utils import step_did_not_run, step_failed, step_succeeded
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._daemon import get_default_daemon_logger
from dagster._daemon.backfill import execute_backfill_iteration
from dagster._legacy import ModeDefinition, pipeline, solid
from dagster._seven import IS_WINDOWS, get_system_temp_directory
from dagster._utils import touch_file
from dagster._utils.error import SerializableErrorInfo

default_mode_def = ModeDefinition(resource_defs={"io_manager": fs_io_manager})


def _failure_flag_file():
    return os.path.join(get_system_temp_directory(), "conditionally_fail")


@solid
def always_succeed(_):
    return 1


@graph()
def comp_always_succeed():
    always_succeed()


@daily_partitioned_config(start_date="2021-05-05")
def my_config(_start, _end):
    return {}


always_succeed_job = comp_always_succeed.to_job(config=my_config)


@solid
def fail_solid(_):
    raise Exception("blah")


@solid
def conditionally_fail(_, _input):
    if os.path.isfile(_failure_flag_file()):
        raise Exception("blah")

    return 1


@solid
def after_failure(_, _input):
    return 1


@pipeline(mode_defs=[default_mode_def])
def the_pipeline():
    always_succeed()


@pipeline(mode_defs=[default_mode_def])
def conditional_failure_pipeline():
    after_failure(conditionally_fail(always_succeed()))


@pipeline(mode_defs=[default_mode_def])
def partial_pipeline():
    always_succeed.alias("step_one")()
    always_succeed.alias("step_two")()
    always_succeed.alias("step_three")()


@pipeline(mode_defs=[default_mode_def])
def parallel_failure_pipeline():
    fail_solid.alias("fail_one")()
    fail_solid.alias("fail_two")()
    fail_solid.alias("fail_three")()
    always_succeed.alias("success_four")()


@solid(config_schema=Field(Any))
def config_solid(_):
    return 1


@pipeline(mode_defs=[default_mode_def])
def config_pipeline():
    config_solid()


# Type-ignores due to mypy bug with inference and lambdas

simple_partition_set: PartitionSetDefinition = PartitionSetDefinition(
    name="simple_partition_set",
    pipeline_name="the_pipeline",
    partition_fn=lambda: [Partition("one"), Partition("two"), Partition("three")],  # type: ignore
)

conditionally_fail_partition_set: PartitionSetDefinition = PartitionSetDefinition(
    name="conditionally_fail_partition_set",
    pipeline_name="conditional_failure_pipeline",
    partition_fn=lambda: [Partition("one"), Partition("two"), Partition("three")],  # type: ignore
)

partial_partition_set: PartitionSetDefinition = PartitionSetDefinition(
    name="partial_partition_set",
    pipeline_name="partial_pipeline",
    partition_fn=lambda: [Partition("one"), Partition("two"), Partition("three")],  # type: ignore
)

parallel_failure_partition_set: PartitionSetDefinition = PartitionSetDefinition(
    name="parallel_failure_partition_set",
    pipeline_name="parallel_failure_pipeline",
    partition_fn=lambda: [Partition("one"), Partition("two"), Partition("three")],  # type: ignore
)


def _large_partition_config(_):
    REQUEST_CONFIG_COUNT = 50000

    def _random_string(length):
        return "".join(random.choice(string.ascii_lowercase) for x in range(length))

    return {
        "solids": {
            "config_solid": {
                "config": {
                    "foo": {
                        _random_string(10): _random_string(20) for i in range(REQUEST_CONFIG_COUNT)
                    }
                }
            }
        }
    }


large_partition_set = PartitionSetDefinition(
    name="large_partition_set",
    pipeline_name="config_pipeline",
    partition_fn=lambda: [Partition("one"), Partition("two"), Partition("three")],  # type: ignore
    run_config_fn_for_partition=_large_partition_config,
)


def _unloadable_partition_set_origin():
    working_directory = os.path.dirname(__file__)
    return ExternalRepositoryOrigin(
        InProcessRepositoryLocationOrigin(
            LoadableTargetOrigin(
                executable_path=sys.executable,
                python_file=__file__,
                working_directory=working_directory,
            )
        ),
        "fake_repository",
    ).get_partition_set_origin("doesnt_exist")


static_partitions = StaticPartitionsDefinition(["x", "y", "z"])


@asset(partitions_def=static_partitions)
def foo():
    return 1


@asset(partitions_def=static_partitions)
def bar(a1):
    return a1


@op(ins={"in1": In(Nothing), "in2": In(Nothing)}, out={"out1": Out(), "out2": Out()})
def reusable():
    return 1, 2


ab1 = AssetsDefinition(
    node_def=reusable,
    keys_by_input_name={
        "in1": AssetKey("foo"),
        "in2": AssetKey("bar"),
    },
    keys_by_output_name={"out1": AssetKey("a1"), "out2": AssetKey("b1")},
    partitions_def=static_partitions,
    can_subset=True,
    asset_deps={AssetKey("a1"): {AssetKey("foo")}, AssetKey("b1"): {AssetKey("bar")}},
)

ab2 = AssetsDefinition(
    node_def=reusable,
    keys_by_input_name={
        "in1": AssetKey("foo"),
        "in2": AssetKey("bar"),
    },
    keys_by_output_name={"out1": AssetKey("a2"), "out2": AssetKey("b2")},
    partitions_def=static_partitions,
    can_subset=True,
    asset_deps={AssetKey("a2"): {AssetKey("foo")}, AssetKey("b2"): {AssetKey("bar")}},
)


@repository
def the_repo():
    return [
        the_pipeline,
        conditional_failure_pipeline,
        partial_pipeline,
        config_pipeline,
        simple_partition_set,
        conditionally_fail_partition_set,
        partial_partition_set,
        large_partition_set,
        always_succeed_job,
        parallel_failure_partition_set,
        parallel_failure_pipeline,
        # the lineage graph defined with these assets is such that: foo -> a1 -> bar -> b1
        # this requires ab1 to be split into two separate asset definitions using the automatic
        # subsetting capabilities. ab2 is defines similarly, so in total 4 copies of the "reusable"
        # op will exist in the full plan, whereas onle a single copy will be needed for a subset
        # plan which only materializes foo -> a1 -> bar
        foo,
        bar,
        ab1,
        ab2,
        define_asset_job("twisted_asset_mess", selection="*", partitions_def=static_partitions),
    ]


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


def wait_for_all_runs_to_finish(instance, timeout=10):
    start_time = time.time()
    FINISHED_STATES = [
        PipelineRunStatus.SUCCESS,
        PipelineRunStatus.FAILURE,
        PipelineRunStatus.CANCELED,
    ]
    while True:
        if time.time() - start_time > timeout:
            raise Exception("Timed out waiting for runs to start")
        time.sleep(0.5)

        not_finished_runs = [
            run for run in instance.get_runs() if run.status not in FINISHED_STATES
        ]

        if len(not_finished_runs) == 0:
            break


def test_simple_backfill(instance, workspace, external_repo):
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

    list(
        execute_backfill_iteration(instance, workspace, get_default_daemon_logger("BackfillDaemon"))
    )

    assert instance.get_runs_count() == 3
    runs = instance.get_runs()
    three, two, one = runs
    assert one.tags[BACKFILL_ID_TAG] == "simple"
    assert one.tags[PARTITION_NAME_TAG] == "one"
    assert two.tags[BACKFILL_ID_TAG] == "simple"
    assert two.tags[PARTITION_NAME_TAG] == "two"
    assert three.tags[BACKFILL_ID_TAG] == "simple"
    assert three.tags[PARTITION_NAME_TAG] == "three"


def test_canceled_backfill(instance, workspace, external_repo):
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

    iterator = execute_backfill_iteration(
        instance, workspace, get_default_daemon_logger("BackfillDaemon")
    )
    next(iterator)
    assert instance.get_runs_count() == 1
    backfill = instance.get_backfills()[0]
    assert backfill.status == BulkActionStatus.REQUESTED
    instance.update_backfill(backfill.with_status(BulkActionStatus.CANCELED))
    list(iterator)
    backfill = instance.get_backfill(backfill.backfill_id)
    assert backfill.status == BulkActionStatus.CANCELED
    assert instance.get_runs_count() == 1


def test_failure_backfill(instance, workspace, external_repo):
    output_file = _failure_flag_file()
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
        list(
            execute_backfill_iteration(
                instance, workspace, get_default_daemon_logger("BackfillDaemon")
            )
        )
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
    list(
        execute_backfill_iteration(instance, workspace, get_default_daemon_logger("BackfillDaemon"))
    )
    wait_for_all_runs_to_start(instance)

    assert instance.get_runs_count() == 6
    from_failure_filter = RunsFilter(tags={BACKFILL_ID_TAG: "fromfailure"})
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


@pytest.mark.skipif(IS_WINDOWS, reason="flaky in windows")
def test_partial_backfill(instance, workspace, external_repo):
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
    list(
        execute_backfill_iteration(instance, workspace, get_default_daemon_logger("BackfillDaemon"))
    )
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

    # delete one of the runs, the partial reexecution should still succeed because the steps
    # can be executed independently, require no input/output config
    instance.delete_run(one.run_id)
    assert instance.get_runs_count() == 2

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
    list(
        execute_backfill_iteration(instance, workspace, get_default_daemon_logger("BackfillDaemon"))
    )
    wait_for_all_runs_to_start(instance)

    assert instance.get_runs_count() == 5
    partial_filter = RunsFilter(tags={BACKFILL_ID_TAG: "partial"})
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


def test_large_backfill(instance, workspace, external_repo):
    external_partition_set = external_repo.get_external_partition_set("large_partition_set")
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

    list(
        execute_backfill_iteration(instance, workspace, get_default_daemon_logger("BackfillDaemon"))
    )

    assert instance.get_runs_count() == 3


def test_unloadable_backfill(instance, workspace):
    unloadable_origin = _unloadable_partition_set_origin()
    instance.add_backfill(
        PartitionBackfill(
            backfill_id="simple",
            partition_set_origin=unloadable_origin,
            status=BulkActionStatus.REQUESTED,
            partition_names=["one", "two", "three"],
            from_failure=False,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=pendulum.now().timestamp(),
        )
    )
    assert instance.get_runs_count() == 0

    list(
        execute_backfill_iteration(instance, workspace, get_default_daemon_logger("BackfillDaemon"))
    )

    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill("simple")
    assert backfill.status == BulkActionStatus.FAILED
    assert isinstance(backfill.error, SerializableErrorInfo)


def test_backfill_from_partitioned_job(instance, workspace, external_repo):
    partition_name_list = [
        partition.name for partition in my_config.partitions_def.get_partitions()
    ]
    external_partition_set = external_repo.get_external_partition_set(
        "comp_always_succeed_partition_set"
    )
    instance.add_backfill(
        PartitionBackfill(
            backfill_id="partition_schedule_from_job",
            partition_set_origin=external_partition_set.get_external_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=partition_name_list[:3],
            from_failure=False,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=pendulum.now().timestamp(),
        )
    )
    assert instance.get_runs_count() == 0

    list(
        execute_backfill_iteration(instance, workspace, get_default_daemon_logger("BackfillDaemon"))
    )

    assert instance.get_runs_count() == 3
    runs = reversed(instance.get_runs())
    for idx, run in enumerate(runs):
        assert run.tags[BACKFILL_ID_TAG] == "partition_schedule_from_job"
        assert run.tags[PARTITION_NAME_TAG] == partition_name_list[idx]
        assert run.tags[PARTITION_SET_TAG] == "comp_always_succeed_partition_set"


def test_backfill_with_asset_selection(instance, workspace, external_repo):
    partition_name_list = [partition.name for partition in static_partitions.get_partitions()]
    external_partition_set = external_repo.get_external_partition_set(
        "twisted_asset_mess_partition_set"
    )
    asset_selection = [AssetKey("foo"), AssetKey("a1"), AssetKey("bar")]
    instance.add_backfill(
        PartitionBackfill(
            backfill_id="backfill_with_asset_selection",
            partition_set_origin=external_partition_set.get_external_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=partition_name_list,
            from_failure=False,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=pendulum.now().timestamp(),
            asset_selection=asset_selection,
        )
    )
    assert instance.get_runs_count() == 0

    list(
        execute_backfill_iteration(instance, workspace, get_default_daemon_logger("BackfillDaemon"))
    )
    wait_for_all_runs_to_start(instance, timeout=30)
    assert instance.get_runs_count() == 3
    wait_for_all_runs_to_finish(instance, timeout=30)

    assert instance.get_runs_count() == 3
    runs = reversed(instance.get_runs())
    for idx, run in enumerate(runs):
        assert run.tags[BACKFILL_ID_TAG] == "backfill_with_asset_selection"
        assert run.tags[PARTITION_NAME_TAG] == partition_name_list[idx]
        assert run.tags[PARTITION_SET_TAG] == "twisted_asset_mess_partition_set"
        assert step_succeeded(instance, run, "foo")
        assert step_succeeded(instance, run, "reusable")
        assert step_succeeded(instance, run, "bar")
    # selected
    for asset_key in asset_selection:
        assert len(instance.run_ids_for_asset_key(asset_key)) == 3
    # not selected
    for asset_key in [AssetKey("a2"), AssetKey("b2")]:
        assert len(instance.run_ids_for_asset_key(asset_key)) == 0


def test_backfill_from_failure_for_subselection(instance, workspace, external_repo):
    partition = parallel_failure_partition_set.get_partition("one")
    run_config = parallel_failure_partition_set.run_config_for_partition(partition)
    tags = parallel_failure_partition_set.tags_for_partition(partition)
    external_partition_set = external_repo.get_external_partition_set(
        "parallel_failure_partition_set"
    )

    execute_pipeline(
        parallel_failure_pipeline,
        run_config=run_config,
        tags=tags,
        instance=instance,
        solid_selection=["fail_three", "success_four"],
        raise_on_error=False,
    )

    assert instance.get_runs_count() == 1
    wait_for_all_runs_to_finish(instance)
    run = instance.get_runs()[0]
    assert run.status == PipelineRunStatus.FAILURE

    instance.add_backfill(
        PartitionBackfill(
            backfill_id="fromfailure",
            partition_set_origin=external_partition_set.get_external_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=["one"],
            from_failure=True,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=pendulum.now().timestamp(),
        )
    )

    list(
        execute_backfill_iteration(instance, workspace, get_default_daemon_logger("BackfillDaemon"))
    )
    assert instance.get_runs_count() == 2
    run = instance.get_runs(limit=1)[0]
    assert run.solids_to_execute
    assert run.solid_selection
    assert len(run.solids_to_execute) == 2
    assert len(run.solid_selection) == 2
