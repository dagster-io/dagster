import json
import logging
import os
import random
import string
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import cast
from unittest import mock

import dagster as dg
import dagster._check as check
import pytest
from dagster import AssetExecutionContext, DagsterInstance
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets.graph.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.selector import (
    JobSubsetSelector,
    PartitionRangeSelector,
    PartitionsByAssetSelector,
    PartitionsSelector,
)
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.events import DagsterEventType
from dagster._core.execution.asset_backfill import (
    AssetBackfillData,
    get_asset_backfill_run_chunk_size,
)
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
from dagster._core.remote_origin import InProcessCodeLocationOrigin, RemoteRepositoryOrigin
from dagster._core.remote_representation.code_location import CodeLocation
from dagster._core.remote_representation.external import RemoteRepository
from dagster._core.storage.compute_log_manager import ComputeIOType
from dagster._core.storage.dagster_run import (
    IN_PROGRESS_RUN_STATUSES,
    DagsterRun,
    DagsterRunStatus,
    RunsFilter,
)
from dagster._core.storage.partition_status_cache import AssetPartitionStatus
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
    BACKFILL_ID_TAG,
    BACKFILL_TAGS,
    MAX_RETRIES_TAG,
    PARTITION_NAME_TAG,
)
from dagster._core.test_utils import (
    create_run_for_test,
    create_test_daemon_workspace_context,
    ensure_dagster_tests_import,
    environ,
    step_did_not_run,
    step_failed,
    step_succeeded,
    wait_for_futures,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.context import BaseWorkspaceRequestContext, WorkspaceProcessContext
from dagster._core.workspace.load_target import ModuleTarget
from dagster._daemon import get_default_daemon_logger
from dagster._daemon.auto_run_reexecution.auto_run_reexecution import (
    consume_new_runs_for_automatic_reexecution,
)
from dagster._daemon.backfill import execute_backfill_iteration
from dagster._time import get_current_timestamp
from dagster._utils import touch_file
from dagster._utils.error import SerializableErrorInfo
from dagster_shared import seven
from dagster_shared.seven import IS_WINDOWS, get_system_temp_directory

ensure_dagster_tests_import()
default_resource_defs = resource_defs = {"io_manager": dg.fs_io_manager}
logger = logging.getLogger("dagster.test_auto_run_reexecution")


DEFAULT_CHUNK_SIZE = 5


@pytest.fixture
def set_default_chunk_size():
    with environ({"DAGSTER_ASSET_BACKFILL_RUN_CHUNK_SIZE": str(DEFAULT_CHUNK_SIZE)}):
        assert get_asset_backfill_run_chunk_size() == DEFAULT_CHUNK_SIZE
        yield DEFAULT_CHUNK_SIZE


def _failure_flag_file():
    return os.path.join(get_system_temp_directory(), "conditionally_fail")


@dg.op
def always_succeed(_):
    return 1


@dg.graph()
def comp_always_succeed():
    always_succeed()


@dg.daily_partitioned_config(start_date="2021-05-05")
def my_config(_start, _end):
    return {}


always_succeed_job = comp_always_succeed.to_job(config=my_config)


@dg.op
def fail_op(_):
    raise Exception("blah")


@dg.op
def conditionally_fail(_, _input):
    if os.path.isfile(_failure_flag_file()):
        raise Exception("blah")

    return 1


@dg.op
def after_failure(_, _input):
    return 1


one_two_three_partitions = dg.StaticPartitionsDefinition(["one", "two", "three"])


@dg.multi_asset(
    specs=[
        dg.AssetSpec(f"a_{i:02}", skippable=True, partitions_def=one_two_three_partitions)
        for i in range(100)
    ],
    can_subset=True,
)
def my_multi_asset(context: AssetExecutionContext):
    for selected in sorted(context.selected_output_names):
        yield dg.Output(None, selected)


@dg.job(partitions_def=one_two_three_partitions)
def the_job():
    always_succeed()


@dg.job(partitions_def=one_two_three_partitions)
def conditional_failure_job():
    after_failure(conditionally_fail(always_succeed()))


@dg.job(partitions_def=one_two_three_partitions)
def partial_job():
    always_succeed.alias("step_one")()
    always_succeed.alias("step_two")()
    always_succeed.alias("step_three")()


@dg.job(partitions_def=one_two_three_partitions)
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


config_job_config = dg.PartitionedConfig(
    partitions_def=one_two_three_partitions,
    run_config_for_partition_key_fn=_large_partition_config,
)


@dg.op(config_schema=dg.Field(dg.Any))
def config_op(_):
    return 1


@dg.job(partitions_def=one_two_three_partitions, config=config_job_config)
def config_job():
    config_op()


def _unloadable_partition_set_origin():
    working_directory = os.path.dirname(__file__)
    return RemoteRepositoryOrigin(
        InProcessCodeLocationOrigin(
            LoadableTargetOrigin(
                executable_path=sys.executable,
                python_file=__file__,
                working_directory=working_directory,
            )
        ),
        "fake_repository",
    ).get_partition_set_origin("doesnt_exist")


static_partitions = dg.StaticPartitionsDefinition(["x", "y", "z"])


@dg.asset(partitions_def=static_partitions)
def foo():
    return 1


@dg.asset(partitions_def=static_partitions)
def bar(a1):
    return a1


@dg.asset(partitions_def=static_partitions)
def pass_on_retry(context):
    if context.run.parent_run_id is None:
        raise Exception("I failed!")


@dg.asset(partitions_def=static_partitions)
def always_fails():
    raise Exception("I always fail")


@dg.asset(
    config_schema={"myparam": dg.Field(str, description="YYYY-MM-DD")},
)
def baz():
    return 10


@dg.op(
    ins={"in1": dg.In(dg.Nothing), "in2": dg.In(dg.Nothing)},
    out={"out1": dg.Out(is_required=False), "out2": dg.Out(is_required=False)},
)
def reusable(context):
    selected_output_names = context.selected_output_names
    if "out1" in selected_output_names:
        yield dg.Output(1, "out1")
    if "out2" in selected_output_names:
        yield dg.Output(2, "out2")


ab1 = dg.AssetsDefinition(
    node_def=reusable,
    keys_by_input_name={
        "in1": dg.AssetKey("foo"),
        "in2": dg.AssetKey("bar"),
    },
    keys_by_output_name={"out1": dg.AssetKey("a1"), "out2": dg.AssetKey("b1")},
    partitions_def=static_partitions,
    can_subset=True,
    asset_deps={dg.AssetKey("a1"): {dg.AssetKey("foo")}, dg.AssetKey("b1"): {dg.AssetKey("bar")}},
)

ab2 = dg.AssetsDefinition(
    node_def=reusable,
    keys_by_input_name={
        "in1": dg.AssetKey("foo"),
        "in2": dg.AssetKey("bar"),
    },
    keys_by_output_name={"out1": dg.AssetKey("a2"), "out2": dg.AssetKey("b2")},
    partitions_def=static_partitions,
    can_subset=True,
    asset_deps={dg.AssetKey("a2"): {dg.AssetKey("foo")}, dg.AssetKey("b2"): {dg.AssetKey("bar")}},
)


partitions_a = dg.StaticPartitionsDefinition(["foo_a"])

partitions_b = dg.StaticPartitionsDefinition(["foo_b"])

partitions_c = dg.StaticPartitionsDefinition(["foo_c"])

partitions_d = dg.StaticPartitionsDefinition(["foo_d"])

partitions_f = dg.StaticPartitionsDefinition(["foo_f", "bar_f"])
partitions_g = dg.StaticPartitionsDefinition(["foo_g", "bar_g"])


@dg.asset(partitions_def=partitions_a)
def asset_a():
    pass


@dg.asset(
    partitions_def=partitions_b,
    ins={"asset_a": dg.AssetIn(partition_mapping=dg.StaticPartitionMapping({"foo_a": "foo_b"}))},
)
def asset_b(asset_a):
    pass


@dg.asset(
    partitions_def=partitions_c,
    ins={"asset_a": dg.AssetIn(partition_mapping=dg.StaticPartitionMapping({"foo_a": "foo_c"}))},
)
def asset_c(asset_a):
    pass


@dg.asset(
    partitions_def=partitions_d,
    ins={"asset_a": dg.AssetIn(partition_mapping=dg.AllPartitionMapping())},
)
def asset_d(asset_a):
    pass


@dg.asset(
    partitions_def=dg.StaticPartitionsDefinition(["e_1", "e_2", "e_3"]),
    ins={"asset_a": dg.AssetIn(partition_mapping=dg.AllPartitionMapping())},
)
def asset_e(asset_a):
    pass


@dg.asset(partitions_def=partitions_f)
def asset_f():
    pass


@dg.asset(
    partitions_def=partitions_g,
    ins={
        "asset_f": dg.AssetIn(
            partition_mapping=dg.StaticPartitionMapping({"foo_f": "foo_g", "bar_f": "bar_g"})
        )
    },
)
def asset_g(asset_f):
    pass


@dg.asset(partitions_def=partitions_a)
def fails_once_asset_a(context):
    if context.run.parent_run_id is None:
        raise Exception("I failed!")


@dg.asset(
    partitions_def=partitions_b,
    ins={
        "fails_once_asset_a": dg.AssetIn(
            partition_mapping=dg.StaticPartitionMapping({"foo_a": "foo_b"})
        )
    },
)
def downstream_of_fails_once_asset_b(fails_once_asset_a):
    pass


@dg.asset(
    partitions_def=partitions_c,
    ins={
        "fails_once_asset_a": dg.AssetIn(
            partition_mapping=dg.StaticPartitionMapping({"foo_a": "foo_c"})
        )
    },
)
def downstream_of_fails_once_asset_c(fails_once_asset_a):
    pass


daily_partitions_def = dg.DailyPartitionsDefinition("2023-01-01")


@dg.asset(partitions_def=daily_partitions_def)
def daily_1():
    return 1


@dg.asset(partitions_def=daily_partitions_def)
def daily_2(daily_1):
    return 1


multi_partitions_def = dg.MultiPartitionsDefinition(
    {"day": daily_partitions_def, "name": static_partitions}
)


@dg.asset(
    partitions_def=multi_partitions_def,
    backfill_policy=BackfillPolicy.single_run(),
)
def multi_partitioned_asset_with_single_run_bp() -> None:
    return


@dg.asset(
    partitions_def=multi_partitions_def,
)
def multi_partitioned_asset() -> None:
    return


@dg.asset(
    partitions_def=daily_partitions_def,
    backfill_policy=BackfillPolicy.single_run(),
)
def asset_with_single_run_backfill_policy() -> None:
    pass


@dg.asset(
    partitions_def=daily_partitions_def,
    backfill_policy=BackfillPolicy.multi_run(),
)
def asset_with_multi_run_backfill_policy() -> None:
    pass


@dg.asset(
    partitions_def=daily_partitions_def,
    backfill_policy=BackfillPolicy.single_run(),
    deps=[
        asset_with_single_run_backfill_policy,
        dg.AssetDep(
            "complex_asset_with_backfill_policy",
            partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
        ),
    ],
)
def complex_asset_with_backfill_policy(context: AssetExecutionContext) -> None:
    statuses = context.instance.get_status_by_partition(
        asset_key=asset_with_single_run_backfill_policy.key,
        partition_keys=context.partition_keys,
        partitions_def=daily_partitions_def,
    )
    assert statuses
    context.log.info(f"got {statuses}")
    assert all(status == AssetPartitionStatus.MATERIALIZED for status in statuses.values())


asset_job_partitions = dg.StaticPartitionsDefinition(["a", "b", "c", "d"])


class BpSingleRunConfig(dg.Config):
    name: str


@dg.asset(partitions_def=asset_job_partitions, backfill_policy=BackfillPolicy.single_run())
def bp_single_run(context: AssetExecutionContext):
    return {k: 1 for k in context.partition_keys}


@dg.asset(partitions_def=asset_job_partitions, backfill_policy=BackfillPolicy.single_run())
def bp_single_run_config(context: AssetExecutionContext, config: BpSingleRunConfig):
    context.log.info(config.name)
    return {k: 1 for k in context.partition_keys}


@dg.asset(partitions_def=asset_job_partitions, backfill_policy=BackfillPolicy.multi_run(2))
def bp_multi_run(context: AssetExecutionContext):
    return {k: 1 for k in context.partition_keys}


@dg.asset(partitions_def=asset_job_partitions)
def bp_none(context: AssetExecutionContext):
    return 1


old_dynamic_partitions_def = dg.DynamicPartitionsDefinition(
    partition_fn=lambda _: ["a", "b", "c", "d"]
)


@dg.job(partitions_def=old_dynamic_partitions_def)
def old_dynamic_partitions_job():
    always_succeed()


@dg.repository
def the_repo():
    return [
        the_job,
        conditional_failure_job,
        partial_job,
        config_job,
        always_succeed_job,
        parallel_failure_job,
        old_dynamic_partitions_job,
        # the lineage graph defined with these assets is such that: foo -> a1 -> bar -> b1
        # this requires ab1 to be split into two separate asset definitions using the automatic
        # subsetting capabilities. ab2 is defines similarly, so in total 4 copies of the "reusable"
        # op will exist in the full plan, whereas only a single copy will be needed for a subset
        # plan which only materializes foo -> a1 -> bar
        foo,
        bar,
        ab1,
        ab2,
        dg.define_asset_job(
            "twisted_asset_mess", selection="*b2", partitions_def=static_partitions
        ),
        always_fails,
        pass_on_retry,
        # baz is a configurable asset which has no dependencies
        baz,
        my_multi_asset,
        asset_a,
        asset_b,
        asset_c,
        asset_d,
        daily_1,
        daily_2,
        asset_e,
        asset_f,
        asset_g,
        multi_partitioned_asset_with_single_run_bp,
        multi_partitioned_asset,
        fails_once_asset_a,
        downstream_of_fails_once_asset_b,
        downstream_of_fails_once_asset_c,
        asset_with_single_run_backfill_policy,
        asset_with_multi_run_backfill_policy,
        complex_asset_with_backfill_policy,
        bp_single_run,
        bp_single_run_config,
        bp_multi_run,
        bp_none,
        dg.define_asset_job(
            "bp_single_run_asset_job",
            selection=[bp_single_run_config, bp_single_run],
            tags={"alpha": "beta"},
            config={"ops": {"bp_single_run_config": {"config": {"name": "harry"}}}},
        ),
        dg.define_asset_job(
            "bp_multi_run_asset_job",
            selection=[bp_multi_run],
            tags={"alpha": "beta"},
        ),
        dg.define_asset_job(
            "bp_none_asset_job",
            selection=[bp_none],
        ),
        dg.define_asset_job(
            "standard_partitioned_asset_job",
            selection=AssetSelection.assets("foo", "a1", "bar"),
        ),
        dg.define_asset_job(
            "multi_asset_job",
            selection=[my_multi_asset],
        ),
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


@pytest.mark.parametrize("parallel", [True, False])
def test_simple_backfill(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
    parallel: bool,
):
    partition_set = remote_repo.get_partition_set("the_job_partition_set")
    instance.add_backfill(
        PartitionBackfill(
            backfill_id="simple",
            partition_set_origin=partition_set.get_remote_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=["one", "two", "three"],
            from_failure=False,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=get_current_timestamp(),
        )
    )
    assert instance.get_runs_count() == 0

    if parallel:
        backfill_daemon_futures = {}
        list(
            execute_backfill_iteration(
                workspace_context,
                get_default_daemon_logger("BackfillDaemon"),
                threadpool_executor=ThreadPoolExecutor(2),
                backfill_futures=backfill_daemon_futures,
            )
        )

        wait_for_futures(backfill_daemon_futures)
    else:
        list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
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


@pytest.mark.parametrize("parallel", [True, False])
def test_two_backfills_at_the_same_time(
    tmp_path: Path,
    parallel: bool,
):
    # In order to avoid deadlock, we need to ensure that the instance we
    # are using will launch runs in separate subprocesses rather than in
    # the same in-memory process. This is akin to the context created in
    # https://github.com/dagster-io/dagster/blob/a116c44/python_modules/dagster/dagster_tests/scheduler_tests/conftest.py#L53-L71
    with dg.instance_for_test(
        overrides={
            "event_log_storage": {
                "module": "dagster._core.storage.event_log",
                "class": "ConsolidatedSqliteEventLogStorage",
                "config": {"base_dir": str(tmp_path)},
            },
            "run_retries": {"enabled": True},
        }
    ) as instance:
        with create_test_daemon_workspace_context(
            workspace_load_target=ModuleTarget(
                module_name="dagster_tests.daemon_tests.test_backfill",
                attribute="the_repo",
                working_directory=os.path.join(os.path.dirname(__file__), "..", ".."),
                location_name="test_location",
            ),
            instance=instance,
        ) as workspace_context:
            remote_repo = cast(
                "CodeLocation",
                next(
                    iter(
                        workspace_context.create_request_context()
                        .get_code_location_entries()
                        .values()
                    )
                ).code_location,
            ).get_repository("the_repo")

            first_partition_set = remote_repo.get_partition_set("the_job_partition_set")
            second_partition_keys = my_config.partitions_def.get_partition_keys()
            second_partition_set = remote_repo.get_partition_set(
                "comp_always_succeed_partition_set"
            )
            instance.add_backfill(
                PartitionBackfill(
                    backfill_id="simple",
                    partition_set_origin=first_partition_set.get_remote_origin(),
                    status=BulkActionStatus.REQUESTED,
                    partition_names=["one", "two", "three"],
                    from_failure=False,
                    reexecution_steps=None,
                    tags=None,
                    backfill_timestamp=get_current_timestamp(),
                )
            )
            instance.add_backfill(
                PartitionBackfill(
                    backfill_id="partition_schedule_from_job",
                    partition_set_origin=second_partition_set.get_remote_origin(),
                    status=BulkActionStatus.REQUESTED,
                    partition_names=second_partition_keys[:3],
                    from_failure=False,
                    reexecution_steps=None,
                    tags=None,
                    backfill_timestamp=get_current_timestamp(),
                )
            )
            assert instance.get_runs_count() == 0

            if parallel:
                threadpool_executor = ThreadPoolExecutor(4)
                backfill_daemon_futures = {}
                list(
                    execute_backfill_iteration(
                        workspace_context,
                        get_default_daemon_logger("BackfillDaemon"),
                        threadpool_executor=threadpool_executor,
                        backfill_futures=backfill_daemon_futures,
                    )
                )

                wait_for_futures(backfill_daemon_futures)
            else:
                list(
                    execute_backfill_iteration(
                        workspace_context, get_default_daemon_logger("BackfillDaemon")
                    )
                )

            assert instance.get_runs_count() == 6

            runs = list(instance.get_runs())
            backfill_ids = sorted(run.tags[BACKFILL_ID_TAG] for run in runs)
            partition_names = {run.tags[PARTITION_NAME_TAG] for run in runs}
            assert backfill_ids == ["partition_schedule_from_job"] * 3 + ["simple"] * 3
            assert partition_names == {"one", "two", "three", *second_partition_keys[:3]}


@pytest.mark.parametrize("parallel", [True, False])
def test_failure_backfill(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
    parallel: bool,
):
    output_file = _failure_flag_file()
    partition_set = remote_repo.get_partition_set("conditional_failure_job_partition_set")
    instance.add_backfill(
        PartitionBackfill(
            backfill_id="shouldfail",
            partition_set_origin=partition_set.get_remote_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=["one", "two", "three"],
            from_failure=False,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=get_current_timestamp(),
        )
    )
    assert instance.get_runs_count() == 0

    try:
        touch_file(output_file)
        if parallel:
            backfill_daemon_futures = {}
            list(
                execute_backfill_iteration(
                    workspace_context,
                    get_default_daemon_logger("BackfillDaemon"),
                    threadpool_executor=ThreadPoolExecutor(2),
                    backfill_futures=backfill_daemon_futures,
                )
            )

            wait_for_futures(backfill_daemon_futures)
        else:
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
            partition_set_origin=partition_set.get_remote_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=["one", "two", "three"],
            from_failure=True,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=get_current_timestamp(),
        )
    )

    assert not os.path.isfile(_failure_flag_file())
    if parallel:
        backfill_daemon_futures = {}
        list(
            execute_backfill_iteration(
                workspace_context,
                get_default_daemon_logger("BackfillDaemon"),
                threadpool_executor=ThreadPoolExecutor(2),
                backfill_futures=backfill_daemon_futures,
            )
        )

        wait_for_futures(backfill_daemon_futures)
    else:
        list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )

    wait_for_all_runs_to_start(instance)

    assert instance.get_runs_count() == 6
    from_failure_filter = dg.RunsFilter(tags={BACKFILL_ID_TAG: "fromfailure"})
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


