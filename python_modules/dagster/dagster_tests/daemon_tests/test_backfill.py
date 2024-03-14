import os
import random
import string
import sys
import time

import dagster._check as check
import mock
import pendulum
import pytest
from dagster import (
    AllPartitionMapping,
    Any,
    AssetIn,
    AssetKey,
    AssetsDefinition,
    DagsterEventType,
    DagsterInstance,
    DailyPartitionsDefinition,
    EventRecordsFilter,
    Field,
    In,
    Nothing,
    Out,
    StaticPartitionMapping,
    asset,
    daily_partitioned_config,
    define_asset_job,
    fs_io_manager,
    graph,
    job,
    op,
    repository,
)
from dagster._core.definitions import (
    StaticPartitionsDefinition,
)
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.partition import PartitionedConfig
from dagster._core.definitions.selector import (
    PartitionRangeSelector,
    PartitionsByAssetSelector,
    PartitionsSelector,
)
from dagster._core.errors import (
    DagsterUserCodeUnreachableError,
)
from dagster._core.execution.asset_backfill import RUN_CHUNK_SIZE
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.remote_representation import (
    ExternalRepository,
    ExternalRepositoryOrigin,
    InProcessCodeLocationOrigin,
)
from dagster._core.storage.dagster_run import IN_PROGRESS_RUN_STATUSES, DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
    BACKFILL_ID_TAG,
    PARTITION_NAME_TAG,
)
from dagster._core.test_utils import (
    environ,
    step_did_not_run,
    step_failed,
    step_succeeded,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._daemon import get_default_daemon_logger
from dagster._daemon.backfill import execute_backfill_iteration
from dagster._seven import IS_WINDOWS, get_system_temp_directory
from dagster._utils import touch_file
from dagster._utils.error import SerializableErrorInfo

default_resource_defs = resource_defs = {"io_manager": fs_io_manager}


def _failure_flag_file():
    return os.path.join(get_system_temp_directory(), "conditionally_fail")


@op
def always_succeed(_):
    return 1


@graph()
def comp_always_succeed():
    always_succeed()


@daily_partitioned_config(start_date="2021-05-05")
def my_config(_start, _end):
    return {}


always_succeed_job = comp_always_succeed.to_job(config=my_config)


@op
def fail_op(_):
    raise Exception("blah")


@op
def conditionally_fail(_, _input):
    if os.path.isfile(_failure_flag_file()):
        raise Exception("blah")

    return 1


@op
def after_failure(_, _input):
    return 1


one_two_three_partitions = StaticPartitionsDefinition(["one", "two", "three"])


@job(partitions_def=one_two_three_partitions)
def the_job():
    always_succeed()


@job(partitions_def=one_two_three_partitions)
def conditional_failure_job():
    after_failure(conditionally_fail(always_succeed()))


@job(partitions_def=one_two_three_partitions)
def partial_job():
    always_succeed.alias("step_one")()
    always_succeed.alias("step_two")()
    always_succeed.alias("step_three")()


@job(partitions_def=one_two_three_partitions)
def parallel_failure_job():
    fail_op.alias("fail_one")()
    fail_op.alias("fail_two")()
    fail_op.alias("fail_three")()
    always_succeed.alias("success_four")()


def _large_partition_config(_):
    REQUEST_CONFIG_COUNT = 50000

    def _random_string(length):
        return "".join(random.choice(string.ascii_lowercase) for x in range(length))

    return {
        "ops": {
            "config_op": {
                "config": {
                    "foo": {
                        _random_string(10): _random_string(20) for i in range(REQUEST_CONFIG_COUNT)
                    }
                }
            }
        }
    }


config_job_config = PartitionedConfig(
    partitions_def=one_two_three_partitions,
    run_config_for_partition_key_fn=_large_partition_config,
)


@op(config_schema=Field(Any))
def config_op(_):
    return 1


@job(partitions_def=one_two_three_partitions, config=config_job_config)
def config_job():
    config_op()


def _unloadable_partition_set_origin():
    working_directory = os.path.dirname(__file__)
    return ExternalRepositoryOrigin(
        InProcessCodeLocationOrigin(
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


@asset(
    config_schema={"myparam": Field(str, description="YYYY-MM-DD")},
)
def baz():
    return 10


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


partitions_a = StaticPartitionsDefinition(["foo_a"])

partitions_b = StaticPartitionsDefinition(["foo_b"])

partitions_c = StaticPartitionsDefinition(["foo_c"])

partitions_d = StaticPartitionsDefinition(["foo_d"])


@asset(partitions_def=partitions_a)
def asset_a():
    pass


@asset(
    partitions_def=partitions_b,
    ins={"asset_a": AssetIn(partition_mapping=StaticPartitionMapping({"foo_a": "foo_b"}))},
)
def asset_b(asset_a):
    pass


@asset(
    partitions_def=partitions_c,
    ins={"asset_a": AssetIn(partition_mapping=StaticPartitionMapping({"foo_a": "foo_c"}))},
)
def asset_c(asset_a):
    pass


@asset(
    partitions_def=partitions_d,
    ins={"asset_a": AssetIn(partition_mapping=AllPartitionMapping())},
)
def asset_d(asset_a):
    pass


@asset(
    partitions_def=StaticPartitionsDefinition(["e_1", "e_2", "e_3"]),
    ins={"asset_a": AssetIn(partition_mapping=AllPartitionMapping())},
)
def asset_e(asset_a):
    pass


daily_partitions_def = DailyPartitionsDefinition("2023-01-01")


@asset(partitions_def=daily_partitions_def)
def daily_1():
    return 1


@asset(partitions_def=daily_partitions_def)
def daily_2(daily_1):
    return 1


@asset(
    partitions_def=daily_partitions_def,
    backfill_policy=BackfillPolicy.single_run(),
)
def asset_with_single_run_backfill_policy():
    return 1


@asset(
    partitions_def=daily_partitions_def,
    backfill_policy=BackfillPolicy.multi_run(),
)
def asset_with_multi_run_backfill_policy():
    pass


@repository
def the_repo():
    return [
        the_job,
        conditional_failure_job,
        partial_job,
        config_job,
        always_succeed_job,
        parallel_failure_job,
        # the lineage graph defined with these assets is such that: foo -> a1 -> bar -> b1
        # this requires ab1 to be split into two separate asset definitions using the automatic
        # subsetting capabilities. ab2 is defines similarly, so in total 4 copies of the "reusable"
        # op will exist in the full plan, whereas only a single copy will be needed for a subset
        # plan which only materializes foo -> a1 -> bar
        foo,
        bar,
        ab1,
        ab2,
        define_asset_job("twisted_asset_mess", selection="*b2", partitions_def=static_partitions),
        # baz is a configurable asset which has no dependencies
        baz,
        asset_a,
        asset_b,
        asset_c,
        asset_d,
        daily_1,
        daily_2,
        asset_e,
        asset_with_single_run_backfill_policy,
        asset_with_multi_run_backfill_policy,
    ]


def wait_for_all_runs_to_start(instance, timeout=10):
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            raise Exception("Timed out waiting for runs to start")
        time.sleep(0.5)

        pending_states = [
            DagsterRunStatus.NOT_STARTED,
            DagsterRunStatus.STARTING,
            DagsterRunStatus.STARTED,
        ]
        pending_runs = [run for run in instance.get_runs() if run.status in pending_states]

        if len(pending_runs) == 0:
            break


def wait_for_all_runs_to_finish(instance, timeout=10):
    start_time = time.time()
    FINISHED_STATES = [
        DagsterRunStatus.SUCCESS,
        DagsterRunStatus.FAILURE,
        DagsterRunStatus.CANCELED,
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


def test_simple_backfill(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
):
    external_partition_set = external_repo.get_external_partition_set("the_job_partition_set")
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

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))

    assert instance.get_runs_count() == 3
    runs = instance.get_runs()
    three, two, one = runs
    assert one.tags[BACKFILL_ID_TAG] == "simple"
    assert one.tags[PARTITION_NAME_TAG] == "one"
    assert two.tags[BACKFILL_ID_TAG] == "simple"
    assert two.tags[PARTITION_NAME_TAG] == "two"
    assert three.tags[BACKFILL_ID_TAG] == "simple"
    assert three.tags[PARTITION_NAME_TAG] == "three"


def test_canceled_backfill(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
):
    external_partition_set = external_repo.get_external_partition_set("the_job_partition_set")
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

    iterator = iter(
        execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon"))
    )
    next(iterator)
    assert instance.get_runs_count() == 1
    backfill = instance.get_backfills()[0]
    assert backfill.status == BulkActionStatus.REQUESTED
    instance.update_backfill(backfill.with_status(BulkActionStatus.CANCELED))
    list(iterator)
    backfill = instance.get_backfill(backfill.backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.CANCELED
    assert instance.get_runs_count() == 1


def test_failure_backfill(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
):
    output_file = _failure_flag_file()
    external_partition_set = external_repo.get_external_partition_set(
        "conditional_failure_job_partition_set"
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
                workspace_context, get_default_daemon_logger("BackfillDaemon")
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
    assert one.status == DagsterRunStatus.FAILURE
    assert step_succeeded(instance, one, "always_succeed")
    assert step_failed(instance, one, "conditionally_fail")
    assert step_did_not_run(instance, one, "after_failure")

    assert two.tags[BACKFILL_ID_TAG] == "shouldfail"
    assert two.tags[PARTITION_NAME_TAG] == "two"
    assert two.status == DagsterRunStatus.FAILURE
    assert step_succeeded(instance, two, "always_succeed")
    assert step_failed(instance, two, "conditionally_fail")
    assert step_did_not_run(instance, two, "after_failure")

    assert three.tags[BACKFILL_ID_TAG] == "shouldfail"
    assert three.tags[PARTITION_NAME_TAG] == "three"
    assert three.status == DagsterRunStatus.FAILURE
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
    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    wait_for_all_runs_to_start(instance)

    assert instance.get_runs_count() == 6
    from_failure_filter = RunsFilter(tags={BACKFILL_ID_TAG: "fromfailure"})
    assert instance.get_runs_count(filters=from_failure_filter) == 3

    runs = instance.get_runs(filters=from_failure_filter)
    three, two, one = runs

    assert one.tags[BACKFILL_ID_TAG] == "fromfailure"
    assert one.tags[PARTITION_NAME_TAG] == "one"
    assert one.status == DagsterRunStatus.SUCCESS
    assert step_did_not_run(instance, one, "always_succeed")
    assert step_succeeded(instance, one, "conditionally_fail")
    assert step_succeeded(instance, one, "after_failure")

    assert two.tags[BACKFILL_ID_TAG] == "fromfailure"
    assert two.tags[PARTITION_NAME_TAG] == "two"
    assert two.status == DagsterRunStatus.SUCCESS
    assert step_did_not_run(instance, one, "always_succeed")
    assert step_succeeded(instance, one, "conditionally_fail")
    assert step_succeeded(instance, one, "after_failure")

    assert three.tags[BACKFILL_ID_TAG] == "fromfailure"
    assert three.tags[PARTITION_NAME_TAG] == "three"
    assert three.status == DagsterRunStatus.SUCCESS
    assert step_did_not_run(instance, one, "always_succeed")
    assert step_succeeded(instance, one, "conditionally_fail")
    assert step_succeeded(instance, one, "after_failure")


@pytest.mark.skipif(IS_WINDOWS, reason="flaky in windows")
def test_partial_backfill(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
):
    external_partition_set = external_repo.get_external_partition_set("partial_job_partition_set")

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
    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    wait_for_all_runs_to_start(instance)

    assert instance.get_runs_count() == 3
    runs = instance.get_runs()
    three, two, one = runs

    assert one.tags[BACKFILL_ID_TAG] == "full"
    assert one.tags[PARTITION_NAME_TAG] == "one"
    assert one.status == DagsterRunStatus.SUCCESS
    assert step_succeeded(instance, one, "step_one")
    assert step_succeeded(instance, one, "step_two")
    assert step_succeeded(instance, one, "step_three")

    assert two.tags[BACKFILL_ID_TAG] == "full"
    assert two.tags[PARTITION_NAME_TAG] == "two"
    assert two.status == DagsterRunStatus.SUCCESS
    assert step_succeeded(instance, two, "step_one")
    assert step_succeeded(instance, two, "step_two")
    assert step_succeeded(instance, two, "step_three")

    assert three.tags[BACKFILL_ID_TAG] == "full"
    assert three.tags[PARTITION_NAME_TAG] == "three"
    assert three.status == DagsterRunStatus.SUCCESS
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
    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    wait_for_all_runs_to_start(instance)

    assert instance.get_runs_count() == 5
    partial_filter = RunsFilter(tags={BACKFILL_ID_TAG: "partial"})
    assert instance.get_runs_count(filters=partial_filter) == 3
    runs = instance.get_runs(filters=partial_filter)
    three, two, one = runs

    assert one.status == DagsterRunStatus.SUCCESS
    assert step_succeeded(instance, one, "step_one")
    assert step_did_not_run(instance, one, "step_two")
    assert step_did_not_run(instance, one, "step_three")

    assert two.status == DagsterRunStatus.SUCCESS
    assert step_succeeded(instance, two, "step_one")
    assert step_did_not_run(instance, two, "step_two")
    assert step_did_not_run(instance, two, "step_three")

    assert three.status == DagsterRunStatus.SUCCESS
    assert step_succeeded(instance, three, "step_one")
    assert step_did_not_run(instance, three, "step_two")
    assert step_did_not_run(instance, three, "step_three")


def test_large_backfill(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
):
    external_partition_set = external_repo.get_external_partition_set("config_job_partition_set")
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

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))

    assert instance.get_runs_count() == 3


def test_unloadable_backfill(instance, workspace_context):
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

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))

    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill("simple")
    assert backfill.status == BulkActionStatus.FAILED
    assert isinstance(backfill.error, SerializableErrorInfo)


