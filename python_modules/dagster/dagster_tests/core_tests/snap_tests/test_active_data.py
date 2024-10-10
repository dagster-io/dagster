from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime
from unittest import mock

from dagster import daily_partitioned_config, job, op, repository
from dagster._core.definitions.decorators.schedule_decorator import schedule
from dagster._core.remote_representation import external_job_data_from_def
from dagster._core.remote_representation.external_data import (
    RepositorySnap,
    TimeWindowPartitionsSnap,
)
from dagster._core.snap.job_snapshot import create_job_snapshot_id
from dagster._core.test_utils import in_process_test_workspace, instance_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
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


def test_external_repository_data(snapshot):
    @repository
    def repo():
        return [foo_job, foo_schedule]

    external_repo_data = RepositorySnap.from_def(repo)
    assert external_repo_data.get_job_data("foo_job")
    assert external_repo_data.get_schedule("foo_schedule")

    job_partition_set_data = external_repo_data.get_partition_set("foo_job_partition_set")
    assert job_partition_set_data
    assert isinstance(job_partition_set_data.partitions, TimeWindowPartitionsSnap)

    now = get_current_datetime()

    assert job_partition_set_data.partitions.get_partitions_definition().get_partition_keys(
        now
    ) == my_partitioned_config.partitions_def.get_partition_keys(now)

    snapshot.assert_match(serialize_pp(external_repo_data))


def test_external_job_data(snapshot):
    snapshot.assert_match(
        serialize_pp(external_job_data_from_def(foo_job, include_parent_snapshot=True))
    )


@mock.patch("dagster._core.remote_representation.job_index.create_job_snapshot_id")
def test_external_repo_shared_index(snapshot_mock):
    # ensure we don't rebuild indexes / snapshot ids repeatedly

    snapshot_mock.side_effect = create_job_snapshot_id
    with instance_for_test() as instance:
        with in_process_test_workspace(
            instance, LoadableTargetOrigin(python_file=__file__)
        ) as workspace:

            def _fetch_snap_id():
                location = workspace.code_locations[0]
                ex_repo = next(iter(location.get_repositories().values()))
                return ex_repo.get_all_jobs()[0].identifying_job_snapshot_id

            _fetch_snap_id()
            assert snapshot_mock.call_count == 1

            _fetch_snap_id()
            assert snapshot_mock.call_count == 1


@mock.patch("dagster._core.remote_representation.job_index.create_job_snapshot_id")
def test_external_repo_shared_index_threaded(snapshot_mock):
    # ensure we don't rebuild indexes / snapshot ids repeatedly across threads

    snapshot_mock.side_effect = create_job_snapshot_id
    with instance_for_test() as instance:
        with in_process_test_workspace(
            instance, LoadableTargetOrigin(python_file=__file__)
        ) as workspace:

            def _fetch_snap_id():
                location = workspace.code_locations[0]
                ex_repo = next(iter(location.get_repositories().values()))
                return ex_repo.get_all_jobs()[0].identifying_job_snapshot_id

            with ThreadPoolExecutor() as executor:
                wait([executor.submit(_fetch_snap_id) for _ in range(100)])

            assert snapshot_mock.call_count == 1