def test_job_backfill_status(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
):
    partition_set = remote_repo.get_partition_set("the_job_partition_set")
    instance.add_backfill(
        PartitionBackfill(
            backfill_id="simple",
            partition_set_origin=partition_set.get_remote_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=["one", "two", "three"],
            from_failure=False,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=get_current_timestamp(),
        )
    )
    assert instance.get_runs_count() == 0

    # seed an in progress run so that this run won't get launched by the backfill daemon and will
    # remain in the in progress state
    fake_run = create_run_for_test(
        instance=instance,
        status=DagsterRunStatus.STARTED,
        tags={
            **DagsterRun.tags_for_backfill_id("simple"),
            PARTITION_NAME_TAG: "one",
        },
    )

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))

    assert instance.get_runs_count() == 3
    backfill = instance.get_backfill("simple")
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    # manually update the run to be in a finished state, backfill should be marked complete on next iteration
    instance.delete_run(fake_run.run_id)
    create_run_for_test(
        instance=instance,
        status=DagsterRunStatus.SUCCESS,
        tags={
            **DagsterRun.tags_for_backfill_id("simple"),
            PARTITION_NAME_TAG: "one",
        },
    )

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))

    assert instance.get_runs_count() == 3
    backfill = instance.get_backfill("simple")
    assert backfill
    assert backfill.status == BulkActionStatus.COMPLETED_SUCCESS
    assert backfill.backfill_end_timestamp is not None


@pytest.mark.skipif(IS_WINDOWS, reason="flaky in windows")
def test_partial_backfill(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
):
    partition_set = remote_repo.get_partition_set("partial_job_partition_set")

    # create full runs, where every step is executed
    instance.add_backfill(
        PartitionBackfill(
            backfill_id="full",
            partition_set_origin=partition_set.get_remote_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=["one", "two", "three"],
            from_failure=False,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=get_current_timestamp(),
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
            partition_set_origin=partition_set.get_remote_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=["one", "two", "three"],
            from_failure=False,
            reexecution_steps=["step_one"],
            tags=None,
            backfill_timestamp=get_current_timestamp(),
        )
    )
    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    wait_for_all_runs_to_start(instance)

    assert instance.get_runs_count() == 5
    partial_filter = dg.RunsFilter(tags={BACKFILL_ID_TAG: "partial"})
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
    remote_repo: RemoteRepository,
):
    partition_set = remote_repo.get_partition_set("config_job_partition_set")
    instance.add_backfill(
        PartitionBackfill(
            backfill_id="simple",
            partition_set_origin=partition_set.get_remote_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=["one", "two", "three"],
            from_failure=False,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=get_current_timestamp(),
        )
    )
    assert instance.get_runs_count() == 0

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))

    assert instance.get_runs_count() == 3