def test_unloadable_backfill_retry(
    instance, workspace_context, unloadable_location_workspace_context
):
    asset_selection = [AssetKey("asset_a"), AssetKey("asset_b"), AssetKey("asset_c")]

    partition_keys = partitions_a.get_partition_keys()
    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id="retry_backfill",
            tags={"custom_tag_key": "custom_tag_value"},
            backfill_timestamp=pendulum.now().timestamp(),
            asset_selection=asset_selection,
            partition_names=partition_keys,
            dynamic_partitions_store=instance,
            all_partitions=False,
        )
    )
    assert instance.get_runs_count() == 0

    with environ({"DAGSTER_BACKFILL_RETRY_DEFINITION_CHANGED_ERROR": "1"}):
        # backfill can't start, but doesn't error
        list(
            execute_backfill_iteration(
                unloadable_location_workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
        assert instance.get_runs_count() == 0
        backfill = instance.get_backfill("retry_backfill")
        assert backfill.status == BulkActionStatus.REQUESTED

        # retries, still not loadable
        list(
            execute_backfill_iteration(
                unloadable_location_workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
        assert instance.get_runs_count() == 0
        backfill = instance.get_backfill("retry_backfill")
        assert backfill.status == BulkActionStatus.REQUESTED

        # continues once the code location is loadable again
        list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
        assert instance.get_runs_count() == 1


def test_backfill_from_partitioned_job(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
):
    partition_keys = my_config.partitions_def.get_partition_keys()
    external_partition_set = external_repo.get_external_partition_set(
        "comp_always_succeed_partition_set"
    )
    instance.add_backfill(
        PartitionBackfill(
            backfill_id="partition_schedule_from_job",
            partition_set_origin=external_partition_set.get_external_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=partition_keys[:3],
            from_failure=False,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=pendulum.now().timestamp(),
        )
    )
    assert instance.get_runs_count() == 0

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))

    assert instance.get_runs_count() == 3
    runs = reversed(list(instance.get_runs()))
    for idx, run in enumerate(runs):
        assert run.tags[BACKFILL_ID_TAG] == "partition_schedule_from_job"
        assert run.tags[PARTITION_NAME_TAG] == partition_keys[idx]


def test_backfill_with_asset_selection(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
):
    partition_keys = static_partitions.get_partition_keys()
    asset_selection = [AssetKey("foo"), AssetKey("a1"), AssetKey("bar")]
    job_def = the_repo.get_implicit_job_def_for_assets(asset_selection)
    assert job_def
    asset_job_name = job_def.name
    partition_set_name = f"{asset_job_name}_partition_set"
    external_partition_set = external_repo.get_external_partition_set(partition_set_name)
    instance.add_backfill(
        PartitionBackfill(
            backfill_id="backfill_with_asset_selection",
            partition_set_origin=external_partition_set.get_external_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=partition_keys,
            from_failure=False,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=pendulum.now().timestamp(),
            asset_selection=asset_selection,
        )
    )
    assert instance.get_runs_count() == 0

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    wait_for_all_runs_to_start(instance, timeout=30)
    assert instance.get_runs_count() == 3
    wait_for_all_runs_to_finish(instance, timeout=30)

    assert instance.get_runs_count() == 3
    runs = reversed(list(instance.get_runs()))
    for idx, run in enumerate(runs):
        assert run.tags[BACKFILL_ID_TAG] == "backfill_with_asset_selection"
        assert run.tags[PARTITION_NAME_TAG] == partition_keys[idx]
        assert step_succeeded(instance, run, "foo")
        assert step_succeeded(instance, run, "reusable")
        assert step_succeeded(instance, run, "bar")


def test_pure_asset_backfill_with_multiple_assets_selected(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
):
    asset_selection = [
        AssetKey("asset_a"),
        AssetKey("asset_b"),
        AssetKey("asset_c"),
        AssetKey("asset_d"),
    ]

    partition_keys = partitions_a.get_partition_keys()

    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id="backfill_with_multiple_assets_selected",
            tags={"custom_tag_key": "custom_tag_value"},
            backfill_timestamp=pendulum.now().timestamp(),
            asset_selection=asset_selection,
            partition_names=partition_keys,
            dynamic_partitions_store=instance,
            all_partitions=False,
        )
    )
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill("backfill_with_multiple_assets_selected")
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )
    assert instance.get_runs_count() == 1
    wait_for_all_runs_to_start(instance, timeout=30)
    wait_for_all_runs_to_finish(instance, timeout=30)
    run = instance.get_runs()[0]
    assert run.tags[BACKFILL_ID_TAG] == "backfill_with_multiple_assets_selected"
    assert run.tags["custom_tag_key"] == "custom_tag_value"
    assert run.asset_selection == {AssetKey(["asset_a"])}

    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )
    assert instance.get_runs_count() == 4
    wait_for_all_runs_to_start(instance, timeout=30)
    wait_for_all_runs_to_finish(instance, timeout=30)

    runs = instance.get_runs()

    assert any([run.asset_selection == {AssetKey(["asset_b"])}] for run in runs)
    assert any([run.asset_selection == {AssetKey(["asset_c"])}] for run in runs)
    assert any([run.asset_selection == {AssetKey(["asset_d"])}] for run in runs)

    assert all([run.status == DagsterRunStatus.SUCCESS] for run in runs)


