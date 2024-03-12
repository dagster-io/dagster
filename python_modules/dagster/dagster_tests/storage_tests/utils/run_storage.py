import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from typing import Optional

import pendulum
import pytest
from dagster import _seven, job, op
from dagster._core.definitions import GraphDefinition
from dagster._core.errors import (
    DagsterRunAlreadyExists,
    DagsterRunNotFoundError,
    DagsterSnapshotDoesNotExist,
)
from dagster._core.events import DagsterEvent, DagsterEventType, JobFailureData, RunFailureReason
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.instance import DagsterInstance, InstanceType
from dagster._core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster._core.remote_representation import (
    ExternalRepositoryOrigin,
    ManagedGrpcPythonEnvCodeLocationOrigin,
)
from dagster._core.run_coordinator import DefaultRunCoordinator
from dagster._core.snap import create_job_snapshot_id
from dagster._core.storage.dagster_run import (
    DagsterRun,
    DagsterRunStatus,
    RunsFilter,
)
from dagster._core.storage.event_log import InMemoryEventLogStorage
from dagster._core.storage.noop_compute_log_manager import NoOpComputeLogManager
from dagster._core.storage.root import LocalArtifactStorage
from dagster._core.storage.runs.base import RunStorage
from dagster._core.storage.runs.migration import REQUIRED_DATA_MIGRATIONS
from dagster._core.storage.runs.sql_run_storage import SqlRunStorage
from dagster._core.storage.tags import (
    PARENT_RUN_ID_TAG,
    PARTITION_NAME_TAG,
    PARTITION_SET_TAG,
    REPOSITORY_LABEL_TAG,
    ROOT_RUN_ID_TAG,
    RUN_FAILURE_REASON_TAG,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.utils import make_new_run_id
from dagster._daemon.daemon import SensorDaemon
from dagster._daemon.types import DaemonHeartbeat
from dagster._serdes import serialize_pp
from dagster._seven.compat.pendulum import create_pendulum_time, pendulum_freeze_time, to_timezone

win_py36 = _seven.IS_WINDOWS and sys.version_info[0] == 3 and sys.version_info[1] == 6


def _get_run_by_id(storage, run_id) -> Optional[DagsterRun]:
    records = storage.get_run_records(RunsFilter(run_ids=[run_id]))
    if not records:
        return None
    return records[0].dagster_run


class TestRunStorage:
    """You can extend this class to easily run these set of tests on any run storage. When extending,
    you simply need to override the `run_storage` fixture and return your implementation of
    `RunStorage`.

    For example:

    ```
    class TestMyStorageImplementation(TestRunStorage):
        __test__ = True

        @pytest.fixture(scope='function', name='storage')
        def run_storage(self):
            return MyStorageImplementation()
    ```
    """

    __test__ = False

    @pytest.fixture(name="storage", params=[])
    def run_storage(self, request):
        with request.param() as s:
            yield s

    # Override for storages that are not allowed to delete runs
    def can_delete_runs(self):
        return True

    @staticmethod
    def fake_repo_target(repo_name=None):
        name = repo_name or "fake_repo_name"
        return ExternalRepositoryOrigin(
            ManagedGrpcPythonEnvCodeLocationOrigin(
                LoadableTargetOrigin(
                    executable_path=sys.executable, module_name="fake", attribute="fake"
                ),
            ),
            name,
        )

    @classmethod
    def fake_job_origin(cls, job_name, repo_name=None):
        return cls.fake_repo_target(repo_name).get_job_origin(job_name)

    @classmethod
    def fake_partition_set_origin(cls, partition_set_name):
        return cls.fake_repo_target().get_partition_set_origin(partition_set_name)

    @staticmethod
    def build_run(
        run_id,
        job_name,
        tags=None,
        status=DagsterRunStatus.NOT_STARTED,
        parent_run_id=None,
        root_run_id=None,
        job_snapshot_id=None,
        external_job_origin=None,
    ):
        return DagsterRun(
            job_name=job_name,
            run_id=run_id,
            run_config=None,
            tags=tags,
            status=status,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            job_snapshot_id=job_snapshot_id,
            external_job_origin=external_job_origin,
        )

    def test_basic_storage(self, storage):
        assert storage
        run_id = make_new_run_id()
        added = storage.add_run(
            TestRunStorage.build_run(run_id=run_id, job_name="some_pipeline", tags={"foo": "bar"})
        )
        assert added
        runs = storage.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert run.run_id == run_id
        assert run.job_name == "some_pipeline"
        assert run.tags
        assert run.tags.get("foo") == "bar"
        assert storage.has_run(run_id)
        fetched_run = _get_run_by_id(storage, run_id)
        assert fetched_run.run_id == run_id
        assert fetched_run.job_name == "some_pipeline"

    def test_clear(self, storage):
        if not self.can_delete_runs():
            pytest.skip("storage cannot delete")

        assert storage
        run_id = make_new_run_id()
        storage.add_run(TestRunStorage.build_run(run_id=run_id, job_name="some_pipeline"))
        assert len(storage.get_runs()) == 1
        storage.wipe()
        assert list(storage.get_runs()) == []

    def test_storage_telemetry(self, storage):
        assert storage
        storage_id = storage.get_run_storage_id()
        assert isinstance(storage_id, str)
        storage_id_again = storage.get_run_storage_id()
        assert storage_id == storage_id_again

    def test_fetch_by_job(self, storage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()
        storage.add_run(TestRunStorage.build_run(run_id=one, job_name="some_pipeline"))
        storage.add_run(TestRunStorage.build_run(run_id=two, job_name="some_other_pipeline"))
        assert len(storage.get_runs()) == 2
        some_runs = storage.get_runs(RunsFilter(job_name="some_pipeline"))
        assert len(some_runs) == 1
        assert some_runs[0].run_id == one

    def test_fetch_by_repo(self, storage):
        assert storage
        self._skip_in_memory(storage)

        one = make_new_run_id()
        two = make_new_run_id()
        job_name = "some_job"

        origin_one = self.fake_job_origin(job_name, "fake_repo_one")
        origin_two = self.fake_job_origin(job_name, "fake_repo_two")
        storage.add_run(
            TestRunStorage.build_run(run_id=one, job_name=job_name, external_job_origin=origin_one)
        )
        storage.add_run(
            TestRunStorage.build_run(run_id=two, job_name=job_name, external_job_origin=origin_two)
        )
        one_runs = storage.get_runs(
            RunsFilter(tags={REPOSITORY_LABEL_TAG: "fake_repo_one@fake:fake"})
        )
        assert len(one_runs) == 1
        two_runs = storage.get_runs(
            RunsFilter(tags={REPOSITORY_LABEL_TAG: "fake_repo_two@fake:fake"})
        )
        assert len(two_runs) == 1

    def test_fetch_by_snapshot_id(self, storage):
        assert storage
        job_def_a = GraphDefinition(name="some_pipeline", node_defs=[]).to_job()
        job_def_b = GraphDefinition(name="some_other_pipeline", node_defs=[]).to_job()
        job_snapshot_a = job_def_a.get_job_snapshot()
        job_snapshot_b = job_def_b.get_job_snapshot()
        job_snapshot_a_id = create_job_snapshot_id(job_snapshot_a)
        job_snapshot_b_id = create_job_snapshot_id(job_snapshot_b)

        assert storage.add_job_snapshot(job_snapshot_a) == job_snapshot_a_id
        assert storage.add_job_snapshot(job_snapshot_b) == job_snapshot_b_id

        one = make_new_run_id()
        two = make_new_run_id()
        storage.add_run(
            TestRunStorage.build_run(
                run_id=one,
                job_name="some_pipeline",
                job_snapshot_id=job_snapshot_a_id,
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two,
                job_name="some_other_pipeline",
                job_snapshot_id=job_snapshot_b_id,
            )
        )
        assert len(storage.get_runs()) == 2
        runs_a = storage.get_runs(RunsFilter(snapshot_id=job_snapshot_a_id))
        assert len(runs_a) == 1
        assert runs_a[0].run_id == one

        runs_b = storage.get_runs(RunsFilter(snapshot_id=job_snapshot_b_id))
        assert len(runs_b) == 1
        assert runs_b[0].run_id == two

    def test_add_run_tags(self, storage: RunStorage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()

        storage.add_run(TestRunStorage.build_run(run_id=one, job_name="foo"))
        storage.add_run(TestRunStorage.build_run(run_id=two, job_name="bar"))

        assert storage.get_run_tags(tag_keys=["tag1", "tag2"]) == []

        storage.add_run_tags(one, {"tag1": "val1", "tag2": "val2"})
        storage.add_run_tags(two, {"tag1": "val1"})

        assert storage.get_run_tags(tag_keys=["tag1", "tag2"]) == [
            ("tag1", {"val1"}),
            ("tag2", {"val2"}),
        ]

        # Adding both existing tags and a new tag
        storage.add_run_tags(one, {"tag1": "val2", "tag3": "val3"})

        test_run = _get_run_by_id(storage, one)
        assert test_run

        assert len(test_run.tags) == 3
        assert test_run.tags["tag1"] == "val2"
        assert test_run.tags["tag2"] == "val2"
        assert test_run.tags["tag3"] == "val3"

        assert storage.get_run_tags(tag_keys=["tag1", "tag2", "tag3"]) == [
            ("tag1", {"val1", "val2"}),
            ("tag2", {"val2"}),
            ("tag3", {"val3"}),
        ]

        # Adding only existing tags
        storage.add_run_tags(one, {"tag1": "val3"})

        test_run = _get_run_by_id(storage, one)
        assert test_run
        assert len(test_run.tags) == 3
        assert test_run.tags["tag1"] == "val3"
        assert test_run.tags["tag2"] == "val2"
        assert test_run.tags["tag3"] == "val3"

        assert storage.get_run_tags(tag_keys=["tag1", "tag2", "tag3"]) == [
            ("tag1", {"val1", "val3"}),
            ("tag2", {"val2"}),
            ("tag3", {"val3"}),
        ]

        # Adding only a new tag that wasn't there before
        storage.add_run_tags(one, {"tag4": "val4"})

        test_run = _get_run_by_id(storage, one)
        assert test_run

        assert len(test_run.tags) == 4
        assert test_run.tags["tag1"] == "val3"
        assert test_run.tags["tag2"] == "val2"
        assert test_run.tags["tag3"] == "val3"
        assert test_run.tags["tag4"] == "val4"

        assert storage.get_run_tags(tag_keys=["tag1", "tag2", "tag3", "tag4"]) == [
            ("tag1", {"val1", "val3"}),
            ("tag2", {"val2"}),
            ("tag3", {"val3"}),
            ("tag4", {"val4"}),
        ]

        test_run = _get_run_by_id(storage, one)
        assert test_run
        assert len(test_run.tags) == 4
        assert test_run.tags["tag1"] == "val3"
        assert test_run.tags["tag2"] == "val2"
        assert test_run.tags["tag3"] == "val3"
        assert test_run.tags["tag4"] == "val4"

        some_runs = storage.get_runs(RunsFilter(tags={"tag3": "val3"}))

        assert len(some_runs) == 1
        assert some_runs[0].run_id == one

        runs_with_old_tag = storage.get_runs(RunsFilter(tags={"tag1": "val1"}))
        assert len(runs_with_old_tag) == 1
        assert runs_with_old_tag[0].tags == {"tag1": "val1"}

        runs_with_new_tag = storage.get_runs(RunsFilter(tags={"tag1": "val3"}))
        assert len(runs_with_new_tag) == 1
        assert runs_with_new_tag[0].tags == {
            "tag1": "val3",
            "tag2": "val2",
            "tag3": "val3",
            "tag4": "val4",
        }

    def test_get_run_tags(self, storage: RunStorage):
        one = make_new_run_id()
        two = make_new_run_id()
        storage.add_run(TestRunStorage.build_run(run_id=one, job_name="foo"))
        storage.add_run(TestRunStorage.build_run(run_id=two, job_name="foo"))
        storage.add_run_tags(
            one,
            {
                "tag1": "val1",
                "tag2": "val2",
                "tag3": "val3",
                "tag4": "val4",
                "x_1": "x_1",
                "x_2": "x_2",
            },
        )
        storage.add_run_tags(two, {"tag1": "val3"})

        # test getting run tag keys
        assert storage.get_run_tag_keys() == ["tag1", "tag2", "tag3", "tag4", "x_1", "x_2"]

        # test getting run tags with key filter
        assert storage.get_run_tags(tag_keys=["tag1"]) == [
            ("tag1", {"val1", "val3"}),
        ]
        assert storage.get_run_tags(tag_keys=["tag1", "tag2"]) == [
            ("tag1", {"val1", "val3"}),
            ("tag2", {"val2"}),
        ]

        # test getting run tags with prefix
        assert storage.get_run_tags(tag_keys=["x_1", "x_2"], value_prefix="x_") == [
            ("x_1", {"x_1"}),
            ("x_2", {"x_2"}),
        ]

        # test getting run tags with limit
        assert storage.get_run_tags(tag_keys=["tag1", "tag2"], limit=3) == [
            ("tag1", {"val1", "val3"}),
            ("tag2", {"val2"}),
        ]

        # empty tag_keys implies nothing instead of everything
        assert storage.get_run_tags(tag_keys=[]) == []

    def test_fetch_by_filter(self, storage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()
        three = make_new_run_id()
        four = make_new_run_id()

        storage.add_run(
            TestRunStorage.build_run(
                run_id=one,
                job_name="some_pipeline",
                tags={"tag": "hello", "tag2": "world"},
                status=DagsterRunStatus.SUCCESS,
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two,
                job_name="some_pipeline",
                tags={"tag": "hello"},
                status=DagsterRunStatus.FAILURE,
            ),
        )

        storage.add_run(
            TestRunStorage.build_run(
                run_id=three, job_name="other_pipeline", status=DagsterRunStatus.SUCCESS
            )
        )

        storage.add_run(
            TestRunStorage.build_run(
                run_id=four,
                job_name="some_other_pipeline",
                tags={"tag": "goodbye"},
                status=DagsterRunStatus.FAILURE,
            ),
        )

        assert len(storage.get_runs()) == 4

        run_ids_filter = RunsFilter(run_ids=[one])
        some_runs = storage.get_runs(run_ids_filter)
        count = storage.get_runs_count(run_ids_filter)
        ids = storage.get_run_ids(run_ids_filter)
        assert len(some_runs) == 1
        assert count == 1
        assert some_runs[0].run_id == one
        assert ids == [one]

        job_name_filter = RunsFilter(job_name="some_pipeline")
        some_runs = storage.get_runs(job_name_filter)
        count = storage.get_runs_count(job_name_filter)
        ids = storage.get_run_ids(job_name_filter)
        assert len(some_runs) == 2
        assert count == 2
        assert some_runs[0].run_id == two
        assert some_runs[1].run_id == one
        assert ids == [two, one]

        run_status_filter = RunsFilter(statuses=[DagsterRunStatus.SUCCESS])
        some_runs = storage.get_runs(run_status_filter)
        count = storage.get_runs_count(run_status_filter)
        run_ids = storage.get_run_ids(run_status_filter)
        assert len(some_runs) == 2
        assert count == 2
        assert some_runs[0].run_id == three
        assert some_runs[1].run_id == one
        assert run_ids == [three, one]

        run_tags_filter = RunsFilter(tags={"tag": "hello"})
        some_runs = storage.get_runs(run_tags_filter)
        count = storage.get_runs_count(run_tags_filter)
        run_ids = storage.get_run_ids(run_tags_filter)
        assert len(some_runs) == 2
        assert count == 2
        assert some_runs[0].run_id == two
        assert some_runs[1].run_id == one
        assert run_ids == [two, one]

        two_run_tags_filter = RunsFilter(tags={"tag": "hello", "tag2": "world"})
        some_runs = storage.get_runs(two_run_tags_filter)
        count = storage.get_runs_count(two_run_tags_filter)
        run_ids = storage.get_run_ids(two_run_tags_filter)
        assert len(some_runs) == 1
        assert count == 1
        assert some_runs[0].run_id == one
        assert run_ids == [one]

        job_and_tags_filter = RunsFilter(job_name="some_pipeline", tags={"tag": "hello"})
        some_runs = storage.get_runs(job_and_tags_filter)
        count = storage.get_runs_count(job_and_tags_filter)
        run_ids = storage.get_run_ids(job_and_tags_filter)
        assert len(some_runs) == 2
        assert count == 2
        assert some_runs[0].run_id == two
        assert some_runs[1].run_id == one
        assert run_ids == [two, one]

        multiple_tag_values_filter = RunsFilter(tags={"tag": ["hello", "goodbye", "farewell"]})
        runs_with_multiple_tag_values = storage.get_runs(multiple_tag_values_filter)
        assert len(runs_with_multiple_tag_values) == 3
        assert runs_with_multiple_tag_values[0].run_id == four
        assert runs_with_multiple_tag_values[1].run_id == two
        assert runs_with_multiple_tag_values[2].run_id == one

        multiple_tags_values_filter = RunsFilter(
            tags={"tag": ["hello", "goodbye", "farewell"], "tag2": "world"},
        )
        runs_with_multiple_tags_values = storage.get_runs(multiple_tags_values_filter)
        assert len(runs_with_multiple_tags_values) == 1
        assert runs_with_multiple_tags_values[0].run_id == one

        count_with_multiple_tag_values = storage.get_runs_count(multiple_tag_values_filter)
        assert count_with_multiple_tag_values == 3

        assert storage.get_run_ids(multiple_tag_values_filter) == [four, two, one]

        multiple_filters = RunsFilter(
            job_name="some_pipeline",
            tags={"tag": "hello"},
            statuses=[DagsterRunStatus.SUCCESS],
        )
        some_runs = storage.get_runs(multiple_filters)
        count = storage.get_runs_count(multiple_filters)
        run_ids = storage.get_run_ids(multiple_filters)
        assert len(some_runs) == 1
        assert count == 1
        assert some_runs[0].run_id == one
        assert run_ids == [one]

        # All filters
        all_filters = RunsFilter(
            run_ids=[one],
            job_name="some_pipeline",
            tags={"tag": "hello"},
            statuses=[DagsterRunStatus.SUCCESS],
        )
        some_runs = storage.get_runs(all_filters)
        count = storage.get_runs_count(all_filters)
        run_ids = storage.get_run_ids(all_filters)
        assert len(some_runs) == 1
        assert count == 1
        assert some_runs[0].run_id == one
        assert run_ids == [one]

        empty_filter = RunsFilter()
        some_runs = storage.get_runs(empty_filter)
        count = storage.get_runs_count(empty_filter)
        run_ids = storage.get_run_ids(empty_filter)
        assert len(some_runs) == 4
        assert count == 4
        assert run_ids == [four, three, two, one]

    def test_fetch_count_by_tag(self, storage: RunStorage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()
        three = make_new_run_id()
        storage.add_run(
            TestRunStorage.build_run(
                run_id=one,
                job_name="some_pipeline",
                tags={"mytag": "hello", "mytag2": "world"},
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two,
                job_name="some_pipeline",
                tags={"mytag": "goodbye", "mytag2": "world"},
            )
        )
        storage.add_run(TestRunStorage.build_run(run_id=three, job_name="some_pipeline"))
        assert len(storage.get_runs()) == 3

        run_count = storage.get_runs_count(
            filters=RunsFilter(tags={"mytag": "hello", "mytag2": "world"})
        )
        assert run_count == 1

        run_count = storage.get_runs_count(filters=RunsFilter(tags={"mytag2": "world"}))
        assert run_count == 2

        run_count = storage.get_runs_count()
        assert run_count == 3

        assert storage.get_run_tags(tag_keys=["mytag", "mytag2"]) == [
            ("mytag", {"hello", "goodbye"}),
            ("mytag2", {"world"}),
        ]

    def test_fetch_by_tags(self, storage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()
        three = make_new_run_id()
        storage.add_run(
            TestRunStorage.build_run(
                run_id=one,
                job_name="some_pipeline",
                tags={"mytag": "hello", "mytag2": "world"},
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two,
                job_name="some_pipeline",
                tags={"mytag": "goodbye", "mytag2": "world"},
            )
        )
        storage.add_run(TestRunStorage.build_run(run_id=three, job_name="some_pipeline"))
        assert len(storage.get_runs()) == 3

        some_runs = storage.get_runs(RunsFilter(tags={"mytag": "hello", "mytag2": "world"}))

        assert len(some_runs) == 1
        assert some_runs[0].run_id == one

        some_runs = storage.get_runs(RunsFilter(tags={"mytag2": "world"}))
        assert len(some_runs) == 2
        assert some_runs[0].run_id == two
        assert some_runs[1].run_id == one

        some_runs = storage.get_runs(RunsFilter(tags={}))
        assert len(some_runs) == 3

    def test_paginated_fetch(self, storage):
        assert storage
        one, two, three = [make_new_run_id(), make_new_run_id(), make_new_run_id()]
        storage.add_run(
            TestRunStorage.build_run(run_id=one, job_name="some_pipeline", tags={"mytag": "hello"})
        )
        storage.add_run(
            TestRunStorage.build_run(run_id=two, job_name="some_pipeline", tags={"mytag": "hello"})
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=three, job_name="some_pipeline", tags={"mytag": "hello"}
            )
        )

        all_runs = storage.get_runs()
        assert len(all_runs) == 3
        assert storage.get_run_ids() == [three, two, one]
        sliced_runs = storage.get_runs(cursor=three, limit=1)
        assert len(sliced_runs) == 1
        assert sliced_runs[0].run_id == two
        assert storage.get_run_ids(cursor=three, limit=1) == [two]

        all_runs = storage.get_runs(RunsFilter(job_name="some_pipeline"))
        assert len(all_runs) == 3
        assert storage.get_run_ids(RunsFilter(job_name="some_pipeline")) == [three, two, one]
        sliced_runs = storage.get_runs(RunsFilter(job_name="some_pipeline"), cursor=three, limit=1)
        assert len(sliced_runs) == 1
        assert sliced_runs[0].run_id == two
        assert storage.get_run_ids(RunsFilter(job_name="some_pipeline"), cursor=three, limit=1) == [
            two
        ]

        all_runs = storage.get_runs(RunsFilter(tags={"mytag": "hello"}))
        assert len(all_runs) == 3
        assert storage.get_run_ids(RunsFilter(tags={"mytag": "hello"})) == [three, two, one]
        sliced_runs = storage.get_runs(RunsFilter(tags={"mytag": "hello"}), cursor=three, limit=1)
        assert len(sliced_runs) == 1
        assert sliced_runs[0].run_id == two
        assert storage.get_run_ids(RunsFilter(tags={"mytag": "hello"}), cursor=three, limit=1) == [
            two
        ]

    def test_get_run_ids(self, storage):
        assert storage

        one, two, three = [make_new_run_id(), make_new_run_id(), make_new_run_id()]
        storage.add_run(
            TestRunStorage.build_run(run_id=one, job_name="some_pipeline", tags={"mytag": "hello"})
        )
        storage.add_run(
            TestRunStorage.build_run(run_id=two, job_name="some_pipeline", tags={"mytag": "hello"})
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=three, job_name="some_pipeline", tags={"mytag": "hello"}
            )
        )

        assert storage.get_run_ids(RunsFilter(job_name="some_pipeline")) == [three, two, one]
        assert storage.get_run_ids(RunsFilter(job_name="some_pipeline"), limit=1) == [three]

    def test_fetch_by_status(self, storage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()
        three = make_new_run_id()
        four = make_new_run_id()
        storage.add_run(
            TestRunStorage.build_run(
                run_id=one, job_name="some_pipeline", status=DagsterRunStatus.NOT_STARTED
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two, job_name="some_pipeline", status=DagsterRunStatus.STARTED
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=three, job_name="some_pipeline", status=DagsterRunStatus.STARTED
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=four, job_name="some_pipeline", status=DagsterRunStatus.FAILURE
            )
        )

        assert {
            run.run_id
            for run in storage.get_runs(RunsFilter(statuses=[DagsterRunStatus.NOT_STARTED]))
        } == {one}

        assert {
            run.run_id for run in storage.get_runs(RunsFilter(statuses=[DagsterRunStatus.STARTED]))
        } == {
            two,
            three,
        }

        assert {
            run.run_id for run in storage.get_runs(RunsFilter(statuses=[DagsterRunStatus.FAILURE]))
        } == {four}

        assert {
            run.run_id for run in storage.get_runs(RunsFilter(statuses=[DagsterRunStatus.SUCCESS]))
        } == set()

    def test_failure_event_updates_tags(self, storage):
        assert storage
        one = make_new_run_id()
        storage.add_run(
            TestRunStorage.build_run(
                run_id=one, job_name="some_pipeline", status=DagsterRunStatus.STARTED
            )
        )
        storage.handle_run_event(
            one,  # fail one after two has fails and three has succeeded
            DagsterEvent(
                message="a message",
                event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
                job_name="some_pipeline",
                event_specific_data=JobFailureData(
                    error=None, failure_reason=RunFailureReason.RUN_EXCEPTION
                ),
            ),
        )

        run = _get_run_by_id(storage, one)
        assert run.tags[RUN_FAILURE_REASON_TAG] == RunFailureReason.RUN_EXCEPTION.value

    def test_fetch_records_by_update_timestamp(self, storage):
        assert storage
        self._skip_in_memory(storage)

        one = make_new_run_id()
        two = make_new_run_id()
        three = make_new_run_id()
        storage.add_run(
            TestRunStorage.build_run(
                run_id=one, job_name="some_pipeline", status=DagsterRunStatus.STARTED
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two, job_name="some_pipeline", status=DagsterRunStatus.FAILURE
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=three, job_name="some_pipeline", status=DagsterRunStatus.STARTED
            )
        )
        storage.handle_run_event(
            three,  # three succeeds
            DagsterEvent(
                message="a message",
                event_type_value=DagsterEventType.PIPELINE_SUCCESS.value,
                job_name="some_pipeline",
            ),
        )
        storage.handle_run_event(
            one,  # fail one after two has fails and three has succeeded
            DagsterEvent(
                message="a message",
                event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
                job_name="some_pipeline",
            ),
        )

        record_two = storage.get_run_records(
            filters=RunsFilter(run_ids=[two], updated_after=datetime(2020, 1, 1))
        )[0]
        run_two_update_timestamp = record_two.update_timestamp
        record_three = storage.get_run_records(filters=RunsFilter(run_ids=[three]))[0]

        assert [
            record.dagster_run.run_id
            for record in storage.get_run_records(
                filters=RunsFilter(updated_after=run_two_update_timestamp),
                order_by="update_timestamp",
                ascending=True,
            )
        ] == [three, one]

        assert [
            record.dagster_run.run_id
            for record in storage.get_run_records(
                filters=RunsFilter(
                    statuses=[DagsterRunStatus.FAILURE], updated_after=run_two_update_timestamp
                ),
            )
        ] == [one]

        assert [
            record.dagster_run.run_id
            for record in storage.get_run_records(
                filters=RunsFilter(updated_before=record_three.update_timestamp)
            )
        ] == [two]

    def test_fetch_records_by_create_timestamp(self, storage):
        assert storage
        self._skip_in_memory(storage)

        one = make_new_run_id()
        two = make_new_run_id()
        three = make_new_run_id()
        storage.add_run(
            TestRunStorage.build_run(
                run_id=one, job_name="some_pipeline", status=DagsterRunStatus.STARTED
            )
        )
        time.sleep(2)
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two, job_name="some_pipeline", status=DagsterRunStatus.STARTED
            )
        )
        time.sleep(2)
        storage.add_run(
            TestRunStorage.build_run(
                run_id=three, job_name="some_pipeline", status=DagsterRunStatus.STARTED
            )
        )
        records = storage.get_run_records()
        assert len(records) == 3
        run_two_create_timestamp = records[1].create_timestamp

        assert [
            record.dagster_run.run_id
            for record in storage.get_run_records(
                filters=RunsFilter(created_after=run_two_create_timestamp + timedelta(seconds=1)),
            )
        ] == [three]
        assert [
            record.dagster_run.run_id
            for record in storage.get_run_records(
                filters=RunsFilter(created_before=run_two_create_timestamp - timedelta(seconds=1)),
            )
        ] == [one]

    def test_fetch_by_status_cursored(self, storage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()
        three = make_new_run_id()
        four = make_new_run_id()
        storage.add_run(
            TestRunStorage.build_run(
                run_id=one, job_name="some_pipeline", status=DagsterRunStatus.STARTED
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two, job_name="some_pipeline", status=DagsterRunStatus.STARTED
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=three, job_name="some_pipeline", status=DagsterRunStatus.NOT_STARTED
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=four, job_name="some_pipeline", status=DagsterRunStatus.STARTED
            )
        )

        cursor_four_runs = storage.get_runs(
            RunsFilter(statuses=[DagsterRunStatus.STARTED]), cursor=four
        )
        assert len(cursor_four_runs) == 2
        assert {run.run_id for run in cursor_four_runs} == {one, two}

        cursor_two_runs = storage.get_runs(
            RunsFilter(statuses=[DagsterRunStatus.STARTED]), cursor=two
        )
        assert len(cursor_two_runs) == 1
        assert {run.run_id for run in cursor_two_runs} == {one}

        cursor_one_runs = storage.get_runs(
            RunsFilter(statuses=[DagsterRunStatus.STARTED]), cursor=one
        )
        assert not cursor_one_runs

        cursor_four_limit_one = storage.get_runs(
            RunsFilter(statuses=[DagsterRunStatus.STARTED]), cursor=four, limit=1
        )
        assert len(cursor_four_limit_one) == 1
        assert cursor_four_limit_one[0].run_id == two

    def test_delete(self, storage):
        if not self.can_delete_runs():
            pytest.skip("storage cannot delete runs")

        assert storage
        run_id = make_new_run_id()
        storage.add_run(TestRunStorage.build_run(run_id=run_id, job_name="some_pipeline"))
        assert len(storage.get_runs()) == 1
        storage.delete_run(run_id)
        assert list(storage.get_runs()) == []

    def test_delete_with_tags(self, storage: RunStorage):
        if not self.can_delete_runs():
            pytest.skip("storage cannot delete runs")

        assert storage
        run_id = make_new_run_id()
        storage.add_run(
            TestRunStorage.build_run(
                run_id=run_id,
                job_name="some_pipeline",
                tags={run_id: run_id},
            )
        )
        assert len(storage.get_runs()) == 1
        assert run_id in [key for key, value in storage.get_run_tags(tag_keys=[run_id])]
        storage.delete_run(run_id)
        assert list(storage.get_runs()) == []
        assert run_id not in [key for key, value in storage.get_run_tags(tag_keys=[run_id])]

    def test_wipe_tags(self, storage: RunStorage):
        if not self.can_delete_runs():
            pytest.skip("storage cannot delete")

        run_id = "some_run_id"
        run = DagsterRun(run_id=run_id, job_name="a_pipeline", tags={"foo": "bar"})

        storage.add_run(run)

        assert _get_run_by_id(storage, run_id) == run
        assert dict(storage.get_run_tags(tag_keys=["foo"])) == {"foo": {"bar"}}

        storage.wipe()
        assert list(storage.get_runs()) == []
        assert dict(storage.get_run_tags(tag_keys=["foo"])) == {}

    def test_write_conflicting_run_id(self, storage: RunStorage):
        double_run_id = "double_run_id"
        job_def = GraphDefinition(name="some_pipeline", node_defs=[]).to_job()

        run = DagsterRun(run_id=double_run_id, job_name=job_def.name)

        assert storage.add_run(run)
        with pytest.raises(DagsterRunAlreadyExists):
            storage.add_run(run)

    def test_add_get_snapshot(self, storage):
        job_def = GraphDefinition(name="some_pipeline", node_defs=[]).to_job()
        job_snapshot = job_def.get_job_snapshot()
        job_snapshot_id = create_job_snapshot_id(job_snapshot)

        assert storage.add_job_snapshot(job_snapshot) == job_snapshot_id
        fetch_job_snapshot = storage.get_job_snapshot(job_snapshot_id)
        assert fetch_job_snapshot
        assert serialize_pp(fetch_job_snapshot) == serialize_pp(job_snapshot)
        assert storage.has_job_snapshot(job_snapshot_id)
        assert not storage.has_job_snapshot("nope")

        if self.can_delete_runs():
            storage.wipe()

            assert not storage.has_job_snapshot(job_snapshot_id)

    def test_single_write_read_with_snapshot(self, storage: RunStorage):
        run_with_snapshot_id = "lkasjdflkjasdf"
        job_def = GraphDefinition(name="some_pipeline", node_defs=[]).to_job()

        job_snapshot = job_def.get_job_snapshot()

        job_snapshot_id = create_job_snapshot_id(job_snapshot)

        run_with_snapshot = DagsterRun(
            run_id=run_with_snapshot_id,
            job_name=job_def.name,
            job_snapshot_id=job_snapshot_id,
        )

        assert not storage.has_job_snapshot(job_snapshot_id)

        assert storage.add_job_snapshot(job_snapshot) == job_snapshot_id

        assert serialize_pp(storage.get_job_snapshot(job_snapshot_id)) == serialize_pp(job_snapshot)

        storage.add_run(run_with_snapshot)

        assert _get_run_by_id(storage, run_with_snapshot_id) == run_with_snapshot

        if self.can_delete_runs():
            storage.wipe()

            assert not storage.has_job_snapshot(job_snapshot_id)
            assert not storage.has_run(run_with_snapshot_id)

    def test_single_write_with_missing_snapshot(self, storage: RunStorage):
        run_with_snapshot_id = "lkasjdflkjasdf"
        job_def = GraphDefinition(name="some_pipeline", node_defs=[]).to_job()

        run_with_missing_snapshot = DagsterRun(
            run_id=run_with_snapshot_id,
            job_name=job_def.name,
            job_snapshot_id="nope",
        )

        with pytest.raises(DagsterSnapshotDoesNotExist):
            storage.add_run(run_with_missing_snapshot)

    def test_add_get_execution_snapshot(self, storage: RunStorage):
        from dagster._core.execution.api import create_execution_plan
        from dagster._core.snap import snapshot_from_execution_plan

        job_def = GraphDefinition(name="some_pipeline", node_defs=[]).to_job()
        execution_plan = create_execution_plan(job_def)
        ep_snapshot = snapshot_from_execution_plan(execution_plan, job_def.get_job_snapshot_id())

        snapshot_id = storage.add_execution_plan_snapshot(ep_snapshot)
        fetched_ep_snapshot = storage.get_execution_plan_snapshot(snapshot_id)

        # idempotent
        assert storage.add_execution_plan_snapshot(ep_snapshot) == snapshot_id

        assert fetched_ep_snapshot
        assert serialize_pp(fetched_ep_snapshot) == serialize_pp(ep_snapshot)
        assert storage.has_execution_plan_snapshot(snapshot_id)
        assert not storage.has_execution_plan_snapshot("nope")

        if self.can_delete_runs():
            storage.wipe()

            assert not storage.has_execution_plan_snapshot(snapshot_id)

    def test_fetch_run_filter(self, storage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()

        storage.add_run(
            TestRunStorage.build_run(
                run_id=one,
                job_name="some_pipeline",
                status=DagsterRunStatus.SUCCESS,
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two,
                job_name="some_pipeline",
                status=DagsterRunStatus.SUCCESS,
            ),
        )

        assert len(storage.get_runs()) == 2

        some_runs = storage.get_runs(RunsFilter(run_ids=[one, two]))
        count = storage.get_runs_count(RunsFilter(run_ids=[one, two]))
        assert len(some_runs) == 2
        assert count == 2

    def test_fetch_run_group(self, storage: RunStorage):
        assert storage
        root_run = TestRunStorage.build_run(run_id=make_new_run_id(), job_name="foo_job")
        runs = [root_run]

        # Create 3 children and 3 descendants of the rightmost child:
        #    root
        #   /  |  \
        # [0] [1] [2]
        #          |
        #         [a]
        #          |
        #         [b]
        #          |
        #         [c]

        for _ in range(3):
            runs.append(
                TestRunStorage.build_run(
                    run_id=make_new_run_id(),
                    job_name="foo_job",
                    root_run_id=root_run.run_id,
                    parent_run_id=root_run.run_id,
                    tags={PARENT_RUN_ID_TAG: root_run.run_id, ROOT_RUN_ID_TAG: root_run.run_id},
                )
            )
        for _ in range(3):
            # get root run id from the previous run if exists, otherwise use previous run's id
            root_run_id = runs[-1].root_run_id if runs[-1].root_run_id else runs[-1].run_id
            parent_run_id = runs[-1].run_id
            runs.append(
                TestRunStorage.build_run(
                    run_id=make_new_run_id(),
                    job_name="foo_job",
                    root_run_id=root_run_id,
                    parent_run_id=parent_run_id,
                    tags={PARENT_RUN_ID_TAG: parent_run_id, ROOT_RUN_ID_TAG: root_run_id},
                )
            )
        for run in runs:
            storage.add_run(run)

        run_group_one = storage.get_run_group(root_run.run_id)
        assert run_group_one

        assert len(run_group_one[1]) == 7

        run_group_two = storage.get_run_group(runs[-1].run_id)
        assert run_group_two

        assert len(run_group_two[1]) == 7

        # The order of runs in each run run group is not deterministic
        unittest.TestCase().assertCountEqual(run_group_one[0], run_group_two[0])
        unittest.TestCase().assertCountEqual(run_group_one[1], run_group_two[1])

    def test_fetch_run_group_not_found(self, storage: RunStorage):
        assert storage
        run = TestRunStorage.build_run(run_id=make_new_run_id(), job_name="foo_job")
        storage.add_run(run)

        with pytest.raises(DagsterRunNotFoundError):
            storage.get_run_group(make_new_run_id())

    def test_partition_status(self, storage: RunStorage):
        one = TestRunStorage.build_run(
            run_id=make_new_run_id(),
            job_name="foo_job",
            status=DagsterRunStatus.FAILURE,
            tags={
                PARTITION_NAME_TAG: "one",
                PARTITION_SET_TAG: "foo_set",
            },
        )
        storage.add_run(one)
        two = TestRunStorage.build_run(
            run_id=make_new_run_id(),
            job_name="foo_job",
            status=DagsterRunStatus.FAILURE,
            tags={
                PARTITION_NAME_TAG: "two",
                PARTITION_SET_TAG: "foo_set",
            },
        )
        storage.add_run(two)
        two_retried = TestRunStorage.build_run(
            run_id=make_new_run_id(),
            job_name="foo_job",
            status=DagsterRunStatus.SUCCESS,
            tags={
                PARTITION_NAME_TAG: "two",
                PARTITION_SET_TAG: "foo_set",
            },
        )
        storage.add_run(two_retried)
        three = TestRunStorage.build_run(
            run_id=make_new_run_id(),
            job_name="foo_job",
            status=DagsterRunStatus.SUCCESS,
            tags={
                PARTITION_NAME_TAG: "three",
                PARTITION_SET_TAG: "foo_set",
            },
        )
        storage.add_run(three)
        wrong_job = TestRunStorage.build_run(
            run_id=make_new_run_id(),
            job_name="bar_job",
            status=DagsterRunStatus.SUCCESS,
            tags={
                PARTITION_NAME_TAG: "ignorable",
                PARTITION_SET_TAG: "foo_set",
            },
        )
        storage.add_run(wrong_job)
        partition_data = storage.get_run_partition_data(
            runs_filter=RunsFilter(
                job_name="foo_job",
                tags={PARTITION_SET_TAG: "foo_set"},
            )
        )
        assert len(partition_data) == 3
        assert {_.partition for _ in partition_data} == {"one", "two", "three"}
        assert {_.run_id for _ in partition_data} == {one.run_id, two_retried.run_id, three.run_id}

    def _skip_in_memory(self, storage):
        from dagster._core.storage.runs import InMemoryRunStorage

        if isinstance(storage, InMemoryRunStorage):
            pytest.skip()

    def test_empty_heartbeat(self, storage):
        self._skip_in_memory(storage)

        assert storage.get_daemon_heartbeats() == {}

    def test_add_heartbeat(self, storage):
        self._skip_in_memory(storage)

        # test insert
        added_heartbeat = DaemonHeartbeat(
            timestamp=pendulum.from_timestamp(1000).float_timestamp,
            daemon_type=SensorDaemon.daemon_type(),
            daemon_id=None,
            errors=[],
        )
        storage.add_daemon_heartbeat(added_heartbeat)
        assert len(storage.get_daemon_heartbeats()) == 1
        stored_heartbeat = storage.get_daemon_heartbeats()[SensorDaemon.daemon_type()]
        assert stored_heartbeat == added_heartbeat

        # test update
        second_added_heartbeat = DaemonHeartbeat(
            timestamp=pendulum.from_timestamp(2000).float_timestamp,
            daemon_type=SensorDaemon.daemon_type(),
            daemon_id=None,
            errors=[],
        )
        storage.add_daemon_heartbeat(second_added_heartbeat)
        assert len(storage.get_daemon_heartbeats()) == 1
        stored_heartbeat = storage.get_daemon_heartbeats()[SensorDaemon.daemon_type()]
        assert stored_heartbeat == second_added_heartbeat

    def test_wipe_heartbeats(self, storage: RunStorage):
        self._skip_in_memory(storage)

        if not self.can_delete_runs():
            pytest.skip("storage cannot delete")

        added_heartbeat = DaemonHeartbeat(
            timestamp=pendulum.from_timestamp(1000).float_timestamp,
            daemon_type=SensorDaemon.daemon_type(),
            daemon_id=None,
            errors=[],
        )
        storage.add_daemon_heartbeat(added_heartbeat)
        storage.wipe_daemon_heartbeats()

    def test_backfill(self, storage: RunStorage):
        origin = self.fake_partition_set_origin("fake_partition_set")
        backfills = storage.get_backfills()
        assert len(backfills) == 0

        one = PartitionBackfill(
            "one",
            partition_set_origin=origin,
            status=BulkActionStatus.REQUESTED,
            partition_names=["a", "b", "c"],
            from_failure=False,
            tags={},
            backfill_timestamp=pendulum.now().timestamp(),
        )
        storage.add_backfill(one)
        assert len(storage.get_backfills()) == 1
        assert len(storage.get_backfills(status=BulkActionStatus.REQUESTED)) == 1
        backfill = storage.get_backfill(one.backfill_id)
        assert backfill == one

        storage.update_backfill(one.with_status(status=BulkActionStatus.COMPLETED))
        assert len(storage.get_backfills()) == 1
        assert len(storage.get_backfills(status=BulkActionStatus.REQUESTED)) == 0

    def test_secondary_index(self, storage):
        self._skip_in_memory(storage)

        if not isinstance(storage, SqlRunStorage):
            return

        for name in REQUIRED_DATA_MIGRATIONS.keys():
            assert storage.has_built_index(name)

    def test_handle_run_event_job_success_test(self, storage):
        run_id = make_new_run_id()
        run_to_add = TestRunStorage.build_run(job_name="pipeline_name", run_id=run_id)
        storage.add_run(run_to_add)

        dagster_job_start_event = DagsterEvent(
            message="a message",
            event_type_value=DagsterEventType.PIPELINE_START.value,
            job_name="pipeline_name",
            step_key=None,
            node_handle=None,
            step_kind_value=None,
            logging_tags=None,
        )

        storage.handle_run_event(run_id, dagster_job_start_event)

        assert _get_run_by_id(storage, run_id).status == DagsterRunStatus.STARTED

        storage.handle_run_event(
            make_new_run_id(),  # diff run
            DagsterEvent(
                message="a message",
                event_type_value=DagsterEventType.PIPELINE_SUCCESS.value,
                job_name="pipeline_name",
                step_key=None,
                node_handle=None,
                step_kind_value=None,
                logging_tags=None,
            ),
        )

        assert _get_run_by_id(storage, run_id).status == DagsterRunStatus.STARTED

        storage.handle_run_event(
            run_id,  # correct run
            DagsterEvent(
                message="a message",
                event_type_value=DagsterEventType.PIPELINE_SUCCESS.value,
                job_name="pipeline_name",
                step_key=None,
                node_handle=None,
                step_kind_value=None,
                logging_tags=None,
            ),
        )

        assert _get_run_by_id(storage, run_id).status == DagsterRunStatus.SUCCESS

    def test_debug_snapshot_import(self, storage):
        from dagster._core.execution.api import create_execution_plan
        from dagster._core.snap import (
            create_execution_plan_snapshot_id,
            snapshot_from_execution_plan,
        )

        run_id = make_new_run_id()
        run_to_add = TestRunStorage.build_run(job_name="pipeline_name", run_id=run_id)
        storage.add_run(run_to_add)

        job_def = GraphDefinition(name="some_pipeline", node_defs=[]).to_job()

        job_snapshot = job_def.get_job_snapshot()
        job_snapshot_id = create_job_snapshot_id(job_snapshot)
        new_job_snapshot_id = f"{job_snapshot_id}-new-snapshot"

        storage.add_snapshot(job_snapshot, snapshot_id=new_job_snapshot_id)
        assert not storage.has_snapshot(job_snapshot_id)
        assert storage.has_snapshot(new_job_snapshot_id)

        execution_plan = create_execution_plan(job_def)
        ep_snapshot = snapshot_from_execution_plan(execution_plan, new_job_snapshot_id)
        ep_snapshot_id = create_execution_plan_snapshot_id(ep_snapshot)
        new_ep_snapshot_id = f"{ep_snapshot_id}-new-snapshot"

        storage.add_snapshot(ep_snapshot, snapshot_id=new_ep_snapshot_id)
        assert not storage.has_snapshot(ep_snapshot_id)
        assert storage.has_snapshot(new_ep_snapshot_id)

    def test_run_record_stats(self, storage):
        assert storage

        self._skip_in_memory(storage)

        run_id = make_new_run_id()
        run_to_add = TestRunStorage.build_run(job_name="pipeline_name", run_id=run_id)

        storage.add_run(run_to_add)

        run_record = storage.get_run_records(RunsFilter(run_ids=[run_id]))[0]

        assert run_record.start_time is None
        assert run_record.end_time is None

        storage.handle_run_event(
            run_id,
            DagsterEvent(
                message="a message",
                event_type_value=DagsterEventType.PIPELINE_START.value,
                job_name="pipeline_name",
            ),
        )

        run_record = storage.get_run_records(RunsFilter(run_ids=[run_id]))[0]

        assert run_record.start_time is not None
        assert run_record.end_time is None

        storage.handle_run_event(
            run_id,
            DagsterEvent(
                message="a message",
                event_type_value=DagsterEventType.PIPELINE_SUCCESS.value,
                job_name="pipeline_name",
            ),
        )

        run_record = storage.get_run_records(RunsFilter(run_ids=[run_id]))[0]

        assert run_record.start_time is not None
        assert run_record.end_time is not None
        assert run_record.end_time >= run_record.start_time

    def test_run_record_timestamps(self, storage):
        assert storage

        self._skip_in_memory(storage)

        @op
        def a():
            pass

        @job
        def my_job():
            a()

        with tempfile.TemporaryDirectory() as temp_dir:
            if storage.has_instance:
                instance = storage._instance  # noqa: SLF001
            else:
                instance = DagsterInstance(
                    instance_type=InstanceType.EPHEMERAL,
                    local_artifact_storage=LocalArtifactStorage(temp_dir),
                    run_storage=storage,
                    event_storage=InMemoryEventLogStorage(),
                    compute_log_manager=NoOpComputeLogManager(),
                    run_coordinator=DefaultRunCoordinator(),
                    run_launcher=SyncInMemoryRunLauncher(),
                )

            freeze_datetime = to_timezone(
                create_pendulum_time(2019, 11, 2, 0, 0, 0, tz="US/Central"), "US/Pacific"
            )

            with pendulum_freeze_time(freeze_datetime):
                result = my_job.execute_in_process(instance=instance)
                records = instance.get_run_records(filters=RunsFilter(run_ids=[result.run_id]))
                assert len(records) == 1
                record = records[0]
                assert record.start_time == freeze_datetime.timestamp()
                assert record.end_time == freeze_datetime.timestamp()

    def test_migrate_repo(self, storage):
        assert storage
        self._skip_in_memory(storage)

        one = make_new_run_id()
        two = make_new_run_id()
        job_name = "some_job"

        origin_one = self.fake_job_origin(job_name, "fake_repo_one")
        origin_two = self.fake_job_origin(job_name, "fake_repo_two")
        storage.add_run(
            TestRunStorage.build_run(run_id=one, job_name=job_name, external_job_origin=origin_one)
        )
        storage.add_run(
            TestRunStorage.build_run(run_id=two, job_name=job_name, external_job_origin=origin_one)
        )

        one_runs = storage.get_runs(
            RunsFilter(tags={REPOSITORY_LABEL_TAG: "fake_repo_one@fake:fake"})
        )
        assert len(one_runs) == 2
        two_runs = storage.get_runs(
            RunsFilter(tags={REPOSITORY_LABEL_TAG: "fake_repo_two@fake:fake"})
        )
        assert len(two_runs) == 0

        # replace job origin for run one
        storage.replace_job_origin(one_runs[1], origin_two)

        one_runs = storage.get_runs(
            RunsFilter(tags={REPOSITORY_LABEL_TAG: "fake_repo_one@fake:fake"})
        )
        assert len(one_runs) == 1
        two_runs = storage.get_runs(
            RunsFilter(tags={REPOSITORY_LABEL_TAG: "fake_repo_two@fake:fake"})
        )
        assert len(two_runs) == 1
        assert two_runs[0].run_id == one