def test_backfill_is_processed_only_once(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
):
    backfill_id = "simple"
    partition_set = remote_repo.get_partition_set("config_job_partition_set")
    instance.add_backfill(
        PartitionBackfill(
            backfill_id=backfill_id,
            partition_set_origin=partition_set.get_remote_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=["one", "two", "three"],
            from_failure=False,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=get_current_timestamp(),
        )
    )
    assert instance.get_runs_count() == 0

    threadpool_executor = ThreadPoolExecutor(2)
    backfill_daemon_futures = {}
    list(
        execute_backfill_iteration(
            workspace_context,
            get_default_daemon_logger("BackfillDaemon"),
            threadpool_executor=threadpool_executor,
            backfill_futures=backfill_daemon_futures,
        )
    )

    assert instance.get_runs_count() == 0
    future = backfill_daemon_futures[backfill_id]

    with mock.patch.object(
        threadpool_executor, "submit", side_effect=AssertionError("Should not be called")
    ):
        list(
            execute_backfill_iteration(
                workspace_context,
                get_default_daemon_logger("BackfillDaemon"),
                threadpool_executor=threadpool_executor,
                backfill_futures=backfill_daemon_futures,
            )
        )

    assert instance.get_runs_count() == 0
    assert backfill_daemon_futures[backfill_id] is future

    wait_for_futures(backfill_daemon_futures)

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
            backfill_timestamp=get_current_timestamp(),
        )
    )
    assert instance.get_runs_count() == 0

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))

    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill("simple")
    assert backfill.status == BulkActionStatus.FAILING
    assert isinstance(backfill.error, SerializableErrorInfo)

    # one more iteration to ensure the launched runs are canceled, then the backfill is marked failed
    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    backfill = instance.get_backfill("simple")
    assert backfill.status == BulkActionStatus.FAILED


def test_unloadable_asset_backfill(instance, workspace_context):
    backfill_id = "simple_fan_out_backfill"
    asset_backfill_data = AssetBackfillData.empty(
        target_subset=AssetGraphSubset(
            partitions_subsets_by_asset_key={
                dg.AssetKey(["does_not_exist"]): my_config.partitions_def.empty_subset()
            }
        ),
        backfill_start_timestamp=get_current_timestamp(),
        dynamic_partitions_store=instance,
    )

    backfill = PartitionBackfill(
        backfill_id=backfill_id,
        status=BulkActionStatus.REQUESTED,
        from_failure=False,
        tags={},
        backfill_timestamp=get_current_timestamp(),
        asset_selection=[dg.AssetKey(["does_not_exist"])],
        serialized_asset_backfill_data=None,
        asset_backfill_data=asset_backfill_data,
        title=None,
        description=None,
    )

    instance.add_backfill(backfill)
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))

    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill("simple_fan_out_backfill")

    # No retries because of the nature of the error
    assert backfill.status == BulkActionStatus.FAILING
    assert backfill.failure_count == 1
    assert isinstance(backfill.error, SerializableErrorInfo)
    assert backfill.backfill_end_timestamp is None

    # once more iteration to ensure all launched runs are canceled, then the backfill is marked failed
    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    backfill = instance.get_backfill("simple_fan_out_backfill")
    assert backfill.status == BulkActionStatus.FAILED
    assert backfill.backfill_end_timestamp is not None


def test_asset_backfill_retryable_error(instance, workspace_context):
    asset_selection = [dg.AssetKey("asset_f"), dg.AssetKey("asset_g")]
    asset_graph = workspace_context.create_request_context().asset_graph

    num_partitions = 2
    target_partitions = partitions_f.get_partition_keys()[0:num_partitions]
    backfill_id = "backfill_with_roots_multiple_partitions"
    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id=backfill_id,
        tags={},
        backfill_timestamp=get_current_timestamp(),
        asset_selection=asset_selection,
        partition_names=target_partitions,
        dynamic_partitions_store=instance,
        all_partitions=False,
        title=None,
        description=None,
        run_config=None,
    )
    instance.add_backfill(backfill)
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    # The following backfill iteration will attempt to submit run requests for asset_f's two partitions.
    # The first call to get_job_execution_data_from_run_request will succeed, but the second call will
    # raise a DagsterUserCodeUnreachableError. Subsequently only the first partition will be successfully
    # submitted.
    def raise_retryable_error(*args, **kwargs):
        raise Exception("This is transient because it is not a DagsterError or a CheckError")

    with mock.patch(
        "dagster._core.execution.submit_asset_runs.get_job_execution_data_from_run_request",
        side_effect=raise_retryable_error,
    ):
        with environ({"DAGSTER_MAX_ASSET_BACKFILL_RETRIES": "2"}):
            errors = [
                error
                for error in list(
                    execute_backfill_iteration(
                        workspace_context, get_default_daemon_logger("BackfillDaemon")
                    )
                )
                if error
            ]
            assert len(errors) == 1
            assert "This is transient because it is not a DagsterError or a CheckError" in str(
                errors[0]
            )

            assert instance.get_runs_count() == 0
            updated_backfill = instance.get_backfill(backfill_id)

            assert updated_backfill
            assert updated_backfill.asset_backfill_data

            # Requested with failure_count 1 because it will retry
            assert updated_backfill.status == BulkActionStatus.REQUESTED
            assert updated_backfill.failure_count == 1

            errors = [
                error
                for error in list(
                    execute_backfill_iteration(
                        workspace_context, get_default_daemon_logger("BackfillDaemon")
                    )
                )
                if error
            ]
            assert len(errors) == 1

            updated_backfill = instance.get_backfill(backfill_id)
            assert updated_backfill.status == BulkActionStatus.REQUESTED
            assert updated_backfill.failure_count == 2

            # Fails once it exceeds DAGSTER_MAX_ASSET_BACKFILL_RETRIES retries
            errors = [
                error
                for error in list(
                    execute_backfill_iteration(
                        workspace_context, get_default_daemon_logger("BackfillDaemon")
                    )
                )
                if error
            ]
            assert len(errors) == 1

            updated_backfill = instance.get_backfill(backfill_id)
            assert updated_backfill.status == BulkActionStatus.FAILING
            assert updated_backfill.failure_count == 3
            assert updated_backfill.backfill_end_timestamp is None

            # one more iteration for the backfill to ensure all runs are canceled, then it's marked failed
            list(
                execute_backfill_iteration(
                    workspace_context, get_default_daemon_logger("BackfillDaemon")
                )
            )
            updated_backfill = instance.get_backfill(backfill_id)
            assert updated_backfill.status == BulkActionStatus.FAILED
            assert updated_backfill.backfill_end_timestamp is not None