def test_pure_asset_backfill(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
):
    del external_repo

    partition_keys = static_partitions.get_partition_keys()
    asset_selection = [AssetKey("foo"), AssetKey("a1"), AssetKey("bar")]
    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id="backfill_with_asset_selection",
            tags={"custom_tag_key": "custom_tag_value"},
            backfill_timestamp=pendulum.now().timestamp(),
            asset_selection=asset_selection,
            partition_names=partition_keys,
            dynamic_partitions_store=instance,
            all_partitions=False,
        )
    )
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill("backfill_with_asset_selection")
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    assert instance.get_runs_count() == 3
    wait_for_all_runs_to_start(instance, timeout=30)
    assert instance.get_runs_count() == 3
    wait_for_all_runs_to_finish(instance, timeout=30)

    assert instance.get_runs_count() == 3
    runs = reversed(list(instance.get_runs()))
    for run in runs:
        assert run.tags[BACKFILL_ID_TAG] == "backfill_with_asset_selection"
        assert run.tags["custom_tag_key"] == "custom_tag_value"
        assert step_succeeded(instance, run, "foo")
        assert step_succeeded(instance, run, "reusable")
        assert step_succeeded(instance, run, "bar")

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    backfill = instance.get_backfill("backfill_with_asset_selection")
    assert backfill
    assert backfill.status == BulkActionStatus.COMPLETED


