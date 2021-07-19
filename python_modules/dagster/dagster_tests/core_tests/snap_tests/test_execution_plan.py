import tempfile

from dagster import (
    InputDefinition,
    ModeDefinition,
    OutputDefinition,
    composite_solid,
    pipeline,
    solid,
)
from dagster.core.execution.api import create_execution_plan
from dagster.core.snap import create_pipeline_snapshot_id, snapshot_from_execution_plan
from dagster.core.storage.memoizable_io_manager import versioned_filesystem_io_manager
from dagster.core.storage.tags import MEMOIZED_RUN_TAG
from dagster.core.test_utils import instance_for_test
from dagster.serdes import serialize_pp


def test_create_noop_execution_plan(snapshot):
    @solid
    def noop_solid(_):
        pass

    @pipeline
    def noop_pipeline():
        noop_solid()

    execution_plan = create_execution_plan(noop_pipeline)

    snapshot.assert_match(
        serialize_pp(
            snapshot_from_execution_plan(
                execution_plan, create_pipeline_snapshot_id(noop_pipeline.get_pipeline_snapshot())
            )
        )
    )


def test_create_execution_plan_with_dep(snapshot):
    @solid
    def solid_one(_):
        return 1

    @solid
    def solid_two(_, num):
        return num + 1

    @pipeline
    def noop_pipeline():
        solid_two(solid_one())

    execution_plan = create_execution_plan(noop_pipeline)

    snapshot.assert_match(
        serialize_pp(
            snapshot_from_execution_plan(
                execution_plan, create_pipeline_snapshot_id(noop_pipeline.get_pipeline_snapshot())
            )
        )
    )


def test_create_with_composite(snapshot):
    @solid(output_defs=[OutputDefinition(name="out_num", dagster_type=int)])
    def return_one(_):
        return 1

    @solid(
        input_defs=[InputDefinition(name="num", dagster_type=int)],
        output_defs=[OutputDefinition(int)],
    )
    def add_one(_, num):
        return num + 1

    @composite_solid(output_defs=[OutputDefinition(name="named_output", dagster_type=int)])
    def comp_1():
        return add_one(return_one())

    @composite_solid(output_defs=[OutputDefinition(name="named_output", dagster_type=int)])
    def comp_2():
        return add_one(return_one())

    @solid
    def add(_, num_one, num_two):
        return num_one + num_two

    @pipeline
    def do_comps():
        add(num_one=comp_1(), num_two=comp_2())

    execution_plan = create_execution_plan(do_comps)

    snapshot.assert_match(
        serialize_pp(
            snapshot_from_execution_plan(
                execution_plan, create_pipeline_snapshot_id(do_comps.get_pipeline_snapshot())
            )
        )
    )


def test_create_noop_execution_plan_with_tags(snapshot):
    @solid(tags={"foo": "bar", "bar": "baaz"})
    def noop_solid(_):
        pass

    @pipeline
    def noop_pipeline():
        noop_solid()

    execution_plan = create_execution_plan(noop_pipeline)

    snapshot.assert_match(
        serialize_pp(
            snapshot_from_execution_plan(
                execution_plan, create_pipeline_snapshot_id(noop_pipeline.get_pipeline_snapshot())
            )
        )
    )


def test_execution_plan_snapshot_step_output_versions():
    @solid(version="foo")
    def noop_solid():
        pass

    @pipeline
    def noop_pipeline():
        noop_solid()

    execution_plan = create_execution_plan(noop_pipeline)

    execution_plan_snap = snapshot_from_execution_plan(
        execution_plan, create_pipeline_snapshot_id(noop_pipeline.get_pipeline_snapshot())
    )

    assert len(execution_plan_snap.step_output_versions) == 0

    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(temp_dir=temp_dir) as instance:

            @pipeline(
                tags={MEMOIZED_RUN_TAG: "true"},
                mode_defs=[
                    ModeDefinition(resource_defs={"io_manager": versioned_filesystem_io_manager})
                ],
            )
            def noop_pipeline_versioned():
                noop_solid()

            execution_plan = create_execution_plan(noop_pipeline_versioned, instance=instance)

            execution_plan_snap = snapshot_from_execution_plan(
                execution_plan, create_pipeline_snapshot_id(noop_pipeline.get_pipeline_snapshot())
            )

            assert len(execution_plan_snap.step_output_versions) == 1