def test_unloadable_backfill_retry(
    instance, workspace_context, unloadable_location_workspace_context
):
    asset_selection = [dg.AssetKey("asset_a"), dg.AssetKey("asset_b"), dg.AssetKey("asset_c")]

    partition_keys = partitions_a.get_partition_keys()
    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id="retry_backfill",
            tags={"custom_tag_key": "custom_tag_value"},
            backfill_timestamp=get_current_timestamp(),
            asset_selection=asset_selection,
            partition_names=partition_keys,
            dynamic_partitions_store=instance,
            all_partitions=False,
            title=None,
            description=None,
            run_config=None,
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
    remote_repo: RemoteRepository,
):
    partition_keys = my_config.partitions_def.get_partition_keys()
    partition_set = remote_repo.get_partition_set("comp_always_succeed_partition_set")
    instance.add_backfill(
        PartitionBackfill(
            backfill_id="partition_schedule_from_job",
            partition_set_origin=partition_set.get_remote_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=partition_keys[:3],
            from_failure=False,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=get_current_timestamp(),
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
    remote_repo: RemoteRepository,
):
    partition_keys = static_partitions.get_partition_keys()
    asset_selection = [dg.AssetKey("foo"), dg.AssetKey("a1"), dg.AssetKey("bar")]
    job_def = the_repo.get_job("standard_partitioned_asset_job")
    assert job_def
    asset_job_name = job_def.name
    partition_set_name = f"{asset_job_name}_partition_set"
    partition_set = remote_repo.get_partition_set(partition_set_name)
    instance.add_backfill(
        PartitionBackfill(
            backfill_id="backfill_with_asset_selection",
            partition_set_origin=partition_set.get_remote_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=partition_keys,
            from_failure=False,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=get_current_timestamp(),
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
    remote_repo: RemoteRepository,
):
    asset_selection = [
        dg.AssetKey("asset_a"),
        dg.AssetKey("asset_b"),
        dg.AssetKey("asset_c"),
        dg.AssetKey("asset_d"),
    ]

    partition_keys = partitions_a.get_partition_keys()

    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id="backfill_with_multiple_assets_selected",
            tags={"custom_tag_key": "custom_tag_value"},
            backfill_timestamp=get_current_timestamp(),
            asset_selection=asset_selection,
            partition_names=partition_keys,
            dynamic_partitions_store=instance,
            all_partitions=False,
            title=None,
            description=None,
            run_config=None,
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
    assert run.asset_selection == {dg.AssetKey(["asset_a"])}

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

    assert any([run.asset_selection == {dg.AssetKey(["asset_b"])}] for run in runs)
    assert any([run.asset_selection == {dg.AssetKey(["asset_c"])}] for run in runs)
    assert any([run.asset_selection == {dg.AssetKey(["asset_d"])}] for run in runs)

    assert all([run.status == DagsterRunStatus.SUCCESS] for run in runs)


def test_pure_asset_backfill(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
):
    del remote_repo

    partition_keys = static_partitions.get_partition_keys()
    asset_selection = [dg.AssetKey("foo"), dg.AssetKey("a1"), dg.AssetKey("bar")]
    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id="backfill_with_asset_selection",
            tags={"custom_tag_key": "custom_tag_value"},
            backfill_timestamp=get_current_timestamp(),
            asset_selection=asset_selection,
            partition_names=partition_keys,
            dynamic_partitions_store=instance,
            all_partitions=False,
            title=None,
            description=None,
            run_config=None,
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
    assert backfill.status == BulkActionStatus.COMPLETED_SUCCESS
    assert backfill.backfill_end_timestamp is not None


def test_backfill_from_failure_for_subselection(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
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

    partition_set = remote_repo.get_partition_set("parallel_failure_job_partition_set")

    instance.add_backfill(
        PartitionBackfill(
            backfill_id="fromfailure",
            partition_set_origin=partition_set.get_remote_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=["one"],
            from_failure=True,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=get_current_timestamp(),
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
    asset_selection = [dg.AssetKey("asset_a"), dg.AssetKey("asset_b"), dg.AssetKey("asset_c")]

    partition_keys = partitions_a.get_partition_keys()
    backfill_id = "backfill_with_multiple_assets_selected"

    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id=backfill_id,
            tags={"custom_tag_key": "custom_tag_value"},
            backfill_timestamp=get_current_timestamp(),
            asset_selection=asset_selection,
            partition_names=partition_keys,
            dynamic_partitions_store=instance,
            all_partitions=False,
            title=None,
            description=None,
            run_config=None,
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
    assert run.asset_selection == {dg.AssetKey(["asset_a"])}

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
    assert backfill.backfill_end_timestamp is not None


# Check run submission at chunk boundary and off of chunk boundary
@pytest.mark.parametrize("num_partitions", [DEFAULT_CHUNK_SIZE * 2, (DEFAULT_CHUNK_SIZE) + 1])
def test_asset_backfill_submit_runs_in_chunks(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    num_partitions: int,
    set_default_chunk_size,
):
    asset_selection = [dg.AssetKey("daily_1"), dg.AssetKey("daily_2")]

    target_partitions = daily_partitions_def.get_partition_keys()[0:num_partitions]
    backfill_id = f"backfill_with_{num_partitions}_partitions"

    asset_graph = workspace_context.create_request_context().asset_graph
    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=asset_graph,
            backfill_id=backfill_id,
            tags={},
            backfill_timestamp=get_current_timestamp(),
            asset_selection=asset_selection,
            partition_names=target_partitions,
            dynamic_partitions_store=instance,
            all_partitions=False,
            title=None,
            description=None,
            run_config=None,
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

    backfill = check.not_none(instance.get_backfill(backfill_id))

    for asset_key in asset_selection:
        assert (
            backfill.get_asset_backfill_data(asset_graph)
            .requested_subset.get_partitions_subset(asset_key, asset_graph)
            .get_partition_keys()
            == target_partitions
        )

    assert instance.get_runs_count() == num_partitions


def test_asset_backfill_mid_iteration_cancel(
    instance: DagsterInstance, workspace_context: WorkspaceProcessContext, set_default_chunk_size
):
    asset_selection = [dg.AssetKey("daily_1"), dg.AssetKey("daily_2")]
    asset_graph = workspace_context.create_request_context().asset_graph

    num_partitions = DEFAULT_CHUNK_SIZE * 2
    target_partitions = daily_partitions_def.get_partition_keys()[0:num_partitions]
    backfill_id = f"backfill_with_{num_partitions}_partitions"

    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id=backfill_id,
        tags={},
        backfill_timestamp=get_current_timestamp(),
        asset_selection=asset_selection,
        partition_names=target_partitions,
        dynamic_partitions_store=instance,
        all_partitions=False,
        title=None,
        description=None,
        run_config=None,
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
        assert instance.get_runs_count() == DEFAULT_CHUNK_SIZE

    # Check that the requested subset only contains runs that were submitted
    updated_backfill = instance.get_backfill(backfill_id)
    assert updated_backfill
    updated_asset_backfill_data = check.not_none(backfill.asset_backfill_data)
    assert all(
        len(partitions_subset) == DEFAULT_CHUNK_SIZE
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

    assert instance.get_runs_count() == DEFAULT_CHUNK_SIZE
    assert instance.get_runs_count(dg.RunsFilter(statuses=IN_PROGRESS_RUN_STATUSES)) == 0


def test_asset_backfill_forcible_mark_as_canceled_during_canceling_iteration(
    instance: DagsterInstance, workspace_context: WorkspaceProcessContext
):
    asset_selection = [dg.AssetKey("daily_1"), dg.AssetKey("daily_2")]
    asset_graph = workspace_context.create_request_context().asset_graph

    backfill_id = "backfill_id"
    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id=backfill_id,
        tags={},
        backfill_timestamp=get_current_timestamp(),
        asset_selection=asset_selection,
        partition_names=["2023-01-01"],
        dynamic_partitions_store=instance,
        all_partitions=False,
        title=None,
        description=None,
        run_config=None,
    ).with_status(BulkActionStatus.CANCELING)
    instance.add_backfill(
        # Add some partitions in a "requested" state to mock that certain partitions are hanging
        backfill.with_asset_backfill_data(
            backfill.asset_backfill_data._replace(  # pyright: ignore[reportOptionalMemberAccess]
                requested_subset=AssetGraphSubset(
                    non_partitioned_asset_keys={dg.AssetKey("daily_1")}
                )
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
    from dagster._core.execution.submit_asset_runs import get_job_execution_data_from_run_request

    asset_selection = [dg.AssetKey("asset_a"), dg.AssetKey("asset_e")]
    asset_graph = workspace_context.create_request_context().asset_graph

    num_partitions = 1
    target_partitions = partitions_a.get_partition_keys()[0:num_partitions]
    backfill_id = "simple_fan_out_backfill"
    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id=backfill_id,
        tags={},
        backfill_timestamp=get_current_timestamp(),
        asset_selection=asset_selection,
        partition_names=target_partitions,
        dynamic_partitions_store=instance,
        all_partitions=False,
        title=None,
        description=None,
        run_config=None,
    )
    instance.add_backfill(backfill)
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED
    assert backfill.failure_count == 0

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
    assert instance.get_runs_count() == 1

    # The following backfill iteration will attempt to submit run requests for asset_e's three partitions.
    # The first call to get_job_execution_data_from_run_request will succeed, but the second call will
    # raise a DagsterUserCodeUnreachableError. Subsequently only the first partition will be successfully
    # submitted.
    counter = 0

    async def raise_code_unreachable_error_on_second_call(*args, **kwargs):
        nonlocal counter
        if counter == 0:
            counter += 1
            return await get_job_execution_data_from_run_request(*args, **kwargs)
        elif counter == 1:
            counter += 1
            raise DagsterUserCodeUnreachableError()
        else:
            # Should not attempt to create a run for the third partition if the second
            # errored with DagsterUserCodeUnreachableError
            raise Exception("Should not reach")

    with mock.patch(
        "dagster._core.execution.submit_asset_runs.get_job_execution_data_from_run_request",
        side_effect=raise_code_unreachable_error_on_second_call,
    ):
        errors = [
            error
            for error in list(
                execute_backfill_iteration(
                    workspace_context, get_default_daemon_logger("BackfillDaemon")
                )
            )
            if error
        ]
        assert len(errors) == 1
        assert (
            "Unable to reach the code server. Backfill will resume once the code server is available"
            in str(errors[0])
        )

    assert instance.get_runs_count() == 2
    updated_backfill = instance.get_backfill(backfill_id)
    assert updated_backfill
    assert (
        updated_backfill.failure_count == 0
    )  # because of the nature of the error, failure count not incremented

    # Runs were still removed off the list of submitting run requests because the error was
    # caught and the backfill data updated
    assert len(updated_backfill.submitting_run_requests) == 2
    assert len(updated_backfill.reserved_run_ids) == 2
    assert updated_backfill.asset_backfill_data
    assert (
        updated_backfill.asset_backfill_data.materialized_subset.num_partitions_and_non_partitioned_assets
        == 1
    )

    # Requested subset still updated since the error was caught and the backfill data updated
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


def test_asset_backfill_first_iteration_code_location_unreachable_error_no_runs_submitted(
    instance: DagsterInstance, workspace_context: WorkspaceProcessContext
):
    # tests that we can recover from unreachable code location error during the first tick when
    # we are requesting the root assets

    asset_selection = [dg.AssetKey("asset_a"), dg.AssetKey("asset_e")]
    asset_graph = workspace_context.create_request_context().asset_graph

    num_partitions = 1
    target_partitions = partitions_a.get_partition_keys()[0:num_partitions]
    backfill_id = "backfill_with_roots"
    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id=backfill_id,
        tags={},
        backfill_timestamp=get_current_timestamp(),
        asset_selection=asset_selection,
        partition_names=target_partitions,
        dynamic_partitions_store=instance,
        all_partitions=False,
        title=None,
        description=None,
        run_config=None,
    )
    instance.add_backfill(backfill)
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    # The following backfill iteration will attempt to submit run requests for asset_a's partition.
    # The call will raise a DagsterUserCodeUnreachableError and no runs will be submitted

    def raise_code_unreachable_error(*args, **kwargs):
        raise DagsterUserCodeUnreachableError()

    with mock.patch(
        "dagster._core.execution.submit_asset_runs.get_job_execution_data_from_run_request",
        side_effect=raise_code_unreachable_error,
    ):
        errors = [
            error
            for error in list(
                execute_backfill_iteration(
                    workspace_context, get_default_daemon_logger("BackfillDaemon")
                )
            )
            if error
        ]
        assert len(errors) == 1
        assert (
            "Unable to reach the code server. Backfill will resume once the code server is available"
            in str(errors[0])
        )

    assert instance.get_runs_count() == 0
    updated_backfill = instance.get_backfill(backfill_id)
    assert updated_backfill
    assert updated_backfill.asset_backfill_data
    assert len(updated_backfill.submitting_run_requests) == 1
    assert (
        updated_backfill.asset_backfill_data.requested_subset.num_partitions_and_non_partitioned_assets
        == 0  # chunk did not finish, so requested_subset was not updated
    )
    assert updated_backfill.asset_backfill_data.requested_runs_for_target_roots

    # Execute backfill iteration again, confirming that the partition for asset_a is requested again
    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )
    # Assert that one run is submitted
    assert instance.get_runs_count() == 1

    updated_backfill = instance.get_backfill(backfill_id)
    assert updated_backfill
    assert updated_backfill.asset_backfill_data
    assert (
        updated_backfill.asset_backfill_data.requested_subset.num_partitions_and_non_partitioned_assets
        == 1
    )


def test_asset_backfill_first_iteration_code_location_unreachable_error_some_runs_submitted(
    instance: DagsterInstance, workspace_context: WorkspaceProcessContext
):
    # tests that we can recover from unreachable code location error during the first tick when
    # we are requesting the root assets
    from dagster._core.execution.submit_asset_runs import get_job_execution_data_from_run_request

    asset_selection = [dg.AssetKey("asset_f"), dg.AssetKey("asset_g")]
    asset_graph = workspace_context.create_request_context().asset_graph

    num_partitions = 2
    target_partitions = partitions_f.get_partition_keys()[0:num_partitions]
    backfill_id = "backfill_with_roots_multiple_partitions"
    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id=backfill_id,
        tags={},
        backfill_timestamp=get_current_timestamp(),
        asset_selection=asset_selection,
        partition_names=target_partitions,
        dynamic_partitions_store=instance,
        all_partitions=False,
        title=None,
        description=None,
        run_config=None,
    )
    instance.add_backfill(backfill)
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    # The following backfill iteration will attempt to submit run requests for asset_f's two partitions.
    # The first call to get_job_execution_data_from_run_request will succeed, but the second call will
    # raise a DagsterUserCodeUnreachableError. Subsequently only the first partition will be successfully
    # submitted.
    counter = 0

    async def raise_code_unreachable_error_on_second_call(*args, **kwargs):
        nonlocal counter
        if counter == 0:
            counter += 1
            return await get_job_execution_data_from_run_request(*args, **kwargs)
        elif counter == 1:
            counter += 1
            raise DagsterUserCodeUnreachableError()
        else:
            # Should not attempt to create a run for the third partition if the second
            # errored with DagsterUserCodeUnreachableError
            raise Exception("Should not reach")

    with mock.patch(
        "dagster._core.execution.submit_asset_runs.get_job_execution_data_from_run_request",
        side_effect=raise_code_unreachable_error_on_second_call,
    ):
        errors = [
            error
            for error in list(
                execute_backfill_iteration(
                    workspace_context, get_default_daemon_logger("BackfillDaemon")
                )
            )
            if error
        ]
        assert len(errors) == 1
        assert (
            "Unable to reach the code server. Backfill will resume once the code server is available"
            in str(errors[0])
        )

    assert instance.get_runs_count() == 1
    updated_backfill = instance.get_backfill(backfill_id)

    assert updated_backfill
    assert updated_backfill.asset_backfill_data

    # error was caught and the submitting run requests and backfill data were updated with
    # what was submitted before the failure
    assert len(updated_backfill.submitting_run_requests or []) == 1
    assert (
        updated_backfill.asset_backfill_data.requested_subset.num_partitions_and_non_partitioned_assets
        == 1
    )
    assert updated_backfill.asset_backfill_data.requested_runs_for_target_roots

    # Execute backfill iteration again, confirming that the remaining partition for asset_f is requested again
    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )
    # Assert that one run is submitted
    assert instance.get_runs_count() == 2

    updated_backfill = instance.get_backfill(backfill_id)
    assert updated_backfill
    assert updated_backfill.asset_backfill_data

    # Chunk finished so requested_subset is now updated
    assert (
        updated_backfill.asset_backfill_data.requested_subset.num_partitions_and_non_partitioned_assets
        == 2
    )
    assert updated_backfill.asset_backfill_data.requested_runs_for_target_roots


def test_backfill_warns_when_runs_completed_but_partitions_marked_as_in_progress(
    instance: DagsterInstance, workspace_context: WorkspaceProcessContext, caplog
):
    asset_selection = [dg.AssetKey("daily_1"), dg.AssetKey("daily_2")]
    asset_graph = workspace_context.create_request_context().asset_graph

    target_partitions = ["2023-01-01"]
    backfill_id = "backfill_with_hanging_partitions"
    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id=backfill_id,
        tags={},
        backfill_timestamp=get_current_timestamp(),
        asset_selection=asset_selection,
        partition_names=target_partitions,
        dynamic_partitions_store=instance,
        all_partitions=False,
        title=None,
        description=None,
        run_config=None,
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

    assert len(errors) == 0

    updated_backfill = check.not_none(instance.get_backfill(backfill_id))
    assert updated_backfill.status == BulkActionStatus.CANCELED

    logs = caplog.text

    assert (
        "All runs have completed, but not all requested partitions have been marked as materialized or failed"
    ) in logs


# Job must have a partitions definition with a-b-c-d partitions
def _get_abcd_job_backfill(remote_repo: RemoteRepository, job_name: str) -> PartitionBackfill:
    partition_set = remote_repo.get_partition_set(f"{job_name}_partition_set")
    return PartitionBackfill(
        backfill_id="simple",
        partition_set_origin=partition_set.get_remote_origin(),
        status=BulkActionStatus.REQUESTED,
        partition_names=["a", "b", "c", "d"],
        from_failure=False,
        reexecution_steps=None,
        tags=None,
        backfill_timestamp=get_current_timestamp(),
    )


def test_asset_job_backfill_single_run(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
):
    backfill = _get_abcd_job_backfill(remote_repo, "bp_single_run_asset_job")
    assert instance.get_runs_count() == 0
    instance.add_backfill(backfill)
    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))

    assert instance.get_runs_count() == 1
    run = instance.get_runs()[0]
    assert run.tags[BACKFILL_ID_TAG] == "simple"
    assert run.tags[ASSET_PARTITION_RANGE_START_TAG] == "a"
    assert run.tags[ASSET_PARTITION_RANGE_END_TAG] == "d"
    assert run.tags["alpha"] == "beta"


def test_asset_job_backfill_single_run_multiple_iterations(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
):
    """Tests that job backfills correctly find existing runs for partitions in the backfill and don't
    relaunch those partitions. This is a regression test for a bug where the backfill would relaunch
    runs for BackfillPolicy.single_run asset jobs since we were incorrectly determining which partitions
    had already been launched.
    """
    backfill = _get_abcd_job_backfill(remote_repo, "bp_single_run_asset_job")
    assert instance.get_runs_count() == 0
    instance.add_backfill(backfill)

    # seed an in progress run. The mimics the backfill daemon having already launched the run for these
    # partitions
    fake_run = create_run_for_test(
        instance=instance,
        status=DagsterRunStatus.STARTED,
        tags={
            **DagsterRun.tags_for_backfill_id("simple"),
            ASSET_PARTITION_RANGE_START_TAG: "a",
            ASSET_PARTITION_RANGE_END_TAG: "d",
        },
    )

    assert instance.get_runs_count() == 1
    run = instance.get_runs()[0]
    assert run.tags[BACKFILL_ID_TAG] == "simple"
    assert run.tags[ASSET_PARTITION_RANGE_START_TAG] == "a"
    assert run.tags[ASSET_PARTITION_RANGE_END_TAG] == "d"

    for _ in range(3):  # simulate the daemon ticking a few times
        list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
        # backfill should not create any new runs
        assert instance.get_runs_count() == 1

    # manually update the run to be in a finished state, backfill should be marked complete on next iteration
    instance.delete_run(fake_run.run_id)
    create_run_for_test(
        instance=instance,
        status=DagsterRunStatus.SUCCESS,
        tags={
            **DagsterRun.tags_for_backfill_id("simple"),
            ASSET_PARTITION_RANGE_START_TAG: "a",
            ASSET_PARTITION_RANGE_END_TAG: "d",
        },
    )

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))

    assert instance.get_runs_count() == 1
    backfill = instance.get_backfill("simple")
    assert backfill
    assert backfill.status == BulkActionStatus.COMPLETED_SUCCESS
    assert backfill.backfill_end_timestamp is not None