def test_backfill_from_failure_for_subselection(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
):
    parallel_failure_job.execute_in_process(
        partition_key="one",
        instance=instance,
        op_selection=["fail_three", "success_four"],
        raise_on_error=False,
    )

    assert instance.get_runs_count() == 1
    wait_for_all_runs_to_finish(instance)
    run = next(iter(instance.get_runs()))
    assert run.status == DagsterRunStatus.FAILURE

    external_partition_set = external_repo.get_external_partition_set(
        "parallel_failure_job_partition_set"
    )

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

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    assert instance.get_runs_count() == 2
    child_run = next(iter(instance.get_runs(limit=1)))
    assert child_run.resolved_op_selection == run.resolved_op_selection
    assert child_run.op_selection == run.op_selection


def test_asset_backfill_cancellation(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
):
    asset_selection = [AssetKey("asset_a"), AssetKey("asset_b"), AssetKey("asset_c")]

    partition_keys = partitions_a.get_partition_keys()
    backfill_id = "backfill_with_multiple_assets_selected"

    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id=backfill_id,
            tags={"custom_tag_key": "custom_tag_value"},
            backfill_timestamp=pendulum.now().timestamp(),
            asset_selection=asset_selection,
            partition_names=partition_keys,
            dynamic_partitions_store=instance,
            all_partitions=False,
        )
    )
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )
    assert instance.get_runs_count() == 1
    run = instance.get_runs()[0]
    assert run.tags[BACKFILL_ID_TAG] == backfill_id
    assert run.asset_selection == {AssetKey(["asset_a"])}

    wait_for_all_runs_to_start(instance, timeout=30)
    instance.update_backfill(backfill.with_status(BulkActionStatus.CANCELING))
    wait_for_all_runs_to_finish(instance, timeout=30)

    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )

    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.CANCELED
    assert instance.get_runs_count() == 1  # Assert that additional runs are not created


