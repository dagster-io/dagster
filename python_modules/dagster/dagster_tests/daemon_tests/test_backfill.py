import os
import random
import string
import sys
import time

import pendulum
import pytest
from dagster import (
    Any,
    AssetIn,
    AssetKey,
    AssetsDefinition,
    DagsterInstance,
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
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.definitions.partition import PartitionedConfig
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.host_representation import (
    ExternalRepository,
    ExternalRepositoryOrigin,
    InProcessCodeLocationOrigin,
)
from dagster._core.storage.dagster_run import DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import BACKFILL_ID_TAG, PARTITION_NAME_TAG
from dagster._core.test_utils import (
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
    # selected
    for asset_key in asset_selection:
        assert len(instance.run_ids_for_asset_key(asset_key)) == 3
    # not selected
    for asset_key in [AssetKey("a2"), AssetKey("b2"), AssetKey("baz")]:
        assert len(instance.run_ids_for_asset_key(asset_key)) == 0


def test_pure_asset_backfill_with_multiple_assets_selected(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    external_repo: ExternalRepository,
):
    asset_selection = [AssetKey("asset_a"), AssetKey("asset_b"), AssetKey("asset_c")]

    partition_keys = partitions_a.get_partition_keys()

    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=ExternalAssetGraph.from_workspace(
                workspace_context.create_request_context()
            ),
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
    assert instance.get_runs_count() == 3
    wait_for_all_runs_to_start(instance, timeout=30)
    wait_for_all_runs_to_finish(instance, timeout=30)

    runs = instance.get_runs()

    assert any([run.asset_selection == {AssetKey(["asset_b"])}] for run in runs)
    assert any([run.asset_selection == {AssetKey(["asset_c"])}] for run in runs)

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
            asset_graph=ExternalAssetGraph.from_workspace(
                workspace_context.create_request_context()
            ),
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
    # selected
    for asset_key in asset_selection:
        assert len(instance.run_ids_for_asset_key(asset_key)) == 3
    # not selected
    for asset_key in [AssetKey("a2"), AssetKey("b2"), AssetKey("baz")]:
        assert len(instance.run_ids_for_asset_key(asset_key)) == 0

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
    run = list(instance.get_runs())[0]
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
    child_run = list(instance.get_runs(limit=1))[0]
    assert child_run.solids_to_execute == run.solids_to_execute
    assert child_run.solid_selection == run.solid_selection