def test_asset_job_backfill_multi_run(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
):
    backfill = _get_abcd_job_backfill(remote_repo, "bp_multi_run_asset_job")
    assert instance.get_runs_count() == 0
    instance.add_backfill(backfill)
    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))

    assert instance.get_runs_count() == 2
    run_1, run_2 = instance.get_runs()

    assert run_1.tags[BACKFILL_ID_TAG] == "simple"
    assert run_1.tags[ASSET_PARTITION_RANGE_START_TAG] == "c"
    assert run_1.tags[ASSET_PARTITION_RANGE_END_TAG] == "d"

    assert run_2.tags[BACKFILL_ID_TAG] == "simple"
    assert run_2.tags[ASSET_PARTITION_RANGE_START_TAG] == "a"
    assert run_2.tags[ASSET_PARTITION_RANGE_END_TAG] == "b"


def test_asset_job_backfill_default(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
):
    backfill = _get_abcd_job_backfill(remote_repo, "bp_none_asset_job")
    assert instance.get_runs_count() == 0
    instance.add_backfill(backfill)
    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))

    assert instance.get_runs_count() == 4
    run_1, run_2, run_3, run_4 = instance.get_runs()

    assert run_1.tags[BACKFILL_ID_TAG] == "simple"
    assert run_1.tags[PARTITION_NAME_TAG] == "d"
    assert run_2.tags[BACKFILL_ID_TAG] == "simple"
    assert run_2.tags[PARTITION_NAME_TAG] == "c"
    assert run_3.tags[BACKFILL_ID_TAG] == "simple"
    assert run_3.tags[PARTITION_NAME_TAG] == "b"
    assert run_4.tags[BACKFILL_ID_TAG] == "simple"
    assert run_4.tags[PARTITION_NAME_TAG] == "a"


def test_asset_backfill_with_single_run_backfill_policy(
    instance: DagsterInstance, workspace_context: WorkspaceProcessContext
):
    partitions = ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"]
    asset_graph = workspace_context.create_request_context().asset_graph

    backfill_id = "asset_backfill_with_backfill_policy"
    backfill = PartitionBackfill.from_partitions_by_assets(
        backfill_id=backfill_id,
        asset_graph=asset_graph,
        backfill_timestamp=get_current_timestamp(),
        tags={},
        dynamic_partitions_store=instance,
        partitions_by_assets=[
            PartitionsByAssetSelector(
                asset_key=asset_with_single_run_backfill_policy.key,
                partitions=PartitionsSelector(
                    [PartitionRangeSelector(partitions[0], partitions[-1])]
                ),
            )
        ],
        title=None,
        description=None,
        run_config=None,
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


def test_asset_backfill_from_asset_graph_subset_with_single_run_backfill_policy(
    instance: DagsterInstance, workspace_context: WorkspaceProcessContext
):
    partitions = ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"]

    backfill_id = "asset_backfill_from_asset_graph_subset_with_backfill_policy"
    asset_graph_subset = AssetGraphSubset.from_asset_partition_set(
        asset_partitions_set={
            AssetKeyPartitionKey(asset_with_single_run_backfill_policy.key, pk) for pk in partitions
        },
        asset_graph=workspace_context.create_request_context().asset_graph,
    )
    backfill = PartitionBackfill.from_asset_graph_subset(
        backfill_id=backfill_id,
        asset_graph_subset=asset_graph_subset,
        backfill_timestamp=get_current_timestamp(),
        tags={},
        dynamic_partitions_store=instance,
        title=None,
        description=None,
        run_config=None,
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
        backfill_timestamp=get_current_timestamp(),
        asset_selection=[asset_with_multi_run_backfill_policy.key],
        partition_names=partitions,
        dynamic_partitions_store=instance,
        all_partitions=False,
        title=None,
        description=None,
        run_config=None,
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


def test_complex_asset_with_backfill_policy(
    instance: DagsterInstance, workspace_context: WorkspaceProcessContext
):
    # repro of bug
    partitions = ["2023-01-01", "2023-01-02", "2023-01-03"]
    asset_graph = workspace_context.create_request_context().asset_graph

    backfill_id = "complex_asset_with_backfills"
    backfill = PartitionBackfill.from_partitions_by_assets(
        backfill_id=backfill_id,
        asset_graph=asset_graph,
        backfill_timestamp=get_current_timestamp(),
        tags={},
        dynamic_partitions_store=instance,
        partitions_by_assets=[
            PartitionsByAssetSelector(
                asset_key=asset_with_single_run_backfill_policy.key,
                partitions=PartitionsSelector(
                    [PartitionRangeSelector(partitions[0], partitions[-1])]
                ),
            ),
            PartitionsByAssetSelector(
                asset_key=complex_asset_with_backfill_policy.key,
                partitions=PartitionsSelector(
                    [PartitionRangeSelector(partitions[0], partitions[-1])]
                ),
            ),
        ],
        title=None,
        description=None,
        run_config=None,
    )
    instance.add_backfill(backfill)

    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED
    assert backfill.asset_selection == [
        asset_with_single_run_backfill_policy.key,
        complex_asset_with_backfill_policy.key,
    ]

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
    assert backfill.status == BulkActionStatus.REQUESTED
    assert set(
        check.not_none(backfill.asset_backfill_data).requested_subset.iterate_asset_partitions()
    ) == {
        AssetKeyPartitionKey(asset_with_single_run_backfill_policy.key, partition)
        for partition in partitions
    }

    # 1 run for the full range of the upstream partition
    assert instance.get_runs_count() == 1
    wait_for_all_runs_to_start(instance, timeout=30)
    wait_for_all_runs_to_finish(instance, timeout=30)

    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )

    # 1 run for the full range of the downstream partition

    assert instance.get_runs_count() == 2
    wait_for_all_runs_to_start(instance, timeout=30)
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
    assert backfill.status == BulkActionStatus.COMPLETED_SUCCESS
    assert backfill.backfill_end_timestamp is not None


def test_error_code_location(
    caplog, instance, workspace_context, unloadable_location_workspace_context
):
    asset_selection = [dg.AssetKey("asset_a")]
    partition_keys = partitions_a.get_partition_keys()
    backfill_id = "dummy_backfill"

    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id=backfill_id,
            tags={},
            backfill_timestamp=get_current_timestamp(),
            asset_selection=asset_selection,
            partition_names=partition_keys,
            dynamic_partitions_store=instance,
            all_partitions=False,
            title=None,
            description=None,
            run_config=None,
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
        " that's failing to load" in errors[0].message  # pyright: ignore[reportOptionalMemberAccess]
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
    asset_selection = [dg.AssetKey("time_partitions_def_changes")]
    partition_keys = ["2023-01-01"]
    backfill_id = "dummy_backfill"
    asset_graph = (
        partitions_defs_changes_location_1_workspace_context.create_request_context().asset_graph
    )

    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id=backfill_id,
        tags={},
        backfill_timestamp=get_current_timestamp(),
        asset_selection=asset_selection,
        partition_names=partition_keys,
        dynamic_partitions_store=instance,
        all_partitions=False,
        title=None,
        description=None,
        run_config=None,
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
    if backcompat_serialization:
        assert ("partitions definition has changed") in error_msg or (
            "partitions definition for asset AssetKey(['time_partitions_def_changes']) has changed"
        ) in error_msg
    else:
        # doesn't have deser issues but does detect that the partition was removed
        assert ("The following partitions were removed: ['2023-01-01']") in error_msg


@pytest.mark.parametrize("backcompat_serialization", [True, False])
def test_raise_error_on_partitions_defs_removed(
    caplog,
    instance,
    partitions_defs_changes_location_1_workspace_context,
    partitions_defs_changes_location_2_workspace_context,
    backcompat_serialization: bool,
):
    asset_selection = [dg.AssetKey("partitions_def_removed")]
    partition_keys = ["2023-01-01"]
    backfill_id = "dummy_backfill"
    asset_graph = (
        partitions_defs_changes_location_1_workspace_context.create_request_context().asset_graph
    )

    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id=backfill_id,
        tags={},
        backfill_timestamp=get_current_timestamp(),
        asset_selection=asset_selection,
        partition_names=partition_keys,
        dynamic_partitions_store=instance,
        all_partitions=False,
        title=None,
        description=None,
        run_config=None,
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
    asset_selection = [dg.AssetKey("static_partition_removed")]
    partition_keys = ["a"]
    asset_graph = (
        partitions_defs_changes_location_1_workspace_context.create_request_context().asset_graph
    )

    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id="dummy_backfill",
        tags={},
        backfill_timestamp=get_current_timestamp(),
        asset_selection=asset_selection,
        partition_names=partition_keys,
        dynamic_partitions_store=instance,
        all_partitions=False,
        title=None,
        description=None,
        run_config=None,
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
        backfill_timestamp=get_current_timestamp(),
        asset_selection=asset_selection,
        partition_names=["c"],
        dynamic_partitions_store=instance,
        all_partitions=False,
        title=None,
        description=None,
        run_config=None,
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
    asset_selection = [dg.AssetKey("time_partitions_def_changes")]
    partition_keys = ["2023-01-01"]
    backfill_id = "dummy_backfill"
    asset_graph = (
        partitions_defs_changes_location_1_workspace_context.create_request_context().asset_graph
    )

    backfill = PartitionBackfill.from_asset_partitions(
        asset_graph=asset_graph,
        backfill_id=backfill_id,
        tags={},
        backfill_timestamp=get_current_timestamp(),
        asset_selection=asset_selection,
        partition_names=partition_keys,
        dynamic_partitions_store=instance,
        all_partitions=False,
        title=None,
        description=None,
        run_config=None,
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
        assert (
            "Targeted partitions for asset AssetKey(['time_partitions_def_changes']) have been removed since this backfill was stored. The following partitions were removed: ['2023-01-01']"
        ) in error_msg
    assert ("The following partitions were removed: ['2023-01-01']") in error_msg


def test_asset_backfill_logging(caplog, instance, workspace_context):
    asset_selection = [
        dg.AssetKey("asset_a"),
        dg.AssetKey("asset_b"),
        dg.AssetKey("asset_c"),
    ]

    partition_keys = partitions_a.get_partition_keys()
    backfill_id = "backfill_with_multiple_assets_selected"

    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id=backfill_id,
            tags={"custom_tag_key": "custom_tag_value"},
            backfill_timestamp=get_current_timestamp(),
            asset_selection=asset_selection,
            partition_names=partition_keys,
            dynamic_partitions_store=instance,
            all_partitions=False,
            title=None,
            description=None,
            run_config=None,
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
    assert (
        """Asset partitions to request:
- asset_a: {foo_a}"""
        in logs
    )


def test_asset_backfill_failure_logging(caplog, instance, workspace_context):
    asset_selection = [
        dg.AssetKey("always_fails"),
    ]

    partition_keys = static_partitions.get_partition_keys()
    backfill_id = "backfill_with_failure"

    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id=backfill_id,
            tags={"custom_tag_key": "custom_tag_value"},
            backfill_timestamp=get_current_timestamp(),
            asset_selection=asset_selection,
            partition_names=partition_keys,
            dynamic_partitions_store=instance,
            all_partitions=False,
            title=None,
            description=None,
            run_config=None,
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

    assert (
        """Overall backfill status:
**Materialized assets:**
None
**Failed assets and their downstream assets:**
None
**Assets requested or in progress:**
- always_fails:"""
        in logs
    )

    wait_for_all_runs_to_finish(instance)

    caplog.clear()

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
    assert backfill.status == BulkActionStatus.COMPLETED_FAILED

    logs = caplog.text
    assert (
        """Overall backfill status:
**Materialized assets:**
None
**Failed assets and their downstream assets:**
- always_fails:"""
    ) in logs

    assert (
        """**Assets requested or in progress:**
None"""
        in logs
    )


def test_backfill_with_title_and_description(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
):
    asset_selection = [
        dg.AssetKey("asset_a"),
        dg.AssetKey("asset_b"),
    ]

    partition_keys = partitions_a.get_partition_keys()

    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id="backfill_with_title",
            tags={"custom_tag_key": "custom_tag_value"},
            backfill_timestamp=get_current_timestamp(),
            asset_selection=asset_selection,
            partition_names=partition_keys,
            dynamic_partitions_store=instance,
            all_partitions=False,
            title="Custom title",
            description="this backfill is fancy",
            run_config=None,
        )
    )
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill("backfill_with_title")
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED
    assert backfill.title == "Custom title"
    assert backfill.description == "this backfill is fancy"

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
    assert backfill.title == "Custom title"
    assert backfill.description == "this backfill is fancy"

    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )
    assert instance.get_runs_count() == 2
    wait_for_all_runs_to_start(instance, timeout=30)
    wait_for_all_runs_to_finish(instance, timeout=30)
    assert backfill.title == "Custom title"
    assert backfill.description == "this backfill is fancy"

    runs = instance.get_runs()

    assert all([run.status == DagsterRunStatus.SUCCESS] for run in runs)