# Check run submission at chunk boundary and off of chunk boundary
@pytest.mark.parametrize("num_partitions", [RUN_CHUNK_SIZE * 2, (RUN_CHUNK_SIZE) + 1])
def test_asset_backfill_submit_runs_in_chunks(
    instance: DagsterInstance, workspace_context: WorkspaceProcessContext, num_partitions: int
):
    asset_selection = [AssetKey("daily_1"), AssetKey("daily_2")]

    target_partitions = daily_partitions_def.get_partition_keys()[0:num_partitions]
    backfill_id = f"backfill_with_{num_partitions}_partitions"

    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id=backfill_id,
            tags={},
            backfill_timestamp=pendulum.now().timestamp(),
            asset_selection=asset_selection,
            partition_names=target_partitions,
            dynamic_partitions_store=instance,
            all_partitions=False,
        )
    )
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )

    assert instance.get_runs_count() == num_partitions


def test_asset_backfill_mid_iteration_cancel(
    instance: DagsterInstance, workspace_context: WorkspaceProcessContext
):
    asset_selection = [AssetKey("daily_1"), AssetKey("daily_2")]
    asset_graph = workspace_context.create_request_context().asset_graph

    num_partitions = RUN_CHUNK_SIZE * 2
    target_partitions = daily_partitions_def.get_partition_keys()[0:num_partitions]
    backfill_id = f"backfill_with_{num_partitions}_partitions"

    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id=backfill_id,
        tags={},
        backfill_timestamp=pendulum.now().timestamp(),
        asset_selection=asset_selection,
        partition_names=target_partitions,
        dynamic_partitions_store=instance,
        all_partitions=False,
    )
    instance.add_backfill(backfill)
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    def _override_backfill_cancellation(backfill: PartitionBackfill):
        instance._run_storage.update_backfill(  # noqa: SLF001
            backfill.with_status(BulkActionStatus.CANCELING)
        )

    # After submitting the first chunk, update the backfill to be CANCELING
    with mock.patch(
        "dagster._core.instance.DagsterInstance.update_backfill",
        side_effect=_override_backfill_cancellation,
    ):
        assert all(
            not error
            for error in list(
                execute_backfill_iteration(
                    workspace_context, get_default_daemon_logger("BackfillDaemon")
                )
            )
        )
        assert instance.get_runs_count() == RUN_CHUNK_SIZE

    # Check that the requested subset only contains runs that were submitted
    updated_backfill = instance.get_backfill(backfill_id)
    assert updated_backfill
    updated_asset_backfill_data = check.not_none(backfill.asset_backfill_data)
    assert all(
        len(partitions_subset) == RUN_CHUNK_SIZE
        for partitions_subset in updated_asset_backfill_data.requested_subset.partitions_subsets_by_asset_key.values()
    )

    # Execute backfill iteration again, confirming that no new runs have been added
    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )

    assert instance.get_runs_count() == RUN_CHUNK_SIZE
    assert instance.get_runs_count(RunsFilter(statuses=IN_PROGRESS_RUN_STATUSES)) == 0


def test_asset_backfill_forcible_mark_as_canceled_during_canceling_iteration(
    instance: DagsterInstance, workspace_context: WorkspaceProcessContext
):
    asset_selection = [AssetKey("daily_1"), AssetKey("daily_2")]
    asset_graph = workspace_context.create_request_context().asset_graph

    backfill_id = "backfill_id"
    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id=backfill_id,
        tags={},
        backfill_timestamp=pendulum.now().timestamp(),
        asset_selection=asset_selection,
        partition_names=["2023-01-01"],
        dynamic_partitions_store=instance,
        all_partitions=False,
    ).with_status(BulkActionStatus.CANCELING)
    instance.add_backfill(
        # Add some partitions in a "requested" state to mock that certain partitions are hanging
        backfill.with_asset_backfill_data(
            backfill.asset_backfill_data._replace(
                requested_subset=AssetGraphSubset(non_partitioned_asset_keys={AssetKey("daily_1")})
            ),
            dynamic_partitions_store=instance,
            asset_graph=asset_graph,
        )
    )
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.CANCELING

    override_get_backfill_num_calls = 0

    def _override_get_backfill(_):
        nonlocal override_get_backfill_num_calls
        if override_get_backfill_num_calls == 1:
            # Mark backfill as canceled during the middle of the cancellation iteration
            override_get_backfill_num_calls += 1
            return backfill.with_status(BulkActionStatus.CANCELED)
        else:
            override_get_backfill_num_calls += 1
            return backfill

    # After submitting the first chunk, update the backfill to be CANCELING
    with mock.patch(
        "dagster._core.instance.DagsterInstance.get_backfill",
        side_effect=_override_get_backfill,
    ):
        # Mock that a run is still in progress. If we don't add this, then the backfill will be
        # marked as failed
        with mock.patch("dagster._core.instance.DagsterInstance.get_run_ids", side_effect=["fake"]):
            assert all(
                not error
                for error in list(
                    execute_backfill_iteration(
                        workspace_context, get_default_daemon_logger("BackfillDaemon")
                    )
                )
            )

    updated_backfill = instance.get_backfill(backfill_id)
    assert updated_backfill
    # Assert that the backfill was indeed marked as canceled
    assert updated_backfill.status == BulkActionStatus.CANCELED


