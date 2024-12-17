from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime
from unittest import mock

from dagster import daily_partitioned_config, job, op, repository
from dagster._core.definitions.decorators.schedule_decorator import schedule
from dagster._core.remote_representation.external_data import (
    JobDataSnap,
    RepositorySnap,
    TimeWindowPartitionsSnap,
)
from dagster._core.snap.job_snapshot import _create_job_snapshot_id
from dagster._core.test_utils import create_test_daemon_workspace_context, instance_for_test
from dagster._serdes import serialize_pp
from dagster._time import get_current_datetime


@op
def foo_op(_):
    pass


@schedule(
    cron_schedule="@daily",
    job_name="foo_job",
    execution_timezone="US/Central",
)
def foo_schedule():
    return {}


@daily_partitioned_config(start_date=datetime(2020, 1, 1), minute_offset=15)
def my_partitioned_config(_start: datetime, _end: datetime):
    return {}


@job(config=my_partitioned_config)
def foo_job():
    foo_op()


@repository
def a_repo():
    return [foo_job]


def test_repository_snap(snapshot):
    @repository
    def repo():
        return [foo_job, foo_schedule]

    repo_snap = RepositorySnap.from_def(repo)
    assert repo_snap.get_job_data("foo_job")
    assert repo_snap.get_schedule("foo_schedule")

    job_partition_set_data = repo_snap.get_partition_set("foo_job_partition_set")
    assert job_partition_set_data
    assert isinstance(job_partition_set_data.partitions, TimeWindowPartitionsSnap)

    now = get_current_datetime()

    assert job_partition_set_data.partitions.get_partitions_definition().get_partition_keys(
        now
    ) == my_partitioned_config.partitions_def.get_partition_keys(now)

    snapshot.assert_match(serialize_pp(repo_snap))


def test_remote_job_data(snapshot):
    snapshot.assert_match(
        serialize_pp(JobDataSnap.from_job_def(foo_job, include_parent_snapshot=True))
    )


import os

from dagster._core.workspace.load_target import ModuleTarget


def workspace_load_target():
    return ModuleTarget(
        module_name="dagster_tests.core_tests.snap_tests.test_active_data",
        attribute="a_repo",
        working_directory=os.path.join(os.path.dirname(__file__), "..", "..", ".."),
        location_name="test_location",
    )


def test_remote_repo_shared_index_single_threaded():
    # ensure we don't rebuild indexes / snapshot ids repeatedly
    with mock.patch("dagster._core.snap.job_snapshot._create_job_snapshot_id") as snapshot_mock:
        snapshot_mock.side_effect = _create_job_snapshot_id
        with instance_for_test() as instance:
            with create_test_daemon_workspace_context(
                workspace_load_target(),
                instance,
            ) as workspace_process_context:
                workspace = workspace_process_context.create_request_context()

                def _fetch_snap_id():
                    location = workspace.code_locations[0]
                    ex_repo = next(iter(location.get_repositories().values()))
                    return ex_repo.get_all_jobs()[0].identifying_job_snapshot_id

                _fetch_snap_id()
                assert snapshot_mock.call_count == 1

                _fetch_snap_id()
                assert snapshot_mock.call_count == 1


def test_remote_repo_shared_index_multi_threaded():
    # ensure we don't rebuild indexes / snapshot ids repeatedly across threads
    with mock.patch("dagster._core.snap.job_snapshot._create_job_snapshot_id") as snapshot_mock:
        snapshot_mock.side_effect = _create_job_snapshot_id
        with instance_for_test() as instance:
            with create_test_daemon_workspace_context(
                workspace_load_target(),
                instance,
            ) as workspace_process_context:
                workspace = workspace_process_context.create_request_context()

                def _fetch_snap_id():
                    location = workspace.code_locations[0]
                    ex_repo = next(iter(location.get_repositories().values()))
                    return ex_repo.get_all_jobs()[0].identifying_job_snapshot_id

                with ThreadPoolExecutor() as executor:
                    wait([executor.submit(_fetch_snap_id) for _ in range(100)])

                assert snapshot_mock.call_count == 1