def test_asset_backfill_with_run_config_simple(
    instance: DagsterInstance, run_config_assets_workspace_context: WorkspaceProcessContext
):
    hourly_partitions_def = dg.HourlyPartitionsDefinition("2023-10-01-00:00")
    daily_partitions_def = dg.DailyPartitionsDefinition("2023-10-01")
    hourly_subset = hourly_partitions_def.empty_subset().with_partition_key_range(
        hourly_partitions_def, dg.PartitionKeyRange("2023-11-01-00:00", "2023-11-01-03:00")
    )
    daily_subset = daily_partitions_def.empty_subset().with_partition_key_range(
        daily_partitions_def, dg.PartitionKeyRange("2023-11-01", "2023-11-01")
    )

    run_config = {
        "ops": {
            "hourly": {"config": {"a": 0}},
            "daily": {"config": {"b": "b"}},
        },
    }
    instance.add_backfill(
        PartitionBackfill.from_asset_graph_subset(
            backfill_id="run_config_backfill",
            backfill_timestamp=get_current_timestamp(),
            tags={},
            asset_graph_subset=AssetGraphSubset(
                partitions_subsets_by_asset_key={
                    AssetKey("hourly"): hourly_subset,
                    AssetKey("daily"): daily_subset,
                }
            ),
            dynamic_partitions_store=instance,
            title="Custom title",
            description="this backfill is fancy",
            run_config=run_config,
        )
    )
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill("run_config_backfill")
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED
    assert backfill.run_config == run_config

    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                run_config_assets_workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )
    assert instance.get_runs_count() == 4
    wait_for_all_runs_to_start(instance, timeout=30)
    wait_for_all_runs_to_finish(instance, timeout=30)

    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                run_config_assets_workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )
    assert instance.get_runs_count() == 5
    wait_for_all_runs_to_start(instance, timeout=30)
    wait_for_all_runs_to_finish(instance, timeout=30)

    runs = instance.get_runs()

    assert all([run.status == DagsterRunStatus.SUCCESS] for run in runs)


def test_asset_backfill_with_run_config_complex(
    instance: DagsterInstance, run_config_assets_workspace_context: WorkspaceProcessContext
):
    daily_partitions_def = dg.DailyPartitionsDefinition("2023-10-01")
    daily_partitions_def_2 = dg.DailyPartitionsDefinition("2023-10-02")
    daily_subset = daily_partitions_def.empty_subset().with_partition_key_range(
        daily_partitions_def, dg.PartitionKeyRange("2023-11-01", "2023-11-04")
    )
    daily_subset_2 = daily_partitions_def_2.empty_subset().with_partition_key_range(
        daily_partitions_def_2, dg.PartitionKeyRange("2023-11-01", "2023-11-04")
    )

    run_config = {
        "ops": {
            "c_and_d_asset": {"config": {"a": 0}},
        },
    }
    instance.add_backfill(
        PartitionBackfill.from_asset_graph_subset(
            backfill_id="run_config_backfill",
            backfill_timestamp=get_current_timestamp(),
            tags={},
            asset_graph_subset=AssetGraphSubset(
                partitions_subsets_by_asset_key={
                    AssetKey("C"): daily_subset,
                    AssetKey("middle"): daily_subset_2,
                    AssetKey("D"): daily_subset,
                }
            ),
            dynamic_partitions_store=instance,
            title="Custom title",
            description="this backfill is fancy",
            run_config=run_config,
        )
    )
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill("run_config_backfill")
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED
    assert backfill.run_config == run_config

    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                run_config_assets_workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )
    assert instance.get_runs_count() == 4
    wait_for_all_runs_to_start(instance, timeout=30)
    wait_for_all_runs_to_finish(instance, timeout=30)

    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                run_config_assets_workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )
    assert instance.get_runs_count() == 8
    wait_for_all_runs_to_start(instance, timeout=30)
    wait_for_all_runs_to_finish(instance, timeout=30)

    assert all(
        not error
        for error in list(
            execute_backfill_iteration(
                run_config_assets_workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    )
    assert instance.get_runs_count() == 12
    wait_for_all_runs_to_start(instance, timeout=30)
    wait_for_all_runs_to_finish(instance, timeout=30)

    runs = instance.get_runs()

    assert all([run.status == DagsterRunStatus.SUCCESS] for run in runs)
    assert all([run.run_config == run_config] for run in runs)


def test_job_backfill_with_run_config(
    instance: DagsterInstance,
    run_config_assets_workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
):
    code_location = cast(
        "CodeLocation",
        next(
            iter(
                run_config_assets_workspace_context.create_request_context()
                .get_code_location_entries()
                .values()
            )
        ).code_location,
    )
    run_config = {
        "ops": {
            "daily": {"config": {"b": "b"}},
            "other_daily": {"config": {"b": "b"}},
        },
    }
    partition_set = code_location.get_repository("__repository__").get_partition_set(
        "daily_job_partition_set"
    )
    instance.add_backfill(
        PartitionBackfill(
            backfill_id="run_config_backfill",
            partition_set_origin=partition_set.get_remote_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=["2023-11-01", "2023-11-02"],
            from_failure=False,
            reexecution_steps=None,
            tags=None,
            backfill_timestamp=get_current_timestamp(),
            run_config=run_config,
        )
    )
    assert instance.get_runs_count() == 0

    list(
        execute_backfill_iteration(
            run_config_assets_workspace_context, get_default_daemon_logger("BackfillDaemon")
        )
    )

    assert instance.get_runs_count() == 2
    runs = instance.get_runs()
    two, one = runs

    assert two.run_config == run_config
    assert one.run_config == run_config


def test_old_dynamic_partitions_job_backfill(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
):
    backfill = _get_abcd_job_backfill(remote_repo, "old_dynamic_partitions_job")
    assert instance.get_runs_count() == 0
    instance.add_backfill(backfill)
    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))

    assert instance.get_runs_count() == 4


@pytest.fixture
def instance_with_backfill_log_storage_enabled(instance):
    def override_backfill_storage_setting(self):
        return True

    orig_backfill_storage_setting = instance.backfill_log_storage_enabled

    try:
        instance.backfill_log_storage_enabled = override_backfill_storage_setting.__get__(
            instance, dg.DagsterInstance
        )
        yield instance
    finally:
        instance.backfill_log_storage_enabled = orig_backfill_storage_setting