def test_asset_backfill_mid_iteration_code_location_unreachable_error(
    instance: DagsterInstance, workspace_context: WorkspaceProcessContext
):
    from dagster._core.execution.submit_asset_runs import _get_job_execution_data_from_run_request

    asset_selection = [AssetKey("asset_a"), AssetKey("asset_e")]
    asset_graph = workspace_context.create_request_context().asset_graph

    num_partitions = 1
    target_partitions = partitions_a.get_partition_keys()[0:num_partitions]
    backfill_id = "simple_fan_out_backfill"
    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id=backfill_id,
        tags={},
        backfill_timestamp=pendulum.now().timestamp(),
        asset_selection=asset_selection,
        partition_names=target_partitions,
        dynamic_partitions_store=instance,
        all_partitions=False,
    )
    instance.add_backfill(backfill)
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )
    updated_backfill = instance.get_backfill(backfill_id)
    assert updated_backfill
    assert updated_backfill.asset_backfill_data
    assert (
        updated_backfill.asset_backfill_data.requested_subset.num_partitions_and_non_partitioned_assets
        == 1
    )

    # The following backfill iteration will attempt to submit run requests for asset_e's three partitions.
    # The first call to _get_job_execution_data_from_run_request will succeed, but the second call will
    # raise a DagsterUserCodeUnreachableError. Subsequently only the first partition will be successfully
    # submitted.
    counter = 0

    def raise_code_unreachable_error_on_second_call(*args, **kwargs):
        nonlocal counter
        if counter == 0:
            counter += 1
            return _get_job_execution_data_from_run_request(*args, **kwargs)
        elif counter == 1:
            counter += 1
            raise DagsterUserCodeUnreachableError()
        else:
            # Should not attempt to create a run for the third partition if the second
            # errored with DagsterUserCodeUnreachableError
            raise Exception("Should not reach")

    with mock.patch(
        "dagster._core.execution.submit_asset_runs._get_job_execution_data_from_run_request",
        side_effect=raise_code_unreachable_error_on_second_call,
    ):
        assert all(
            not error
            for error in list(
                execute_backfill_iteration(
                    workspace_context, get_default_daemon_logger("BackfillDaemon")
                )
            )
        )

    assert instance.get_runs_count() == 2
    updated_backfill = instance.get_backfill(backfill_id)
    assert updated_backfill
    assert updated_backfill.asset_backfill_data
    assert (
        updated_backfill.asset_backfill_data.materialized_subset.num_partitions_and_non_partitioned_assets
        == 1
    )
    assert (
        updated_backfill.asset_backfill_data.requested_subset.num_partitions_and_non_partitioned_assets
        == 2
    )

    # Execute backfill iteration again, confirming that the two partitions that did not submit runs
    # on the previous iteration are requested on this iteration.
    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )
    # Assert that two new runs are submitted
    assert instance.get_runs_count() == 4

    updated_backfill = instance.get_backfill(backfill_id)
    assert updated_backfill
    assert updated_backfill.asset_backfill_data
    assert (
        updated_backfill.asset_backfill_data.requested_subset.num_partitions_and_non_partitioned_assets
        == 4
    )


def test_fail_backfill_when_runs_completed_but_partitions_marked_as_in_progress(
    instance: DagsterInstance, workspace_context: WorkspaceProcessContext
):
    asset_selection = [AssetKey("daily_1"), AssetKey("daily_2")]
    asset_graph = workspace_context.create_request_context().asset_graph

    target_partitions = ["2023-01-01"]
    backfill_id = "backfill_with_hanging_partitions"
    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id=backfill_id,
        tags={},
        backfill_timestamp=pendulum.now().timestamp(),
        asset_selection=asset_selection,
        partition_names=target_partitions,
        dynamic_partitions_store=instance,
        all_partitions=False,
    )
    instance.add_backfill(backfill)
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )
    assert instance.get_runs_count() == 1

    updated_backfill = instance.get_backfill(backfill_id)
    assert updated_backfill
    assert updated_backfill.asset_backfill_data

    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )

    updated_backfill = instance.get_backfill(backfill_id)
    assert updated_backfill
    assert updated_backfill.asset_backfill_data
    assert len(updated_backfill.asset_backfill_data.materialized_subset) == 2
    # Replace materialized_subset with an empty subset to mock "hanging" partitions
    # Mark the backfill as CANCELING
    instance.update_backfill(
        updated_backfill.with_asset_backfill_data(
            updated_backfill.asset_backfill_data._replace(materialized_subset=AssetGraphSubset()),
            dynamic_partitions_store=instance,
            asset_graph=asset_graph,
        ).with_status(BulkActionStatus.CANCELING)
    )

    errors = list(
        filter(
            lambda e: e is not None,
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            ),
        )
    )

    assert len(errors) == 1
    error_msg = check.not_none(errors[0]).message
    assert (
        "All runs have completed, but not all requested partitions have been marked as materialized or failed"
    ) in error_msg


def test_asset_backfill_with_single_run_backfill_policy(
    instance: DagsterInstance, workspace_context: WorkspaceProcessContext
):
    partitions = ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"]
    asset_graph = workspace_context.create_request_context().asset_graph

    backfill_id = "asset_backfill_with_backfill_policy"
    backfill = PartitionBackfill.from_partitions_by_assets(
        backfill_id=backfill_id,
        asset_graph=asset_graph,
        backfill_timestamp=pendulum.now().timestamp(),
        tags={},
        dynamic_partitions_store=instance,
        partitions_by_assets=[
            PartitionsByAssetSelector(
                asset_with_single_run_backfill_policy.key,
                PartitionsSelector(PartitionRangeSelector(partitions[0], partitions[-1])),
            )
        ],
    )
    instance.add_backfill(backfill)

    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED
    assert backfill.asset_selection == [asset_with_single_run_backfill_policy.key]

    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )

    assert instance.get_runs_count() == 1
    assert instance.get_runs()[0].tags.get(ASSET_PARTITION_RANGE_START_TAG) == partitions[0]
    assert instance.get_runs()[0].tags.get(ASSET_PARTITION_RANGE_END_TAG) == partitions[-1]


