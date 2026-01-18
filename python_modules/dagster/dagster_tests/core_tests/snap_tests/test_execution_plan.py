import dagster as dg
from dagster._core.execution.api import create_execution_plan
from dagster._core.snap import snapshot_from_execution_plan
from dagster._serdes import serialize_pp


def test_create_noop_execution_plan(snapshot):
    @dg.op
    def noop_op(_):
        pass

    @dg.job
    def noop_job():
        noop_op()

    execution_plan = create_execution_plan(noop_job)

    snapshot.assert_match(
        serialize_pp(
            snapshot_from_execution_plan(execution_plan, noop_job.get_job_snapshot().snapshot_id)
        )
    )


def test_create_execution_plan_with_dep(snapshot):
    @dg.op
    def op_one(_):
        return 1

    @dg.op
    def op_two(_, num):
        return num + 1

    @dg.job
    def noop_job():
        op_two(op_one())

    execution_plan = create_execution_plan(noop_job)

    snapshot.assert_match(
        serialize_pp(
            snapshot_from_execution_plan(
                execution_plan,
                noop_job.get_job_snapshot().snapshot_id,
            )
        )
    )


def test_create_with_graph(snapshot):
    @dg.op(out={"out_num": dg.Out(dagster_type=int)})
    def return_one(_):
        return 1

    @dg.op(
        ins={"num": dg.In(dagster_type=int)},
        out=dg.Out(int),
    )
    def add_one(_, num):
        return num + 1

    @dg.graph(out={"named_output": dg.GraphOut()})
    def comp_1():
        return add_one(return_one())

    @dg.graph(out={"named_output": dg.GraphOut()})
    def comp_2():
        return add_one(return_one())

    @dg.op
    def add(_, num_one, num_two):
        return num_one + num_two

    @dg.job
    def do_comps():
        add(num_one=comp_1(), num_two=comp_2())

    execution_plan = create_execution_plan(do_comps)

    snapshot.assert_match(
        serialize_pp(
            snapshot_from_execution_plan(
                execution_plan,
                do_comps.get_job_snapshot().snapshot_id,
            )
        )
    )


def test_create_noop_execution_plan_with_tags(snapshot):
    @dg.op(tags={"foo": "bar", "bar": "baaz"})
    def noop_op(_):
        pass

    @dg.job
    def noop_job():
        noop_op()

    execution_plan = create_execution_plan(noop_job)

    snapshot.assert_match(
        serialize_pp(
            snapshot_from_execution_plan(
                execution_plan,
                noop_job.get_job_snapshot().snapshot_id,
            )
        )
    )
