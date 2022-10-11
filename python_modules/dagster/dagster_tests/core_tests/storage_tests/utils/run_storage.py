import sys
import tempfile
from datetime import datetime

import pendulum
import pytest

from dagster import _seven, job, op
from dagster._core.definitions import PipelineDefinition
from dagster._core.errors import (
    DagsterRunAlreadyExists,
    DagsterRunNotFoundError,
    DagsterSnapshotDoesNotExist,
)
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.host_representation import (
    ExternalRepositoryOrigin,
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
)
from dagster._core.instance import DagsterInstance, InstanceType
from dagster._core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster._core.run_coordinator import DefaultRunCoordinator
from dagster._core.snap import create_pipeline_snapshot_id
from dagster._core.storage.event_log import InMemoryEventLogStorage
from dagster._core.storage.noop_compute_log_manager import NoOpComputeLogManager
from dagster._core.storage.pipeline_run import (
    DagsterRun,
    JobBucket,
    PipelineRunStatus,
    RunsFilter,
    TagBucket,
)
from dagster._core.storage.root import LocalArtifactStorage
from dagster._core.storage.runs.migration import REQUIRED_DATA_MIGRATIONS
from dagster._core.storage.runs.sql_run_storage import SqlRunStorage
from dagster._core.storage.tags import (
    PARENT_RUN_ID_TAG,
    PARTITION_NAME_TAG,
    PARTITION_SET_TAG,
    REPOSITORY_LABEL_TAG,
    ROOT_RUN_ID_TAG,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.utils import make_new_run_id
from dagster._daemon.daemon import SensorDaemon
from dagster._daemon.types import DaemonHeartbeat
from dagster._serdes import serialize_pp
from dagster._seven.compat.pendulum import create_pendulum_time, to_timezone

win_py36 = _seven.IS_WINDOWS and sys.version_info[0] == 3 and sys.version_info[1] == 6


class TestRunStorage:
    """
    You can extend this class to easily run these set of tests on any run storage. When extending,
    you simply need to override the `run_storage` fixture and return your implementation of
    `RunStorage`.

    For example:

    ```
    class TestMyStorageImplementation(TestRunStorage):
        __test__ = True

        @pytest.fixture(scope='function', name='storage')
        def run_storage(self):  # pylint: disable=arguments-differ
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
            ManagedGrpcPythonEnvRepositoryLocationOrigin(
                LoadableTargetOrigin(
                    executable_path=sys.executable, module_name="fake", attribute="fake"
                ),
            ),
            name,
        )

    @classmethod
    def fake_job_origin(cls, job_name, repo_name=None):
        return cls.fake_repo_target(repo_name).get_pipeline_origin(job_name)

    @classmethod
    def fake_partition_set_origin(cls, partition_set_name):
        return cls.fake_repo_target().get_partition_set_origin(partition_set_name)

    @staticmethod
    def build_run(
        run_id,
        pipeline_name,
        mode="default",
        tags=None,
        status=PipelineRunStatus.NOT_STARTED,
        parent_run_id=None,
        root_run_id=None,
        pipeline_snapshot_id=None,
        external_pipeline_origin=None,
    ):
        return DagsterRun(
            pipeline_name=pipeline_name,
            run_id=run_id,
            run_config=None,
            mode=mode,
            tags=tags,
            status=status,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            pipeline_snapshot_id=pipeline_snapshot_id,
            external_pipeline_origin=external_pipeline_origin,
        )

    def test_basic_storage(self, storage):
        assert storage
        run_id = make_new_run_id()
        added = storage.add_run(
            TestRunStorage.build_run(
                run_id=run_id, pipeline_name="some_pipeline", tags={"foo": "bar"}
            )
        )
        assert added
        runs = storage.get_runs()
        assert len(runs) == 1
        run = runs[0]
        assert run.run_id == run_id
        assert run.pipeline_name == "some_pipeline"
        assert run.tags
        assert run.tags.get("foo") == "bar"
        assert storage.has_run(run_id)
        fetched_run = storage.get_run_by_id(run_id)
        assert fetched_run.run_id == run_id
        assert fetched_run.pipeline_name == "some_pipeline"

    def test_clear(self, storage):
        if not self.can_delete_runs():
            pytest.skip("storage cannot delete")

        assert storage
        run_id = make_new_run_id()
        storage.add_run(TestRunStorage.build_run(run_id=run_id, pipeline_name="some_pipeline"))
        assert len(storage.get_runs()) == 1
        storage.wipe()
        assert list(storage.get_runs()) == []

    def test_storage_telemetry(self, storage):
        assert storage
        storage_id = storage.get_run_storage_id()
        assert isinstance(storage_id, str)
        storage_id_again = storage.get_run_storage_id()
        assert storage_id == storage_id_again

    def test_fetch_by_pipeline(self, storage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()
        storage.add_run(TestRunStorage.build_run(run_id=one, pipeline_name="some_pipeline"))
        storage.add_run(TestRunStorage.build_run(run_id=two, pipeline_name="some_other_pipeline"))
        assert len(storage.get_runs()) == 2
        some_runs = storage.get_runs(RunsFilter(pipeline_name="some_pipeline"))
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
            TestRunStorage.build_run(
                run_id=one, pipeline_name=job_name, external_pipeline_origin=origin_one
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two, pipeline_name=job_name, external_pipeline_origin=origin_two
            )
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
        pipeline_def_a = PipelineDefinition(name="some_pipeline", solid_defs=[])
        pipeline_def_b = PipelineDefinition(name="some_other_pipeline", solid_defs=[])
        pipeline_snapshot_a = pipeline_def_a.get_pipeline_snapshot()
        pipeline_snapshot_b = pipeline_def_b.get_pipeline_snapshot()
        pipeline_snapshot_a_id = create_pipeline_snapshot_id(pipeline_snapshot_a)
        pipeline_snapshot_b_id = create_pipeline_snapshot_id(pipeline_snapshot_b)

        assert storage.add_pipeline_snapshot(pipeline_snapshot_a) == pipeline_snapshot_a_id
        assert storage.add_pipeline_snapshot(pipeline_snapshot_b) == pipeline_snapshot_b_id

        one = make_new_run_id()
        two = make_new_run_id()
        storage.add_run(
            TestRunStorage.build_run(
                run_id=one,
                pipeline_name="some_pipeline",
                pipeline_snapshot_id=pipeline_snapshot_a_id,
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two,
                pipeline_name="some_other_pipeline",
                pipeline_snapshot_id=pipeline_snapshot_b_id,
            )
        )
        assert len(storage.get_runs()) == 2
        runs_a = storage.get_runs(RunsFilter(snapshot_id=pipeline_snapshot_a_id))
        assert len(runs_a) == 1
        assert runs_a[0].run_id == one

        runs_b = storage.get_runs(RunsFilter(snapshot_id=pipeline_snapshot_b_id))
        assert len(runs_b) == 1
        assert runs_b[0].run_id == two

    def test_add_run_tags(self, storage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()

        storage.add_run(TestRunStorage.build_run(run_id=one, pipeline_name="foo"))
        storage.add_run(TestRunStorage.build_run(run_id=two, pipeline_name="bar"))

        assert storage.get_run_tags() == []

        storage.add_run_tags(one, {"tag1": "val1", "tag2": "val2"})
        storage.add_run_tags(two, {"tag1": "val1"})

        assert storage.get_run_tags() == [("tag1", {"val1"}), ("tag2", {"val2"})]

        # Adding both existing tags and a new tag
        storage.add_run_tags(one, {"tag1": "val2", "tag3": "val3"})

        test_run = storage.get_run_by_id(one)

        assert len(test_run.tags) == 3
        assert test_run.tags["tag1"] == "val2"
        assert test_run.tags["tag2"] == "val2"
        assert test_run.tags["tag3"] == "val3"

        assert storage.get_run_tags() == [
            ("tag1", {"val1", "val2"}),
            ("tag2", {"val2"}),
            ("tag3", {"val3"}),
        ]

        # Adding only existing tags
        storage.add_run_tags(one, {"tag1": "val3"})

        test_run = storage.get_run_by_id(one)

        assert len(test_run.tags) == 3
        assert test_run.tags["tag1"] == "val3"
        assert test_run.tags["tag2"] == "val2"
        assert test_run.tags["tag3"] == "val3"

        assert storage.get_run_tags() == [
            ("tag1", {"val1", "val3"}),
            ("tag2", {"val2"}),
            ("tag3", {"val3"}),
        ]

        # Adding only a new tag that wasn't there before
        storage.add_run_tags(one, {"tag4": "val4"})

        test_run = storage.get_run_by_id(one)

        assert len(test_run.tags) == 4
        assert test_run.tags["tag1"] == "val3"
        assert test_run.tags["tag2"] == "val2"
        assert test_run.tags["tag3"] == "val3"
        assert test_run.tags["tag4"] == "val4"

        assert storage.get_run_tags() == [
            ("tag1", {"val1", "val3"}),
            ("tag2", {"val2"}),
            ("tag3", {"val3"}),
            ("tag4", {"val4"}),
        ]

        test_run = storage.get_run_by_id(one)
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

    def test_fetch_by_filter(self, storage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()
        three = make_new_run_id()
        four = make_new_run_id()

        storage.add_run(
            TestRunStorage.build_run(
                run_id=one,
                pipeline_name="some_pipeline",
                tags={"tag": "hello", "tag2": "world"},
                status=PipelineRunStatus.SUCCESS,
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two,
                pipeline_name="some_pipeline",
                tags={"tag": "hello"},
                status=PipelineRunStatus.FAILURE,
            ),
        )

        storage.add_run(
            TestRunStorage.build_run(
                run_id=three, pipeline_name="other_pipeline", status=PipelineRunStatus.SUCCESS
            )
        )

        storage.add_run(
            TestRunStorage.build_run(
                run_id=four,
                pipeline_name="some_other_pipeline",
                tags={"tag": "goodbye"},
                status=PipelineRunStatus.FAILURE,
            ),
        )

        assert len(storage.get_runs()) == 4

        some_runs = storage.get_runs(RunsFilter(run_ids=[one]))
        count = storage.get_runs_count(RunsFilter(run_ids=[one]))
        assert len(some_runs) == 1
        assert count == 1
        assert some_runs[0].run_id == one

        some_runs = storage.get_runs(RunsFilter(pipeline_name="some_pipeline"))
        count = storage.get_runs_count(RunsFilter(pipeline_name="some_pipeline"))
        assert len(some_runs) == 2
        assert count == 2
        assert some_runs[0].run_id == two
        assert some_runs[1].run_id == one

        some_runs = storage.get_runs(RunsFilter(statuses=[PipelineRunStatus.SUCCESS]))
        count = storage.get_runs_count(RunsFilter(statuses=[PipelineRunStatus.SUCCESS]))
        assert len(some_runs) == 2
        assert count == 2
        assert some_runs[0].run_id == three
        assert some_runs[1].run_id == one

        some_runs = storage.get_runs(RunsFilter(tags={"tag": "hello"}))
        count = storage.get_runs_count(RunsFilter(tags={"tag": "hello"}))
        assert len(some_runs) == 2
        assert count == 2
        assert some_runs[0].run_id == two
        assert some_runs[1].run_id == one

        some_runs = storage.get_runs(RunsFilter(tags={"tag": "hello", "tag2": "world"}))
        count = storage.get_runs_count(RunsFilter(tags={"tag": "hello", "tag2": "world"}))
        assert len(some_runs) == 1
        assert count == 1
        assert some_runs[0].run_id == one

        some_runs = storage.get_runs(
            RunsFilter(pipeline_name="some_pipeline", tags={"tag": "hello"})
        )
        count = storage.get_runs_count(
            RunsFilter(pipeline_name="some_pipeline", tags={"tag": "hello"})
        )
        assert len(some_runs) == 2
        assert count == 2
        assert some_runs[0].run_id == two
        assert some_runs[1].run_id == one

        runs_with_multiple_tag_values = storage.get_runs(
            RunsFilter(tags={"tag": ["hello", "goodbye", "farewell"]})
        )
        assert len(runs_with_multiple_tag_values) == 3
        assert runs_with_multiple_tag_values[0].run_id == four
        assert runs_with_multiple_tag_values[1].run_id == two
        assert runs_with_multiple_tag_values[2].run_id == one

        count_with_multiple_tag_values = storage.get_runs_count(
            RunsFilter(tags={"tag": ["hello", "goodbye", "farewell"]})
        )
        assert count_with_multiple_tag_values == 3

        some_runs = storage.get_runs(
            RunsFilter(
                pipeline_name="some_pipeline",
                tags={"tag": "hello"},
                statuses=[PipelineRunStatus.SUCCESS],
            )
        )
        count = storage.get_runs_count(
            RunsFilter(
                pipeline_name="some_pipeline",
                tags={"tag": "hello"},
                statuses=[PipelineRunStatus.SUCCESS],
            )
        )
        assert len(some_runs) == 1
        assert count == 1
        assert some_runs[0].run_id == one

        # All filters
        some_runs = storage.get_runs(
            RunsFilter(
                run_ids=[one],
                pipeline_name="some_pipeline",
                tags={"tag": "hello"},
                statuses=[PipelineRunStatus.SUCCESS],
            )
        )
        count = storage.get_runs_count(
            RunsFilter(
                run_ids=[one],
                pipeline_name="some_pipeline",
                tags={"tag": "hello"},
                statuses=[PipelineRunStatus.SUCCESS],
            )
        )
        assert len(some_runs) == 1
        assert count == 1
        assert some_runs[0].run_id == one

        some_runs = storage.get_runs(RunsFilter())
        count = storage.get_runs_count(RunsFilter())
        assert len(some_runs) == 4
        assert count == 4

    def test_fetch_count_by_tag(self, storage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()
        three = make_new_run_id()
        storage.add_run(
            TestRunStorage.build_run(
                run_id=one,
                pipeline_name="some_pipeline",
                tags={"mytag": "hello", "mytag2": "world"},
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two,
                pipeline_name="some_pipeline",
                tags={"mytag": "goodbye", "mytag2": "world"},
            )
        )
        storage.add_run(TestRunStorage.build_run(run_id=three, pipeline_name="some_pipeline"))
        assert len(storage.get_runs()) == 3

        run_count = storage.get_runs_count(
            filters=RunsFilter(tags={"mytag": "hello", "mytag2": "world"})
        )
        assert run_count == 1

        run_count = storage.get_runs_count(filters=RunsFilter(tags={"mytag2": "world"}))
        assert run_count == 2

        run_count = storage.get_runs_count()
        assert run_count == 3

        assert storage.get_run_tags() == [("mytag", {"hello", "goodbye"}), ("mytag2", {"world"})]

    def test_fetch_by_tags(self, storage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()
        three = make_new_run_id()
        storage.add_run(
            TestRunStorage.build_run(
                run_id=one,
                pipeline_name="some_pipeline",
                tags={"mytag": "hello", "mytag2": "world"},
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two,
                pipeline_name="some_pipeline",
                tags={"mytag": "goodbye", "mytag2": "world"},
            )
        )
        storage.add_run(TestRunStorage.build_run(run_id=three, pipeline_name="some_pipeline"))
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
            TestRunStorage.build_run(
                run_id=one, pipeline_name="some_pipeline", tags={"mytag": "hello"}
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two, pipeline_name="some_pipeline", tags={"mytag": "hello"}
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=three, pipeline_name="some_pipeline", tags={"mytag": "hello"}
            )
        )

        all_runs = storage.get_runs()
        assert len(all_runs) == 3
        sliced_runs = storage.get_runs(cursor=three, limit=1)
        assert len(sliced_runs) == 1
        assert sliced_runs[0].run_id == two

        all_runs = storage.get_runs(RunsFilter(pipeline_name="some_pipeline"))
        assert len(all_runs) == 3
        sliced_runs = storage.get_runs(
            RunsFilter(pipeline_name="some_pipeline"), cursor=three, limit=1
        )
        assert len(sliced_runs) == 1
        assert sliced_runs[0].run_id == two

        all_runs = storage.get_runs(RunsFilter(tags={"mytag": "hello"}))
        assert len(all_runs) == 3
        sliced_runs = storage.get_runs(RunsFilter(tags={"mytag": "hello"}), cursor=three, limit=1)
        assert len(sliced_runs) == 1
        assert sliced_runs[0].run_id == two

    def test_fetch_by_status(self, storage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()
        three = make_new_run_id()
        four = make_new_run_id()
        storage.add_run(
            TestRunStorage.build_run(
                run_id=one, pipeline_name="some_pipeline", status=PipelineRunStatus.NOT_STARTED
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two, pipeline_name="some_pipeline", status=PipelineRunStatus.STARTED
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=three, pipeline_name="some_pipeline", status=PipelineRunStatus.STARTED
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=four, pipeline_name="some_pipeline", status=PipelineRunStatus.FAILURE
            )
        )

        assert {
            run.run_id
            for run in storage.get_runs(RunsFilter(statuses=[PipelineRunStatus.NOT_STARTED]))
        } == {one}

        assert {
            run.run_id for run in storage.get_runs(RunsFilter(statuses=[PipelineRunStatus.STARTED]))
        } == {
            two,
            three,
        }

        assert {
            run.run_id for run in storage.get_runs(RunsFilter(statuses=[PipelineRunStatus.FAILURE]))
        } == {four}

        assert {
            run.run_id for run in storage.get_runs(RunsFilter(statuses=[PipelineRunStatus.SUCCESS]))
        } == set()

    def test_fetch_records_by_update_timestamp(self, storage):
        assert storage
        self._skip_in_memory(storage)

        one = make_new_run_id()
        two = make_new_run_id()
        three = make_new_run_id()
        storage.add_run(
            TestRunStorage.build_run(
                run_id=one, pipeline_name="some_pipeline", status=PipelineRunStatus.STARTED
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two, pipeline_name="some_pipeline", status=PipelineRunStatus.FAILURE
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=three, pipeline_name="some_pipeline", status=PipelineRunStatus.STARTED
            )
        )
        storage.handle_run_event(
            three,  # three succeeds
            DagsterEvent(
                message="a message",
                event_type_value=DagsterEventType.PIPELINE_SUCCESS.value,
                pipeline_name="some_pipeline",
            ),
        )
        storage.handle_run_event(
            one,  # fail one after two has fails and three has succeeded
            DagsterEvent(
                message="a message",
                event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
                pipeline_name="some_pipeline",
            ),
        )

        record_two = storage.get_run_records(
            filters=RunsFilter(run_ids=[two], updated_after=datetime(2020, 1, 1))
        )[0]
        run_two_update_timestamp = record_two.update_timestamp

        assert [
            record.pipeline_run.run_id
            for record in storage.get_run_records(
                filters=RunsFilter(updated_after=run_two_update_timestamp),
                order_by="update_timestamp",
                ascending=True,
            )
        ] == [three, one]

        assert [
            record.pipeline_run.run_id
            for record in storage.get_run_records(
                filters=RunsFilter(
                    statuses=[PipelineRunStatus.FAILURE], updated_after=run_two_update_timestamp
                ),
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
                run_id=one, pipeline_name="some_pipeline", status=PipelineRunStatus.STARTED
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two, pipeline_name="some_pipeline", status=PipelineRunStatus.STARTED
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=three, pipeline_name="some_pipeline", status=PipelineRunStatus.NOT_STARTED
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=four, pipeline_name="some_pipeline", status=PipelineRunStatus.STARTED
            )
        )

        cursor_four_runs = storage.get_runs(
            RunsFilter(statuses=[PipelineRunStatus.STARTED]), cursor=four
        )
        assert len(cursor_four_runs) == 2
        assert {run.run_id for run in cursor_four_runs} == {one, two}

        cursor_two_runs = storage.get_runs(
            RunsFilter(statuses=[PipelineRunStatus.STARTED]), cursor=two
        )
        assert len(cursor_two_runs) == 1
        assert {run.run_id for run in cursor_two_runs} == {one}

        cursor_one_runs = storage.get_runs(
            RunsFilter(statuses=[PipelineRunStatus.STARTED]), cursor=one
        )
        assert not cursor_one_runs

        cursor_four_limit_one = storage.get_runs(
            RunsFilter(statuses=[PipelineRunStatus.STARTED]), cursor=four, limit=1
        )
        assert len(cursor_four_limit_one) == 1
        assert cursor_four_limit_one[0].run_id == two

    def test_delete(self, storage):
        if not self.can_delete_runs():
            pytest.skip("storage cannot delete runs")

        assert storage
        run_id = make_new_run_id()
        storage.add_run(TestRunStorage.build_run(run_id=run_id, pipeline_name="some_pipeline"))
        assert len(storage.get_runs()) == 1
        storage.delete_run(run_id)
        assert list(storage.get_runs()) == []

    def test_delete_with_tags(self, storage):
        if not self.can_delete_runs():
            pytest.skip("storage cannot delete runs")

        assert storage
        run_id = make_new_run_id()
        storage.add_run(
            TestRunStorage.build_run(
                run_id=run_id,
                pipeline_name="some_pipeline",
                tags={run_id: run_id},
            )
        )
        assert len(storage.get_runs()) == 1
        assert run_id in [key for key, value in storage.get_run_tags()]
        storage.delete_run(run_id)
        assert list(storage.get_runs()) == []
        assert run_id not in [key for key, value in storage.get_run_tags()]

    def test_wipe_tags(self, storage):
        if not self.can_delete_runs():
            pytest.skip("storage cannot delete")

        run_id = "some_run_id"
        run = DagsterRun(run_id=run_id, pipeline_name="a_pipeline", tags={"foo": "bar"})

        storage.add_run(run)

        assert storage.get_run_by_id(run_id) == run
        assert dict(storage.get_run_tags()) == {"foo": {"bar"}}

        storage.wipe()
        assert list(storage.get_runs()) == []
        assert dict(storage.get_run_tags()) == {}

    def test_write_conflicting_run_id(self, storage):
        double_run_id = "double_run_id"
        pipeline_def = PipelineDefinition(name="some_pipeline", solid_defs=[])

        run = DagsterRun(run_id=double_run_id, pipeline_name=pipeline_def.name)

        assert storage.add_run(run)
        with pytest.raises(DagsterRunAlreadyExists):
            storage.add_run(run)

    def test_add_get_snapshot(self, storage):
        pipeline_def = PipelineDefinition(name="some_pipeline", solid_defs=[])
        pipeline_snapshot = pipeline_def.get_pipeline_snapshot()
        pipeline_snapshot_id = create_pipeline_snapshot_id(pipeline_snapshot)

        assert storage.add_pipeline_snapshot(pipeline_snapshot) == pipeline_snapshot_id
        fetched_pipeline_snapshot = storage.get_pipeline_snapshot(pipeline_snapshot_id)
        assert fetched_pipeline_snapshot
        assert serialize_pp(fetched_pipeline_snapshot) == serialize_pp(pipeline_snapshot)
        assert storage.has_pipeline_snapshot(pipeline_snapshot_id)
        assert not storage.has_pipeline_snapshot("nope")

        if self.can_delete_runs():
            storage.wipe()

            assert not storage.has_pipeline_snapshot(pipeline_snapshot_id)

    def test_single_write_read_with_snapshot(self, storage):
        run_with_snapshot_id = "lkasjdflkjasdf"
        pipeline_def = PipelineDefinition(name="some_pipeline", solid_defs=[])

        pipeline_snapshot = pipeline_def.get_pipeline_snapshot()

        pipeline_snapshot_id = create_pipeline_snapshot_id(pipeline_snapshot)

        run_with_snapshot = DagsterRun(
            run_id=run_with_snapshot_id,
            pipeline_name=pipeline_def.name,
            pipeline_snapshot_id=pipeline_snapshot_id,
        )

        assert not storage.has_pipeline_snapshot(pipeline_snapshot_id)

        assert storage.add_pipeline_snapshot(pipeline_snapshot) == pipeline_snapshot_id

        assert serialize_pp(storage.get_pipeline_snapshot(pipeline_snapshot_id)) == serialize_pp(
            pipeline_snapshot
        )

        storage.add_run(run_with_snapshot)

        assert storage.get_run_by_id(run_with_snapshot_id) == run_with_snapshot

        if self.can_delete_runs():
            storage.wipe()

            assert not storage.has_pipeline_snapshot(pipeline_snapshot_id)
            assert not storage.has_run(run_with_snapshot_id)

    def test_single_write_with_missing_snapshot(self, storage):

        run_with_snapshot_id = "lkasjdflkjasdf"
        pipeline_def = PipelineDefinition(name="some_pipeline", solid_defs=[])

        run_with_missing_snapshot = DagsterRun(
            run_id=run_with_snapshot_id,
            pipeline_name=pipeline_def.name,
            pipeline_snapshot_id="nope",
        )

        with pytest.raises(DagsterSnapshotDoesNotExist):
            storage.add_run(run_with_missing_snapshot)

    def test_add_get_execution_snapshot(self, storage):
        from dagster._core.execution.api import create_execution_plan
        from dagster._core.snap import snapshot_from_execution_plan

        pipeline_def = PipelineDefinition(name="some_pipeline", solid_defs=[])
        execution_plan = create_execution_plan(pipeline_def)
        ep_snapshot = snapshot_from_execution_plan(
            execution_plan, pipeline_def.get_pipeline_snapshot_id()
        )

        snapshot_id = storage.add_execution_plan_snapshot(ep_snapshot)
        fetched_ep_snapshot = storage.get_execution_plan_snapshot(snapshot_id)
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
                pipeline_name="some_pipeline",
                status=PipelineRunStatus.SUCCESS,
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two,
                pipeline_name="some_pipeline",
                status=PipelineRunStatus.SUCCESS,
            ),
        )

        assert len(storage.get_runs()) == 2

        some_runs = storage.get_runs(RunsFilter(run_ids=[one, two]))
        count = storage.get_runs_count(RunsFilter(run_ids=[one, two]))
        assert len(some_runs) == 2
        assert count == 2

    def test_fetch_run_group(self, storage):
        assert storage
        root_run = TestRunStorage.build_run(run_id=make_new_run_id(), pipeline_name="foo_pipeline")
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
                    pipeline_name="foo_pipeline",
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
                    pipeline_name="foo_pipeline",
                    root_run_id=root_run_id,
                    parent_run_id=parent_run_id,
                    tags={PARENT_RUN_ID_TAG: parent_run_id, ROOT_RUN_ID_TAG: root_run_id},
                )
            )
        for run in runs:
            storage.add_run(run)

        run_group_one = storage.get_run_group(root_run.run_id)

        assert len(run_group_one[1]) == 7

        run_group_two = storage.get_run_group(runs[-1].run_id)

        assert len(run_group_two[1]) == 7

        assert run_group_one[0] == run_group_two[0]
        assert run_group_one[1] == run_group_two[1]

    def test_fetch_run_group_not_found(self, storage):
        assert storage
        run = TestRunStorage.build_run(run_id=make_new_run_id(), pipeline_name="foo_pipeline")
        storage.add_run(run)

        with pytest.raises(DagsterRunNotFoundError):
            storage.get_run_group(make_new_run_id())

    def test_fetch_run_groups(self, storage):
        assert storage
        root_runs = [
            TestRunStorage.build_run(run_id=make_new_run_id(), pipeline_name="foo_pipeline")
            for i in range(3)
        ]
        runs = [run for run in root_runs]
        for _ in range(5):
            for root_run in root_runs:
                runs.append(
                    TestRunStorage.build_run(
                        run_id=make_new_run_id(),
                        pipeline_name="foo_pipeline",
                        tags={PARENT_RUN_ID_TAG: root_run.run_id, ROOT_RUN_ID_TAG: root_run.run_id},
                    )
                )
        for run in runs:
            storage.add_run(run)

        run_groups = storage.get_run_groups(limit=5)

        assert len(run_groups) == 3

        expected_group_lens = {
            root_runs[i].run_id: expected_len for i, expected_len in enumerate([2, 3, 3])
        }

        for root_run_id in run_groups:
            assert len(run_groups[root_run_id]["runs"]) == expected_group_lens[root_run_id]
            assert run_groups[root_run_id]["count"] == 6

    def test_fetch_run_groups_filter(self, storage):
        assert storage

        root_runs = [
            TestRunStorage.build_run(run_id=make_new_run_id(), pipeline_name="foo_pipeline")
            for i in range(3)
        ]

        runs = [run for run in root_runs]
        for root_run in root_runs:
            failed_run_id = make_new_run_id()
            runs.append(
                TestRunStorage.build_run(
                    run_id=failed_run_id,
                    pipeline_name="foo_pipeline",
                    tags={PARENT_RUN_ID_TAG: root_run.run_id, ROOT_RUN_ID_TAG: root_run.run_id},
                    status=PipelineRunStatus.FAILURE,
                )
            )
            for _ in range(3):
                runs.append(
                    TestRunStorage.build_run(
                        run_id=make_new_run_id(),
                        pipeline_name="foo_pipeline",
                        tags={PARENT_RUN_ID_TAG: failed_run_id, ROOT_RUN_ID_TAG: root_run.run_id},
                    )
                )

        for run in runs:
            storage.add_run(run)

        run_groups = storage.get_run_groups(
            limit=5, filters=RunsFilter(statuses=[PipelineRunStatus.FAILURE])
        )

        assert len(run_groups) == 3

        for root_run_id in run_groups:
            assert len(run_groups[root_run_id]["runs"]) == 2
            assert run_groups[root_run_id]["count"] == 5

    def test_fetch_run_groups_ordering(self, storage):
        assert storage

        first_root_run = TestRunStorage.build_run(
            run_id=make_new_run_id(), pipeline_name="foo_pipeline"
        )

        storage.add_run(first_root_run)

        second_root_run = TestRunStorage.build_run(
            run_id=make_new_run_id(), pipeline_name="foo_pipeline"
        )

        storage.add_run(second_root_run)

        second_root_run_child = TestRunStorage.build_run(
            run_id=make_new_run_id(),
            pipeline_name="foo_pipeline",
            tags={
                PARENT_RUN_ID_TAG: second_root_run.run_id,
                ROOT_RUN_ID_TAG: second_root_run.run_id,
            },
        )

        storage.add_run(second_root_run_child)

        first_root_run_child = TestRunStorage.build_run(
            run_id=make_new_run_id(),
            pipeline_name="foo_pipeline",
            tags={
                PARENT_RUN_ID_TAG: first_root_run.run_id,
                ROOT_RUN_ID_TAG: first_root_run.run_id,
            },
        )

        storage.add_run(first_root_run_child)

        run_groups = storage.get_run_groups(limit=1)

        assert first_root_run.run_id in run_groups
        assert second_root_run.run_id not in run_groups

    def test_partition_status(self, storage):
        one = TestRunStorage.build_run(
            run_id=make_new_run_id(),
            pipeline_name="foo_pipeline",
            status=PipelineRunStatus.FAILURE,
            tags={
                PARTITION_NAME_TAG: "one",
                PARTITION_SET_TAG: "foo_set",
            },
        )
        storage.add_run(one)
        two = TestRunStorage.build_run(
            run_id=make_new_run_id(),
            pipeline_name="foo_pipeline",
            status=PipelineRunStatus.FAILURE,
            tags={
                PARTITION_NAME_TAG: "two",
                PARTITION_SET_TAG: "foo_set",
            },
        )
        storage.add_run(two)
        two_retried = TestRunStorage.build_run(
            run_id=make_new_run_id(),
            pipeline_name="foo_pipeline",
            status=PipelineRunStatus.SUCCESS,
            tags={
                PARTITION_NAME_TAG: "two",
                PARTITION_SET_TAG: "foo_set",
            },
        )
        storage.add_run(two_retried)
        three = TestRunStorage.build_run(
            run_id=make_new_run_id(),
            pipeline_name="foo_pipeline",
            status=PipelineRunStatus.SUCCESS,
            tags={
                PARTITION_NAME_TAG: "three",
                PARTITION_SET_TAG: "foo_set",
            },
        )
        storage.add_run(three)
        partition_data = storage.get_run_partition_data(
            runs_filter=RunsFilter(
                pipeline_name="foo_pipeline",
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

    def test_wipe_heartbeats(self, storage):
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

    def test_backfill(self, storage):
        origin = self.fake_partition_set_origin("fake_partition_set")
        backfills = storage.get_backfills()
        assert len(backfills) == 0

        one = PartitionBackfill(
            "one",
            origin,
            BulkActionStatus.REQUESTED,
            ["a", "b", "c"],
            False,
            None,
            None,
            pendulum.now().timestamp(),
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
        if not isinstance(storage, SqlRunStorage):
            return

        for name in REQUIRED_DATA_MIGRATIONS.keys():
            assert storage.has_built_index(name)

    def test_handle_run_event_pipeline_success_test(self, storage):
        run_id = make_new_run_id()
        run_to_add = TestRunStorage.build_run(pipeline_name="pipeline_name", run_id=run_id)
        storage.add_run(run_to_add)

        dagster_pipeline_start_event = DagsterEvent(
            message="a message",
            event_type_value=DagsterEventType.PIPELINE_START.value,
            pipeline_name="pipeline_name",
            step_key=None,
            solid_handle=None,
            step_kind_value=None,
            logging_tags=None,
        )

        storage.handle_run_event(run_id, dagster_pipeline_start_event)

        assert storage.get_run_by_id(run_id).status == PipelineRunStatus.STARTED

        storage.handle_run_event(
            make_new_run_id(),  # diff run
            DagsterEvent(
                message="a message",
                event_type_value=DagsterEventType.PIPELINE_SUCCESS.value,
                pipeline_name="pipeline_name",
                step_key=None,
                solid_handle=None,
                step_kind_value=None,
                logging_tags=None,
            ),
        )

        assert storage.get_run_by_id(run_id).status == PipelineRunStatus.STARTED

        storage.handle_run_event(
            run_id,  # correct run
            DagsterEvent(
                message="a message",
                event_type_value=DagsterEventType.PIPELINE_SUCCESS.value,
                pipeline_name="pipeline_name",
                step_key=None,
                solid_handle=None,
                step_kind_value=None,
                logging_tags=None,
            ),
        )

        assert storage.get_run_by_id(run_id).status == PipelineRunStatus.SUCCESS

    def test_debug_snapshot_import(self, storage):
        from dagster._core.execution.api import create_execution_plan
        from dagster._core.snap import (
            create_execution_plan_snapshot_id,
            snapshot_from_execution_plan,
        )

        run_id = make_new_run_id()
        run_to_add = TestRunStorage.build_run(pipeline_name="pipeline_name", run_id=run_id)
        storage.add_run(run_to_add)

        pipeline_def = PipelineDefinition(name="some_pipeline", solid_defs=[])

        pipeline_snapshot = pipeline_def.get_pipeline_snapshot()
        pipeline_snapshot_id = create_pipeline_snapshot_id(pipeline_snapshot)
        new_pipeline_snapshot_id = f"{pipeline_snapshot_id}-new-snapshot"

        storage.add_snapshot(pipeline_snapshot, snapshot_id=new_pipeline_snapshot_id)
        assert not storage.has_snapshot(pipeline_snapshot_id)
        assert storage.has_snapshot(new_pipeline_snapshot_id)

        execution_plan = create_execution_plan(pipeline_def)
        ep_snapshot = snapshot_from_execution_plan(execution_plan, new_pipeline_snapshot_id)
        ep_snapshot_id = create_execution_plan_snapshot_id(ep_snapshot)
        new_ep_snapshot_id = f"{ep_snapshot_id}-new-snapshot"

        storage.add_snapshot(ep_snapshot, snapshot_id=new_ep_snapshot_id)
        assert not storage.has_snapshot(ep_snapshot_id)
        assert storage.has_snapshot(new_ep_snapshot_id)

    def test_run_record_stats(self, storage):
        assert storage

        self._skip_in_memory(storage)

        run_id = make_new_run_id()
        run_to_add = TestRunStorage.build_run(pipeline_name="pipeline_name", run_id=run_id)

        storage.add_run(run_to_add)

        run_record = storage.get_run_records(RunsFilter(run_ids=[run_id]))[0]

        assert run_record.start_time is None
        assert run_record.end_time is None

        storage.handle_run_event(
            run_id,
            DagsterEvent(
                message="a message",
                event_type_value=DagsterEventType.PIPELINE_START.value,
                pipeline_name="pipeline_name",
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
                pipeline_name="pipeline_name",
            ),
        )

        run_record = storage.get_run_records(RunsFilter(run_ids=[run_id]))[0]

        assert run_record.start_time is not None
        assert run_record.end_time is not None
        assert run_record.end_time >= run_record.start_time

    def test_by_job(self, storage):
        if not storage.supports_bucket_queries:
            pytest.skip("storage cannot bucket")

        def _add_run(job_name, tags=None):
            return storage.add_run(
                TestRunStorage.build_run(
                    pipeline_name=job_name, run_id=make_new_run_id(), tags=tags
                )
            )

        _a_one = _add_run("a_pipeline", tags={"a": "A"})
        a_two = _add_run("a_pipeline", tags={"a": "A"})
        _b_one = _add_run("b_pipeline", tags={"a": "A"})
        b_two = _add_run("b_pipeline", tags={"a": "A"})
        c_one = _add_run("c_pipeline", tags={"a": "A"})
        c_two = _add_run("c_pipeline", tags={"a": "B"})

        runs_by_job = {
            run.pipeline_name: run
            for run in storage.get_runs(
                bucket_by=JobBucket(
                    job_names=["a_pipeline", "b_pipeline", "c_pipeline"], bucket_limit=1
                )
            )
        }
        assert set(runs_by_job.keys()) == {"a_pipeline", "b_pipeline", "c_pipeline"}
        assert runs_by_job.get("a_pipeline").run_id == a_two.run_id
        assert runs_by_job.get("b_pipeline").run_id == b_two.run_id
        assert runs_by_job.get("c_pipeline").run_id == c_two.run_id

        # fetch with a runs filter applied
        runs_by_job = {
            run.pipeline_name: run
            for run in storage.get_runs(
                filters=RunsFilter(tags={"a": "A"}),
                bucket_by=JobBucket(
                    job_names=["a_pipeline", "b_pipeline", "c_pipeline"], bucket_limit=1
                ),
            )
        }
        assert set(runs_by_job.keys()) == {"a_pipeline", "b_pipeline", "c_pipeline"}
        assert runs_by_job.get("a_pipeline").run_id == a_two.run_id
        assert runs_by_job.get("b_pipeline").run_id == b_two.run_id
        assert runs_by_job.get("c_pipeline").run_id == c_one.run_id

    def test_by_tag(self, storage):
        if not storage.supports_bucket_queries:
            pytest.skip("storage cannot bucket")

        def _add_run(job_name, tags=None):
            return storage.add_run(
                TestRunStorage.build_run(
                    pipeline_name=job_name, run_id=make_new_run_id(), tags=tags
                )
            )

        _one = _add_run("a", tags={"a": "1", "b": "1"})
        _two = _add_run("a", tags={"a": "2", "b": "1"})
        three = _add_run("a", tags={"a": "3", "b": "1"})
        _none = _add_run("a", tags={"b": "1"})
        b = _add_run("b", tags={"a": "4", "b": "2"})
        one = _add_run("a", tags={"a": "1", "b": "1"})
        two = _add_run("a", tags={"a": "2", "b": "1"})

        runs_by_tag = {
            run.tags.get("a"): run
            for run in storage.get_runs(
                bucket_by=TagBucket(tag_key="a", tag_values=["1", "2", "3", "4"], bucket_limit=1)
            )
        }
        assert set(runs_by_tag.keys()) == {"1", "2", "3", "4"}
        assert runs_by_tag.get("1").run_id == one.run_id
        assert runs_by_tag.get("2").run_id == two.run_id
        assert runs_by_tag.get("3").run_id == three.run_id
        assert runs_by_tag.get("4").run_id == b.run_id

        # fetch with a pipeline_name filter applied
        runs_by_tag = {
            run.tags.get("a"): run
            for run in storage.get_runs(
                filters=RunsFilter(pipeline_name="a"),
                bucket_by=TagBucket(tag_key="a", tag_values=["1", "2", "3", "4"], bucket_limit=1),
            )
        }
        assert set(runs_by_tag.keys()) == {"1", "2", "3"}
        assert runs_by_tag.get("1").run_id == one.run_id
        assert runs_by_tag.get("2").run_id == two.run_id
        assert runs_by_tag.get("3").run_id == three.run_id

        # fetch with a tags filter applied
        runs_by_tag = {
            run.tags.get("a"): run
            for run in storage.get_runs(
                filters=RunsFilter(tags={"b": "1"}),
                bucket_by=TagBucket(tag_key="a", tag_values=["1", "2", "3", "4"], bucket_limit=1),
            )
        }
        assert set(runs_by_tag.keys()) == {"1", "2", "3"}
        assert runs_by_tag.get("1").run_id == one.run_id
        assert runs_by_tag.get("2").run_id == two.run_id
        assert runs_by_tag.get("3").run_id == three.run_id

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
            if storage._instance:  # pylint: disable=protected-access
                instance = storage._instance  # pylint: disable=protected-access
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

            with pendulum.test(freeze_datetime):
                result = my_job.execute_in_process(instance=instance)
                records = instance.get_run_records(filters=RunsFilter(run_ids=[result.run_id]))
                assert len(records) == 1
                record = records[0]
                assert record.start_time == freeze_datetime.timestamp()
                assert record.end_time == freeze_datetime.timestamp()

    def test_kvs(self, storage):
        if not storage.supports_kvs():
            pytest.skip("storage cannot kvs")

        storage.kvs_set({"key": "value"})
        assert storage.kvs_get({"key"}) == {"key": "value"}

        storage.kvs_set({"key": "new-value"})
        assert storage.kvs_get({"key"}) == {"key": "new-value"}

        storage.kvs_set({"foo": "foo", "bar": "bar"})
        assert storage.kvs_get({"foo", "bar", "key"}) == {
            "key": "new-value",
            "foo": "foo",
            "bar": "bar",
        }

        storage.kvs_set({"foo": "1", "bar": "2", "key": "3"})
        assert storage.kvs_get({"foo", "bar", "key"}) == {"foo": "1", "bar": "2", "key": "3"}

    def test_migrate_repo(self, storage):
        assert storage
        self._skip_in_memory(storage)

        one = make_new_run_id()
        two = make_new_run_id()
        job_name = "some_job"

        origin_one = self.fake_job_origin(job_name, "fake_repo_one")
        origin_two = self.fake_job_origin(job_name, "fake_repo_two")
        storage.add_run(
            TestRunStorage.build_run(
                run_id=one, pipeline_name=job_name, external_pipeline_origin=origin_one
            )
        )
        storage.add_run(
            TestRunStorage.build_run(
                run_id=two, pipeline_name=job_name, external_pipeline_origin=origin_one
            )
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
