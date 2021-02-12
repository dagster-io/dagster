import sys

import pendulum
import pytest
from dagster.core.definitions import PipelineDefinition
from dagster.core.errors import DagsterRunAlreadyExists, DagsterSnapshotDoesNotExist
from dagster.core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster.core.host_representation import (
    ExternalRepositoryOrigin,
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
)
from dagster.core.snap import create_pipeline_snapshot_id
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus, PipelineRunsFilter
from dagster.core.storage.tags import PARENT_RUN_ID_TAG, ROOT_RUN_ID_TAG
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.core.utils import make_new_run_id
from dagster.daemon.daemon import SensorDaemon
from dagster.daemon.types import DaemonHeartbeat
from dagster.serdes import serialize_pp


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

    @staticmethod
    def fake_repo_target():
        return ExternalRepositoryOrigin(
            ManagedGrpcPythonEnvRepositoryLocationOrigin(
                LoadableTargetOrigin(
                    executable_path=sys.executable, module_name="fake", attribute="fake"
                ),
            ),
            "fake_repo_name",
        )

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
    ):
        return PipelineRun(
            pipeline_name=pipeline_name,
            run_id=run_id,
            run_config=None,
            mode=mode,
            tags=tags,
            status=status,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            pipeline_snapshot_id=pipeline_snapshot_id,
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
        assert storage
        run_id = make_new_run_id()
        storage.add_run(TestRunStorage.build_run(run_id=run_id, pipeline_name="some_pipeline"))
        assert len(storage.get_runs()) == 1
        storage.wipe()
        assert list(storage.get_runs()) == []

    def test_fetch_by_pipeline(self, storage):
        assert storage
        one = make_new_run_id()
        two = make_new_run_id()
        storage.add_run(TestRunStorage.build_run(run_id=one, pipeline_name="some_pipeline"))
        storage.add_run(TestRunStorage.build_run(run_id=two, pipeline_name="some_other_pipeline"))
        assert len(storage.get_runs()) == 2
        some_runs = storage.get_runs(PipelineRunsFilter(pipeline_name="some_pipeline"))
        assert len(some_runs) == 1
        assert some_runs[0].run_id == one

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
        runs_a = storage.get_runs(PipelineRunsFilter(snapshot_id=pipeline_snapshot_a_id))
        assert len(runs_a) == 1
        assert runs_a[0].run_id == one

        runs_b = storage.get_runs(PipelineRunsFilter(snapshot_id=pipeline_snapshot_b_id))
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

        some_runs = storage.get_runs(PipelineRunsFilter(tags={"tag3": "val3"}))

        assert len(some_runs) == 1
        assert some_runs[0].run_id == one

        runs_with_old_tag = storage.get_runs(PipelineRunsFilter(tags={"tag1": "val1"}))
        assert len(runs_with_old_tag) == 1
        assert runs_with_old_tag[0].tags == {"tag1": "val1"}

        runs_with_new_tag = storage.get_runs(PipelineRunsFilter(tags={"tag1": "val3"}))
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

        assert len(storage.get_runs()) == 3

        some_runs = storage.get_runs(PipelineRunsFilter(run_ids=[one]))
        count = storage.get_runs_count(PipelineRunsFilter(run_ids=[one]))
        assert len(some_runs) == 1
        assert count == 1
        assert some_runs[0].run_id == one

        some_runs = storage.get_runs(PipelineRunsFilter(pipeline_name="some_pipeline"))
        count = storage.get_runs_count(PipelineRunsFilter(pipeline_name="some_pipeline"))
        assert len(some_runs) == 2
        assert count == 2
        assert some_runs[0].run_id == two
        assert some_runs[1].run_id == one

        some_runs = storage.get_runs(PipelineRunsFilter(statuses=[PipelineRunStatus.SUCCESS]))
        count = storage.get_runs_count(PipelineRunsFilter(statuses=[PipelineRunStatus.SUCCESS]))
        assert len(some_runs) == 2
        assert count == 2
        assert some_runs[0].run_id == three
        assert some_runs[1].run_id == one

        some_runs = storage.get_runs(PipelineRunsFilter(tags={"tag": "hello"}))
        count = storage.get_runs_count(PipelineRunsFilter(tags={"tag": "hello"}))
        assert len(some_runs) == 2
        assert count == 2
        assert some_runs[0].run_id == two
        assert some_runs[1].run_id == one

        some_runs = storage.get_runs(PipelineRunsFilter(tags={"tag": "hello", "tag2": "world"}))
        count = storage.get_runs_count(PipelineRunsFilter(tags={"tag": "hello", "tag2": "world"}))
        assert len(some_runs) == 1
        assert count == 1
        assert some_runs[0].run_id == one

        some_runs = storage.get_runs(
            PipelineRunsFilter(pipeline_name="some_pipeline", tags={"tag": "hello"})
        )
        count = storage.get_runs_count(
            PipelineRunsFilter(pipeline_name="some_pipeline", tags={"tag": "hello"})
        )
        assert len(some_runs) == 2
        assert count == 2
        assert some_runs[0].run_id == two
        assert some_runs[1].run_id == one

        some_runs = storage.get_runs(
            PipelineRunsFilter(
                pipeline_name="some_pipeline",
                tags={"tag": "hello"},
                statuses=[PipelineRunStatus.SUCCESS],
            )
        )
        count = storage.get_runs_count(
            PipelineRunsFilter(
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
            PipelineRunsFilter(
                run_ids=[one],
                pipeline_name="some_pipeline",
                tags={"tag": "hello"},
                statuses=[PipelineRunStatus.SUCCESS],
            )
        )
        count = storage.get_runs_count(
            PipelineRunsFilter(
                run_ids=[one],
                pipeline_name="some_pipeline",
                tags={"tag": "hello"},
                statuses=[PipelineRunStatus.SUCCESS],
            )
        )
        assert len(some_runs) == 1
        assert count == 1
        assert some_runs[0].run_id == one

        some_runs = storage.get_runs(PipelineRunsFilter())
        count = storage.get_runs_count(PipelineRunsFilter())
        assert len(some_runs) == 3
        assert count == 3

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
            filters=PipelineRunsFilter(tags={"mytag": "hello", "mytag2": "world"})
        )
        assert run_count == 1

        run_count = storage.get_runs_count(filters=PipelineRunsFilter(tags={"mytag2": "world"}))
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

        some_runs = storage.get_runs(PipelineRunsFilter(tags={"mytag": "hello", "mytag2": "world"}))

        assert len(some_runs) == 1
        assert some_runs[0].run_id == one

        some_runs = storage.get_runs(PipelineRunsFilter(tags={"mytag2": "world"}))
        assert len(some_runs) == 2
        assert some_runs[0].run_id == two
        assert some_runs[1].run_id == one

        some_runs = storage.get_runs(PipelineRunsFilter(tags={}))
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

        all_runs = storage.get_runs(PipelineRunsFilter(pipeline_name="some_pipeline"))
        assert len(all_runs) == 3
        sliced_runs = storage.get_runs(
            PipelineRunsFilter(pipeline_name="some_pipeline"), cursor=three, limit=1
        )
        assert len(sliced_runs) == 1
        assert sliced_runs[0].run_id == two

        all_runs = storage.get_runs(PipelineRunsFilter(tags={"mytag": "hello"}))
        assert len(all_runs) == 3
        sliced_runs = storage.get_runs(
            PipelineRunsFilter(tags={"mytag": "hello"}), cursor=three, limit=1
        )
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
            for run in storage.get_runs(
                PipelineRunsFilter(statuses=[PipelineRunStatus.NOT_STARTED])
            )
        } == {one}

        assert {
            run.run_id
            for run in storage.get_runs(PipelineRunsFilter(statuses=[PipelineRunStatus.STARTED]))
        } == {
            two,
            three,
        }

        assert {
            run.run_id
            for run in storage.get_runs(PipelineRunsFilter(statuses=[PipelineRunStatus.FAILURE]))
        } == {four}

        assert {
            run.run_id
            for run in storage.get_runs(PipelineRunsFilter(statuses=[PipelineRunStatus.SUCCESS]))
        } == set()

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
            PipelineRunsFilter(statuses=[PipelineRunStatus.STARTED]), cursor=four
        )
        assert len(cursor_four_runs) == 2
        assert {run.run_id for run in cursor_four_runs} == {one, two}

        cursor_two_runs = storage.get_runs(
            PipelineRunsFilter(statuses=[PipelineRunStatus.STARTED]), cursor=two
        )
        assert len(cursor_two_runs) == 1
        assert {run.run_id for run in cursor_two_runs} == {one}

        cursor_one_runs = storage.get_runs(
            PipelineRunsFilter(statuses=[PipelineRunStatus.STARTED]), cursor=one
        )
        assert not cursor_one_runs

        cursor_four_limit_one = storage.get_runs(
            PipelineRunsFilter(statuses=[PipelineRunStatus.STARTED]), cursor=four, limit=1
        )
        assert len(cursor_four_limit_one) == 1
        assert cursor_four_limit_one[0].run_id == two

    def test_delete(self, storage):
        assert storage
        run_id = make_new_run_id()
        storage.add_run(TestRunStorage.build_run(run_id=run_id, pipeline_name="some_pipeline"))
        assert len(storage.get_runs()) == 1
        storage.delete_run(run_id)
        assert list(storage.get_runs()) == []

    def test_delete_with_tags(self, storage):
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
        run_id = "some_run_id"
        run = PipelineRun(run_id=run_id, pipeline_name="a_pipeline", tags={"foo": "bar"})

        storage.add_run(run)

        assert storage.get_run_by_id(run_id) == run
        assert dict(storage.get_run_tags()) == {"foo": {"bar"}}

        storage.wipe()
        assert list(storage.get_runs()) == []
        assert dict(storage.get_run_tags()) == {}

    def test_write_conflicting_run_id(self, storage):
        double_run_id = "double_run_id"
        pipeline_def = PipelineDefinition(name="some_pipeline", solid_defs=[])

        run = PipelineRun(run_id=double_run_id, pipeline_name=pipeline_def.name)

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

        storage.wipe()

        assert not storage.has_pipeline_snapshot(pipeline_snapshot_id)

    def test_single_write_read_with_snapshot(self, storage):
        run_with_snapshot_id = "lkasjdflkjasdf"
        pipeline_def = PipelineDefinition(name="some_pipeline", solid_defs=[])

        pipeline_snapshot = pipeline_def.get_pipeline_snapshot()

        pipeline_snapshot_id = create_pipeline_snapshot_id(pipeline_snapshot)

        run_with_snapshot = PipelineRun(
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

        storage.wipe()

        assert not storage.has_pipeline_snapshot(pipeline_snapshot_id)
        assert not storage.has_run(run_with_snapshot_id)

    def test_single_write_with_missing_snapshot(self, storage):

        run_with_snapshot_id = "lkasjdflkjasdf"
        pipeline_def = PipelineDefinition(name="some_pipeline", solid_defs=[])

        run_with_missing_snapshot = PipelineRun(
            run_id=run_with_snapshot_id,
            pipeline_name=pipeline_def.name,
            pipeline_snapshot_id="nope",
        )

        with pytest.raises(DagsterSnapshotDoesNotExist):
            storage.add_run(run_with_missing_snapshot)

    def test_add_get_execution_snapshot(self, storage):
        from dagster.core.execution.api import create_execution_plan
        from dagster.core.snap import snapshot_from_execution_plan

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

        some_runs = storage.get_runs(PipelineRunsFilter(run_ids=[one, two]))
        count = storage.get_runs_count(PipelineRunsFilter(run_ids=[one, two]))
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

        run_group_result = storage.get_run_group(make_new_run_id())
        assert run_group_result is None

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
            limit=5, filters=PipelineRunsFilter(statuses=[PipelineRunStatus.FAILURE])
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

    def _skip_in_memory(self, storage):
        from dagster.core.storage.runs import InMemoryRunStorage

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
        assert storage.has_bulk_actions_table()
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
