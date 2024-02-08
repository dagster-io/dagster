from dagster import GraphOut, In, Out, graph, job, op
from dagster._core.execution.api import create_execution_plan
from dagster._core.snap import create_job_snapshot_id, snapshot_from_execution_plan
from dagster._serdes import serialize_pp


def test_create_noop_execution_plan(snapshot, ignore_code_origin):
    @op
    def noop_op(_):
        pass

    @job
    def noop_job():
        noop_op()

    execution_plan = create_execution_plan(noop_job)

    snapshot.assert_match(
        serialize_pp(
            snapshot_from_execution_plan(
                execution_plan,
                create_job_snapshot_id(noop_job.get_job_snapshot()),
            )
        )
    )


def test_create_execution_plan_with_dep(snapshot, ignore_code_origin):
    @op
    def op_one(_):
        return 1

    @op
    def op_two(_, num):
        return num + 1

    @job
    def noop_job():
        op_two(op_one())

    execution_plan = create_execution_plan(noop_job)

    snapshot.assert_match(
        serialize_pp(
            snapshot_from_execution_plan(
                execution_plan,
                create_job_snapshot_id(noop_job.get_job_snapshot()),
            )
        )
    )


def test_create_with_graph(snapshot, ignore_code_origin):
    @op(out={"out_num": Out(dagster_type=int)})
    def return_one(_):
        return 1

    @op(
        ins={"num": In(dagster_type=int)},
        out=Out(int),
    )
    def add_one(_, num):
        return num + 1

    @graph(out={"named_output": GraphOut()})
    def comp_1():
        return add_one(return_one())

    @graph(out={"named_output": GraphOut()})
    def comp_2():
        return add_one(return_one())

    @op
    def add(_, num_one, num_two):
        return num_one + num_two

    @job
    def do_comps():
        add(num_one=comp_1(), num_two=comp_2())

    execution_plan = create_execution_plan(do_comps)

    snapshot.assert_match(
        serialize_pp(
            snapshot_from_execution_plan(
                execution_plan,
                create_job_snapshot_id(do_comps.get_job_snapshot()),
            )
        )
    )


def test_create_noop_execution_plan_with_tags(snapshot, ignore_code_origin):
    @op(tags={"foo": "bar", "bar": "baaz"})
    def noop_op(_):
        pass

    @job
    def noop_job():
        noop_op()

    execution_plan = create_execution_plan(noop_job)

    snapshot.assert_match(
        serialize_pp(
            snapshot_from_execution_plan(
                execution_plan,
                create_job_snapshot_id(noop_job.get_job_snapshot()),
            )
        )
    )