def test_asset_backfill_with_multi_run_backfill_policy(
    instance: DagsterInstance, workspace_context: WorkspaceProcessContext
):
    partitions = ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"]
    asset_graph = workspace_context.create_request_context().asset_graph

    backfill_id = "asset_backfill_with_multi_run_backfill_policy"
    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id=backfill_id,
        tags={},
        backfill_timestamp=pendulum.now().timestamp(),
        asset_selection=[asset_with_multi_run_backfill_policy.key],
        partition_names=partitions,
        dynamic_partitions_store=instance,
        all_partitions=False,
    )
    instance.add_backfill(backfill)

    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )

    assert instance.get_runs_count() == 4

    updated_backfill = instance.get_backfill(backfill_id)
    assert updated_backfill
    assert list(
        check.not_none(
            updated_backfill.asset_backfill_data
        ).requested_subset.iterate_asset_partitions()
    ) == [
        AssetKeyPartitionKey(asset_with_multi_run_backfill_policy.key, partition)
        for partition in partitions
    ]


def test_error_code_location(
    caplog, instance, workspace_context, unloadable_location_workspace_context
):
    asset_selection = [AssetKey("asset_a")]
    partition_keys = partitions_a.get_partition_keys()
    backfill_id = "dummy_backfill"

    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id=backfill_id,
            tags={},
            backfill_timestamp=pendulum.now().timestamp(),
            asset_selection=asset_selection,
            partition_names=partition_keys,
            dynamic_partitions_store=instance,
            all_partitions=False,
        )
    )

    errors = list(
        execute_backfill_iteration(
            unloadable_location_workspace_context, get_default_daemon_logger("BackfillDaemon")
        )
    )

    assert len(errors) == 1
    assert (
        "dagster._core.errors.DagsterAssetBackfillDataLoadError: Asset AssetKey(['asset_a']) existed at"
        " storage-time, but no longer does. This could be because it's inside a code location"
        " that's failing to load" in errors[0].message
    )
    assert "Failure loading location" in caplog.text


@pytest.mark.parametrize("backcompat_serialization", [True, False])
def test_raise_error_on_asset_backfill_partitions_defs_changes(
    caplog,
    instance,
    partitions_defs_changes_location_1_workspace_context,
    partitions_defs_changes_location_2_workspace_context,
    backcompat_serialization: bool,
):
    asset_selection = [AssetKey("time_partitions_def_changes")]
    partition_keys = ["2023-01-01"]
    backfill_id = "dummy_backfill"
    asset_graph = (
        partitions_defs_changes_location_1_workspace_context.create_request_context().asset_graph
    )

    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id=backfill_id,
        tags={},
        backfill_timestamp=pendulum.now().timestamp(),
        asset_selection=asset_selection,
        partition_names=partition_keys,
        dynamic_partitions_store=instance,
        all_partitions=False,
    )

    if backcompat_serialization:
        backfill = backfill._replace(
            serialized_asset_backfill_data=check.not_none(backfill.asset_backfill_data).serialize(
                instance, asset_graph
            ),
            asset_backfill_data=None,
        )

    instance.add_backfill(backfill)

    errors = list(
        execute_backfill_iteration(
            partitions_defs_changes_location_2_workspace_context,
            get_default_daemon_logger("BackfillDaemon"),
        )
    )

    assert len(errors) == 1
    error_msg = check.not_none(errors[0]).message
    assert ("partitions definition has changed") in error_msg or (
        "partitions definition for asset AssetKey(['time_partitions_def_changes']) has changed"
    ) in error_msg


@pytest.mark.parametrize("backcompat_serialization", [True, False])
def test_raise_error_on_partitions_defs_removed(
    caplog,
    instance,
    partitions_defs_changes_location_1_workspace_context,
    partitions_defs_changes_location_2_workspace_context,
    backcompat_serialization: bool,
):
    asset_selection = [AssetKey("partitions_def_removed")]
    partition_keys = ["2023-01-01"]
    backfill_id = "dummy_backfill"
    asset_graph = (
        partitions_defs_changes_location_1_workspace_context.create_request_context().asset_graph
    )

    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id=backfill_id,
        tags={},
        backfill_timestamp=pendulum.now().timestamp(),
        asset_selection=asset_selection,
        partition_names=partition_keys,
        dynamic_partitions_store=instance,
        all_partitions=False,
    )

    if backcompat_serialization:
        backfill = backfill._replace(
            serialized_asset_backfill_data=check.not_none(backfill.asset_backfill_data).serialize(
                instance, asset_graph
            ),
            asset_backfill_data=None,
        )

    instance.add_backfill(backfill)

    errors = [
        e
        for e in execute_backfill_iteration(
            partitions_defs_changes_location_2_workspace_context,
            get_default_daemon_logger("BackfillDaemon"),
        )
        if e is not None
    ]
    assert len(errors) == 1
    assert ("had a PartitionsDefinition at storage-time, but no longer does") in errors[0].message