def test_asset_backfill_logs(
    instance_with_backfill_log_storage_enabled: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
):
    instance = instance_with_backfill_log_storage_enabled

    partition_keys = static_partitions.get_partition_keys()
    asset_selection = [dg.AssetKey("foo"), dg.AssetKey("a1"), dg.AssetKey("bar")]
    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id="backfill_with_asset_selection",
            tags={"custom_tag_key": "custom_tag_value"},
            backfill_timestamp=get_current_timestamp(),
            asset_selection=asset_selection,
            partition_names=partition_keys,
            dynamic_partitions_store=instance,
            all_partitions=False,
            title=None,
            description=None,
            run_config=None,
        )
    )
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill("backfill_with_asset_selection")
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    assert instance.get_runs_count() == 3
    wait_for_all_runs_to_start(instance, timeout=15)
    assert instance.get_runs_count() == 3
    wait_for_all_runs_to_finish(instance, timeout=15)

    os.environ["DAGSTER_CAPTURED_LOG_CHUNK_SIZE"] = "20"

    cm = instance.compute_log_manager

    logs, cursor = cm.read_log_lines_for_log_key_prefix(
        ["backfill", backfill.backfill_id], cursor=None, io_type=ComputeIOType.STDERR
    )
    assert cursor is not None
    assert logs
    for log_line in logs:
        if not log_line:
            continue
        try:
            record_dict = seven.json.loads(log_line)
        except json.JSONDecodeError:
            continue
        assert record_dict.get("msg")

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    backfill = instance.get_backfill("backfill_with_asset_selection")
    assert backfill
    assert backfill.status == BulkActionStatus.COMPLETED_SUCCESS
    assert backfill.backfill_end_timestamp is not None

    # set num_lines high so we know we get all of the remaining logs
    os.environ["DAGSTER_CAPTURED_LOG_CHUNK_SIZE"] = "100"
    logs, cursor = cm.read_log_lines_for_log_key_prefix(
        ["backfill", backfill.backfill_id], cursor=cursor.to_string(), io_type=ComputeIOType.STDERR
    )

    assert cursor is not None
    assert not cursor.has_more_now
    for log_line in logs:
        if not log_line:
            continue
        try:
            record_dict = seven.json.loads(log_line)
        except json.JSONDecodeError:
            continue
        assert record_dict.get("msg")


@pytest.mark.parametrize("parallel", [True, False])
def test_asset_backfill_from_asset_graph_subset(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
    parallel: bool,
):
    del remote_repo

    partition_keys = static_partitions.get_partition_keys()
    asset_selection = [dg.AssetKey("foo"), dg.AssetKey("a1"), dg.AssetKey("bar")]

    asset_graph_subset = AssetGraphSubset.from_asset_partition_set(
        asset_partitions_set={
            AssetKeyPartitionKey(ak, pk) for ak in asset_selection for pk in partition_keys
        },
        asset_graph=workspace_context.create_request_context().asset_graph,
    )
    instance.add_backfill(
        PartitionBackfill.from_asset_graph_subset(
            backfill_id="backfill_from_asset_graph_subset",
            tags={"custom_tag_key": "custom_tag_value"},
            backfill_timestamp=get_current_timestamp(),
            dynamic_partitions_store=instance,
            title=None,
            description=None,
            asset_graph_subset=asset_graph_subset,
            run_config=None,
        )
    )
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill("backfill_from_asset_graph_subset")
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    if parallel:
        backfill_daemon_futures = {}
        list(
            execute_backfill_iteration(
                workspace_context,
                get_default_daemon_logger("BackfillDaemon"),
                threadpool_executor=ThreadPoolExecutor(2),
                backfill_futures=backfill_daemon_futures,
            )
        )

        wait_for_futures(backfill_daemon_futures)
    else:
        list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    assert instance.get_runs_count() == 3
    wait_for_all_runs_to_start(instance, timeout=30)
    assert instance.get_runs_count() == 3
    wait_for_all_runs_to_finish(instance, timeout=30)

    assert instance.get_runs_count() == 3
    runs = reversed(list(instance.get_runs()))
    for run in runs:
        assert run.tags[BACKFILL_ID_TAG] == "backfill_from_asset_graph_subset"
        assert run.tags["custom_tag_key"] == "custom_tag_value"
        assert step_succeeded(instance, run, "foo")
        assert step_succeeded(instance, run, "reusable")
        assert step_succeeded(instance, run, "bar")

    if parallel:
        backfill_daemon_futures = {}
        list(
            execute_backfill_iteration(
                workspace_context,
                get_default_daemon_logger("BackfillDaemon"),
                threadpool_executor=ThreadPoolExecutor(2),
                backfill_futures=backfill_daemon_futures,
            )
        )

        wait_for_futures(backfill_daemon_futures)
    else:
        list(
            execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
    backfill = instance.get_backfill("backfill_from_asset_graph_subset")
    assert backfill
    assert backfill.status == BulkActionStatus.COMPLETED_SUCCESS
    assert backfill.backfill_end_timestamp is not None


def test_asset_backfill_from_asset_graph_subset_with_static_and_time_partitions(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
):
    del remote_repo

    static_partition_keys = static_partitions.get_partition_keys()
    static_asset_selection = [dg.AssetKey("foo"), dg.AssetKey("a1"), dg.AssetKey("bar")]
    static_asset_partition_set = {
        AssetKeyPartitionKey(ak, pk)
        for ak in static_asset_selection
        for pk in static_partition_keys
    }

    time_asset_selection = [dg.AssetKey("daily_1"), dg.AssetKey("daily_2")]
    time_target_partitions = daily_partitions_def.get_partition_keys()[0:5]
    time_asset_partition_set = {
        AssetKeyPartitionKey(ak, pk) for ak in time_asset_selection for pk in time_target_partitions
    }

    asset_graph_subset = AssetGraphSubset.from_asset_partition_set(
        asset_partitions_set=static_asset_partition_set | time_asset_partition_set,
        asset_graph=workspace_context.create_request_context().asset_graph,
    )
    instance.add_backfill(
        PartitionBackfill.from_asset_graph_subset(
            backfill_id="backfill_from_asset_graph_subset_with_static_and_time_partitions",
            tags={"custom_tag_key": "custom_tag_value"},
            backfill_timestamp=get_current_timestamp(),
            dynamic_partitions_store=instance,
            title=None,
            description=None,
            asset_graph_subset=asset_graph_subset,
            run_config=None,
        )
    )
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(
        "backfill_from_asset_graph_subset_with_static_and_time_partitions"
    )
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    assert instance.get_runs_count() == 8
    wait_for_all_runs_to_start(instance, timeout=30)
    assert instance.get_runs_count() == 8
    wait_for_all_runs_to_finish(instance, timeout=30)

    assert instance.get_runs_count() == 8
    runs = reversed(list(instance.get_runs()))
    for run in runs:
        assert (
            run.tags[BACKFILL_ID_TAG]
            == "backfill_from_asset_graph_subset_with_static_and_time_partitions"
        )
        assert run.tags["custom_tag_key"] == "custom_tag_value"

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    backfill = instance.get_backfill(
        "backfill_from_asset_graph_subset_with_static_and_time_partitions"
    )
    assert backfill
    assert backfill.status == BulkActionStatus.COMPLETED_SUCCESS
    assert backfill.backfill_end_timestamp is not None


def test_asset_backfill_not_complete_until_retries_complete(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
):
    del remote_repo
    backfill_id = "run_retries_backfill"
    partition_keys = static_partitions.get_partition_keys()
    asset_selection = [dg.AssetKey("foo"), dg.AssetKey("a1"), dg.AssetKey("bar")]
    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id=backfill_id,
            tags={"custom_tag_key": "custom_tag_value"},
            backfill_timestamp=get_current_timestamp(),
            asset_selection=asset_selection,
            partition_names=partition_keys,
            dynamic_partitions_store=instance,
            all_partitions=False,
            title=None,
            description=None,
            run_config=None,
        )
    )
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
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
        assert run.tags[BACKFILL_ID_TAG] == backfill_id
        assert run.tags["custom_tag_key"] == "custom_tag_value"
        assert step_succeeded(instance, run, "foo")
        assert step_succeeded(instance, run, "reusable")
        assert step_succeeded(instance, run, "bar")

    # simulate a retry of a run
    run_to_retry = instance.get_runs()[0]
    retried_run = create_run_for_test(
        instance=instance,
        job_name=run_to_retry.job_name,
        tags=run_to_retry.tags,
        root_run_id=run_to_retry.run_id,
        parent_run_id=run_to_retry.run_id,
    )

    # since there is a run in progress, the backfill should not be marked as complete, even though
    # all targeted asset partitions have a completed state
    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.asset_backfill_data
    assert backfill.asset_backfill_data.all_targeted_partitions_have_materialization_status()
    assert backfill.status == BulkActionStatus.REQUESTED

    # manually mark the run as successful to show that the backfill will be marked as complete
    # since there are no in progress runs
    instance.handle_new_event(
        dg.EventLogEntry(
            error_info=None,
            level="debug",
            user_message="",
            run_id=retried_run.run_id,
            timestamp=time.time(),
            dagster_event=dg.DagsterEvent(
                event_type_value=DagsterEventType.RUN_SUCCESS.value,
                job_name=retried_run.job_name,
            ),
        )
    )

    retried_run = instance.get_runs(filters=dg.RunsFilter(run_ids=[retried_run.run_id]))[0]
    assert retried_run.status == DagsterRunStatus.SUCCESS

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.COMPLETED_SUCCESS
    assert backfill.backfill_end_timestamp is not None


def test_asset_backfill_not_complete_if_automatic_retry_could_happen(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
):
    del remote_repo
    backfill_id = "run_retries_backfill"
    partition_keys = static_partitions.get_partition_keys()
    asset_selection = [dg.AssetKey("foo"), dg.AssetKey("pass_on_retry")]
    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id=backfill_id,
            tags={"custom_tag_key": "custom_tag_value", MAX_RETRIES_TAG: "2"},
            backfill_timestamp=get_current_timestamp(),
            asset_selection=asset_selection,
            partition_names=partition_keys,
            dynamic_partitions_store=instance,
            all_partitions=False,
            title=None,
            description=None,
            run_config=None,
        )
    )
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
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
        assert run.tags[BACKFILL_ID_TAG] == backfill_id
        assert run.tags["custom_tag_key"] == "custom_tag_value"
        assert step_succeeded(instance, run, "foo")
        assert step_failed(instance, run, "pass_on_retry")

    # since the failed runs should have automatic retries launched for them, the backfill should not
    # be considered complete, even though the targeted asset partitions have a completed state
    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.asset_backfill_data
    assert backfill.asset_backfill_data.all_targeted_partitions_have_materialization_status()
    assert backfill.status == BulkActionStatus.REQUESTED

    # automatic retries wont get automatically run in test environment, so we run the function manually
    runs = instance.get_run_records()
    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_process_context=workspace_context,
            run_records=runs,
            logger=logger,
        )
    )
    wait_for_all_runs_to_finish(instance, timeout=30)
    assert instance.get_runs_count() == 6

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.COMPLETED_SUCCESS
    assert backfill.backfill_end_timestamp is not None


