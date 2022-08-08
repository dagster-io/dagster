from dagster._core.execution.api import create_execution_plan
from dagster._core.snap import create_pipeline_snapshot_id, snapshot_from_execution_plan
from dagster._legacy import (
    InputDefinition,
    OutputDefinition,
    composite_solid,
    pipeline,
    solid,
)
from dagster._serdes import serialize_pp
from dagster import In, Out, op


def test_create_noop_execution_plan(snapshot):
    @op
    def noop_op(_):
        pass

    @pipeline
    def noop_pipeline():
        noop_op()

    execution_plan = create_execution_plan(noop_pipeline)

    snapshot.assert_match(
        serialize_pp(
            snapshot_from_execution_plan(
                execution_plan,
                create_pipeline_snapshot_id(noop_pipeline.get_pipeline_snapshot()),
            )
        )
    )


def test_create_execution_plan_with_dep(snapshot):
    @op
    def op_one(_):
        return 1

    @op
    def op_two(_, num):
        return num + 1

    @pipeline
    def noop_pipeline():
        op_two(op_one())

    execution_plan = create_execution_plan(noop_pipeline)

    snapshot.assert_match(
        serialize_pp(
            snapshot_from_execution_plan(
                execution_plan,
                create_pipeline_snapshot_id(noop_pipeline.get_pipeline_snapshot()),
            )
        )
    )


def test_create_with_composite(snapshot):
    @op(out={"out_num": Out(dagster_type=int)})
    def return_one(_):
        return 1

    @op(
        ins={"num": In(dagster_type=int)},
        out=Out(int),
    )
    def add_one(_, num):
        return num + 1

    @composite_solid(
        output_defs=[OutputDefinition(name="named_output", dagster_type=int)]
    )
    def comp_1():
        return add_one(return_one())

    @composite_solid(
        output_defs=[OutputDefinition(name="named_output", dagster_type=int)]
    )
    def comp_2():
        return add_one(return_one())

    @op
    def add(_, num_one, num_two):
        return num_one + num_two

    @pipeline
    def do_comps():
        add(num_one=comp_1(), num_two=comp_2())

    execution_plan = create_execution_plan(do_comps)

    snapshot.assert_match(
        serialize_pp(
            snapshot_from_execution_plan(
                execution_plan,
                create_pipeline_snapshot_id(do_comps.get_pipeline_snapshot()),
            )
        )
    )


def test_create_noop_execution_plan_with_tags(snapshot):
    @op(tags={"foo": "bar", "bar": "baaz"})
    def noop_op(_):
        pass

    @pipeline
    def noop_pipeline():
        noop_op()

    execution_plan = create_execution_plan(noop_pipeline)

    snapshot.assert_match(
        serialize_pp(
            snapshot_from_execution_plan(
                execution_plan,
                create_pipeline_snapshot_id(noop_pipeline.get_pipeline_snapshot()),
            )
        )
    )