def test_raise_error_on_target_static_partition_removed(
    caplog,
    instance,
    partitions_defs_changes_location_1_workspace_context,
    partitions_defs_changes_location_2_workspace_context,
):
    asset_selection = [AssetKey("static_partition_removed")]
    partition_keys = ["a"]
    asset_graph = (
        partitions_defs_changes_location_1_workspace_context.create_request_context().asset_graph
    )

    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id="dummy_backfill",
        tags={},
        backfill_timestamp=pendulum.now().timestamp(),
        asset_selection=asset_selection,
        partition_names=partition_keys,
        dynamic_partitions_store=instance,
        all_partitions=False,
    )
    instance.add_backfill(backfill)
    # When a static partitions def is changed, but all target partitions still exist,
    # backfill executes successfully
    errors = [
        e
        for e in execute_backfill_iteration(
            partitions_defs_changes_location_2_workspace_context,
            get_default_daemon_logger("BackfillDaemon"),
        )
        if e is not None
    ]
    assert len(errors) == 0

    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id="dummy_backfill_2",
        tags={},
        backfill_timestamp=pendulum.now().timestamp(),
        asset_selection=asset_selection,
        partition_names=["c"],
        dynamic_partitions_store=instance,
        all_partitions=False,
    )
    instance.add_backfill(backfill)
    # When a static partitions def is changed, but any target partitions is removed,
    # error is raised
    errors = [
        e
        for e in execute_backfill_iteration(
            partitions_defs_changes_location_2_workspace_context,
            get_default_daemon_logger("BackfillDaemon"),
        )
        if e is not None
    ]
    assert len(errors) == 1
    assert ("The following partitions were removed: {'c'}.") in errors[0].message


def test_partitions_def_changed_backfill_retry_envvar_set(
    caplog,
    instance,
    partitions_defs_changes_location_1_workspace_context,
    partitions_defs_changes_location_2_workspace_context,
):
    asset_selection = [AssetKey("time_partitions_def_changes")]
    partition_keys = ["2023-01-01"]
    backfill_id = "dummy_backfill"
    asset_graph = (
        partitions_defs_changes_location_1_workspace_context.create_request_context().asset_graph
    )

    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id=backfill_id,
        tags={},
        backfill_timestamp=pendulum.now().timestamp(),
        asset_selection=asset_selection,
        partition_names=partition_keys,
        dynamic_partitions_store=instance,
        all_partitions=False,
    )

    instance.add_backfill(backfill)

    with environ({"DAGSTER_BACKFILL_RETRY_DEFINITION_CHANGED_ERROR": "1"}):
        errors = list(
            execute_backfill_iteration(
                partitions_defs_changes_location_2_workspace_context,
                get_default_daemon_logger("BackfillDaemon"),
            )
        )

        assert len(errors) == 1
        error_msg = check.not_none(errors[0]).message
        assert ("partitions definition has changed") in error_msg or (
            "partitions definition for asset AssetKey(['time_partitions_def_changes']) has changed"
        ) in error_msg


def test_asset_backfill_logging(caplog, instance, workspace_context):
    asset_selection = [AssetKey("asset_a"), AssetKey("asset_b"), AssetKey("asset_c")]

    partition_keys = partitions_a.get_partition_keys()
    backfill_id = "backfill_with_multiple_assets_selected"

    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id=backfill_id,
            tags={"custom_tag_key": "custom_tag_value"},
            backfill_timestamp=pendulum.now().timestamp(),
            asset_selection=asset_selection,
            partition_names=partition_keys,
            dynamic_partitions_store=instance,
            all_partitions=False,
        )
    )
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )

    logs = caplog.text
    assert "Evaluating asset backfill backfill_with_multiple_assets_selected" in logs
    assert "DefaultPartitionsSubset(subset={'foo_b'})" in logs
    assert "latest_storage_id=None" in logs
    assert "AssetBackfillData" in logs


def test_asset_backfill_asset_graph_out_of_sync_with_workspace(
    caplog,
    instance: DagsterInstance,
    base_job_name_changes_location_1_workspace_context,
    base_job_name_changes_location_2_workspace_context,
):
    location_1_asset_graph = (
        base_job_name_changes_location_1_workspace_context.create_request_context().asset_graph
    )
    location_2_asset_graph = (
        base_job_name_changes_location_2_workspace_context.create_request_context().asset_graph
    )

    backfill_id = "hourly_asset_backfill"
    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=location_1_asset_graph,
        backfill_id=backfill_id,
        tags={},
        backfill_timestamp=pendulum.now().timestamp(),
        asset_selection=[AssetKey(["hourly_asset"])],
        partition_names=["2023-01-01-00:00"],
        dynamic_partitions_store=instance,
        all_partitions=False,
    )
    instance.add_backfill(backfill)

    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED
    with mock.patch(
        "dagster._core.workspace.workspace.IWorkspace.asset_graph",
        new_callable=mock.PropertyMock,
    ) as asset_graph_mock:
        asset_graph_mock.side_effect = [
            location_2_asset_graph,  # On first fetch, return location 2 asset graph,
            location_1_asset_graph,  # then return location 1 asset graph for subsequent fetch
        ]

        assert all(
            not error
            for error in list(
                execute_backfill_iteration(
                    base_job_name_changes_location_1_workspace_context,
                    get_default_daemon_logger("BackfillDaemon"),
                )
            )
        )

    logs = caplog.text
    assert "Execution plan is out of sync with the workspace" in logs

    assert instance.get_runs_count() == 1
    assert (
        len(
            instance.get_event_records(
                EventRecordsFilter(
                    DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                    asset_key=AssetKey(["hourly_asset"]),
                )
            )
        )
        == 1
    )