def test_asset_backfill_fails_if_retries_fail(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
):
    del remote_repo
    backfill_id = "run_retries_backfill"
    partition_keys = static_partitions.get_partition_keys()
    asset_selection = [
        dg.AssetKey("foo"),
        dg.AssetKey("pass_on_retry"),
        dg.AssetKey("always_fails"),
    ]
    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id=backfill_id,
            tags={"custom_tag_key": "custom_tag_value", MAX_RETRIES_TAG: "2"},
            backfill_timestamp=get_current_timestamp(),
            asset_selection=asset_selection,
            partition_names=partition_keys,
            dynamic_partitions_store=instance,
            all_partitions=False,
            title=None,
            description=None,
            run_config=None,
        )
    )
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
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
        assert run.tags[BACKFILL_ID_TAG] == backfill_id
        assert run.tags["custom_tag_key"] == "custom_tag_value"
        assert step_succeeded(instance, run, "foo")
        assert step_failed(instance, run, "pass_on_retry")

    # since the failed runs should have automatic retries launched for them, the backfill should not
    # be considered complete, even though the targeted asset partitions have a completed state
    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.asset_backfill_data
    assert backfill.asset_backfill_data.all_targeted_partitions_have_materialization_status()
    assert backfill.status == BulkActionStatus.REQUESTED

    runs = instance.get_run_records()
    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_process_context=workspace_context,
            run_records=runs,
            logger=logger,
        )
    )
    wait_for_all_runs_to_finish(instance, timeout=30)
    assert instance.get_runs_count() == 6

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    # retry limit hasn't been hit, so backfill still in progress
    assert backfill.status == BulkActionStatus.REQUESTED

    runs = instance.get_run_records()
    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_process_context=workspace_context,
            run_records=runs,
            logger=logger,
        )
    )
    wait_for_all_runs_to_finish(instance, timeout=30)
    assert instance.get_runs_count() == 9

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.COMPLETED_FAILED
    assert backfill.backfill_end_timestamp is not None


def test_asset_backfill_retries_make_downstreams_runnable(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
):
    del remote_repo
    backfill_id = "run_retries_backfill_with_downstream"
    partition_keys = partitions_a.get_partition_keys()
    asset_selection = [
        dg.AssetKey("fails_once_asset_a"),
        dg.AssetKey("downstream_of_fails_once_asset_b"),
        dg.AssetKey("downstream_of_fails_once_asset_c"),
    ]
    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id=backfill_id,
            tags={"custom_tag_key": "custom_tag_value", MAX_RETRIES_TAG: "2"},
            backfill_timestamp=get_current_timestamp(),
            asset_selection=asset_selection,
            partition_names=partition_keys,
            dynamic_partitions_store=instance,
            all_partitions=False,
            title=None,
            description=None,
            run_config=None,
        )
    )
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    assert instance.get_runs_count() == 1
    wait_for_all_runs_to_start(instance, timeout=30)
    assert instance.get_runs_count() == 1
    wait_for_all_runs_to_finish(instance, timeout=30)

    assert instance.get_runs_count() == 1
    runs = reversed(list(instance.get_runs()))
    for run in runs:
        assert run.tags[BACKFILL_ID_TAG] == backfill_id
        assert step_failed(instance, run, "fails_once_asset_a")

    # if the backfill daemon runs again, we will see that the downstreams are in the failed and downstream subset
    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    assert instance.get_runs_count() == 1
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.asset_backfill_data
    assert (
        backfill.asset_backfill_data.materialized_subset.num_partitions_and_non_partitioned_assets
        == 0
    )
    assert (
        backfill.asset_backfill_data.failed_and_downstream_subset.num_partitions_and_non_partitioned_assets
        == 3
    )

    # launch a retry of the failed run
    runs = instance.get_run_records()
    list(
        consume_new_runs_for_automatic_reexecution(
            workspace_process_context=workspace_context,
            run_records=runs,
            logger=logger,
        )
    )
    wait_for_all_runs_to_finish(instance, timeout=30)
    assert instance.get_runs_count() == 2

    # now that the failed run has been retried, the backfill daemon can launch runs of the downstream assets
    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    assert instance.get_runs_count() == 4
    wait_for_all_runs_to_start(instance, timeout=30)
    assert instance.get_runs_count() == 4
    wait_for_all_runs_to_finish(instance, timeout=30)
    assert instance.get_runs_count() == 4

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.COMPLETED_SUCCESS
    assert backfill.backfill_end_timestamp is not None
    assert backfill.asset_backfill_data
    assert (
        backfill.asset_backfill_data.failed_and_downstream_subset.num_partitions_and_non_partitioned_assets
        == 0
    )


def test_run_retry_not_part_of_completed_backfill(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    workspace_request_context: BaseWorkspaceRequestContext,
    code_location: CodeLocation,
    remote_repo: RemoteRepository,
):
    backfill_id = "run_retries_backfill"
    partition_keys = static_partitions.get_partition_keys()
    asset_selection = [dg.AssetKey("foo"), dg.AssetKey("a1"), dg.AssetKey("bar")]
    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_request_context.asset_graph,
            backfill_id=backfill_id,
            tags={"custom_tag_key": "custom_tag_value"},
            backfill_timestamp=get_current_timestamp(),
            asset_selection=asset_selection,
            partition_names=partition_keys,
            dynamic_partitions_store=instance,
            all_partitions=False,
            title=None,
            description=None,
            run_config=None,
        )
    )
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
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
        assert run.tags[BACKFILL_ID_TAG] == backfill_id
        assert run.tags["custom_tag_key"] == "custom_tag_value"
        assert step_succeeded(instance, run, "foo")
        assert step_succeeded(instance, run, "reusable")
        assert step_succeeded(instance, run, "bar")

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.COMPLETED_SUCCESS
    assert backfill.backfill_end_timestamp is not None

    # simulate a retry of a run
    run_to_retry = instance.get_runs()[0]
    selector = JobSubsetSelector(
        location_name=code_location.name,
        repository_name=remote_repo.name,
        job_name=run_to_retry.job_name,
        asset_selection=run_to_retry.asset_selection,
        op_selection=None,
    )
    remote_job = code_location.get_job(selector)
    retried_run = instance.create_reexecuted_run(
        parent_run=run_to_retry,
        request_context=workspace_request_context,
        code_location=code_location,
        remote_job=remote_job,
        strategy=ReexecutionStrategy.ALL_STEPS,
        run_config=run_to_retry.run_config,
        use_parent_run_tags=True,  # ensures that the logic for not copying over backfill tags is tested
    )

    for tag in BACKFILL_TAGS:
        assert tag not in retried_run.tags.keys()

    # Since the backfill is alerady complete, it should not be processed by the backfill daemon and
    # should remain in a completed state
    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.COMPLETED_SUCCESS
    assert backfill.backfill_end_timestamp is not None

    assert retried_run.run_id not in [
        r.run_id for r in instance.get_runs(filters=RunsFilter.for_backfill(backfill_id))
    ]


def test_multi_partitioned_asset_backfill(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
):
    del remote_repo

    num_partitions = 4
    target_partitions = multi_partitions_def.get_partition_keys()[0:num_partitions]
    asset_selection = [dg.AssetKey("multi_partitioned_asset")]
    backfill_id = "backfill_multi_partitions"
    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id=backfill_id,
            tags={"custom_tag_key": "custom_tag_value"},
            backfill_timestamp=get_current_timestamp(),
            asset_selection=asset_selection,
            partition_names=target_partitions,
            dynamic_partitions_store=instance,
            all_partitions=False,
            title=None,
            description=None,
            run_config=None,
        )
    )
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    assert instance.get_runs_count() == num_partitions
    wait_for_all_runs_to_start(instance, timeout=30)
    assert instance.get_runs_count() == num_partitions
    wait_for_all_runs_to_finish(instance, timeout=30)

    assert instance.get_runs_count() == num_partitions
    runs = reversed(list(instance.get_runs()))
    for run in runs:
        assert run.tags[BACKFILL_ID_TAG] == backfill_id
        assert run.tags["custom_tag_key"] == "custom_tag_value"

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    backfill = instance.get_backfill(backfill_id)
    assert backfill is not None
    assert backfill.status == BulkActionStatus.COMPLETED_SUCCESS


def test_multi_partitioned_asset_with_single_run_bp_backfill(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
):
    del remote_repo

    target_partitions = ["2023-01-01|x", "2023-01-02|x", "2023-01-01|z", "2023-01-01|y"]
    asset_selection = [dg.AssetKey("multi_partitioned_asset_with_single_run_bp")]
    backfill_id = "backfill_multi_partitions"
    instance.add_backfill(
        PartitionBackfill.from_asset_partitions(
            asset_graph=workspace_context.create_request_context().asset_graph,
            backfill_id=backfill_id,
            tags={"custom_tag_key": "custom_tag_value"},
            backfill_timestamp=get_current_timestamp(),
            asset_selection=asset_selection,
            partition_names=target_partitions,
            dynamic_partitions_store=instance,
            all_partitions=False,
            title=None,
            description=None,
            run_config=None,
        )
    )
    assert instance.get_runs_count() == 0
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    assert backfill.status == BulkActionStatus.REQUESTED

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    # even though it is a single run backfill, the multi-partitions selected will span two ranges
    # because we compute ranges per-primary key
    assert instance.get_runs_count() == 2
    wait_for_all_runs_to_start(instance, timeout=30)
    assert instance.get_runs_count() == 2
    wait_for_all_runs_to_finish(instance, timeout=30)

    assert instance.get_runs_count() == 2
    runs = reversed(list(instance.get_runs()))
    partition_ranges = []
    for run in runs:
        assert run.tags[BACKFILL_ID_TAG] == backfill_id
        partition_ranges.append(
            (run.tags[ASSET_PARTITION_RANGE_START_TAG], run.tags[ASSET_PARTITION_RANGE_END_TAG])
        )

    assert sorted(partition_ranges) == sorted(
        [("2023-01-01|x", "2023-01-01|z"), ("2023-01-02|x", "2023-01-02|x")]
    )

    list(execute_backfill_iteration(workspace_context, get_default_daemon_logger("BackfillDaemon")))
    backfill = instance.get_backfill(backfill_id)
    assert backfill
    wait_for_all_runs_to_start(instance, timeout=30)
    wait_for_all_runs_to_finish(instance, timeout=30)
    assert backfill.status == BulkActionStatus.COMPLETED_SUCCESS

    # assert the expected asset materialization events exist with the expected partitions

    result = instance.fetch_materializations(
        dg.AssetRecordsFilter(
            asset_key=asset_selection[0],
        ),
        limit=10,
    )
    records_in_backfill = []
    for record in result.records:
        run = instance.get_run_by_id(record.run_id)
        if run and run.tags.get(BACKFILL_ID_TAG) == backfill_id:
            records_in_backfill.append(record)

    partitions_materialized = {record.partition_key for record in records_in_backfill}
    assert partitions_materialized == set(target_partitions)


@pytest.mark.skip("Occasionally hangs indefinitely in CI due to threading deadlock")
def test_threaded_submit_backfill(
    instance: DagsterInstance,
    workspace_context: WorkspaceProcessContext,
    remote_repo: RemoteRepository,
):
    job_def = the_repo.get_job("multi_asset_job")
    assert job_def
    partition_set_name = f"{job_def.name}_partition_set"
    partition_set = remote_repo.get_partition_set(partition_set_name)
    backfill = PartitionBackfill(
        backfill_id="backfill_with_asset_selection",
        partition_set_origin=partition_set.get_remote_origin(),
        status=BulkActionStatus.REQUESTED,
        partition_names=["one", "two", "three"],
        from_failure=False,
        reexecution_steps=None,
        tags=None,
        backfill_timestamp=get_current_timestamp(),
    )
    assert not backfill.is_asset_backfill
    instance.add_backfill(backfill)
    assert instance.get_runs_count() == 0

    with ThreadPoolExecutor(3) as submit_threadpool_executor:
        list(
            execute_backfill_iteration(
                workspace_context,
                get_default_daemon_logger("BackfillDaemon"),
                threadpool_executor=None,
                submit_threadpool_executor=submit_threadpool_executor,
            )
        )

    assert instance.get_runs_count() == 3
    runs = instance.get_runs()
    partitions = {run.tags[PARTITION_NAME_TAG] for run in runs}
    assert partitions == {"one", "two", "three"}
