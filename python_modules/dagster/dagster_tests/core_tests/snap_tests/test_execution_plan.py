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


def test_execution_plan_snapshot_asset_check_keys():
    @dg.asset
    def my_asset():
        return 1

    @dg.asset_check(asset=my_asset)
    def my_check():
        return dg.AssetCheckResult(passed=True)

    @dg.asset_check(asset=my_asset)
    def my_other_check():
        return dg.AssetCheckResult(passed=True)

    defs = dg.Definitions(assets=[my_asset], asset_checks=[my_check, my_other_check])
    job_def = defs.get_implicit_global_asset_job_def()

    execution_plan = create_execution_plan(job_def)
    snapshot = snapshot_from_execution_plan(execution_plan, job_def.get_job_snapshot().snapshot_id)

    assert snapshot.asset_selection == {dg.AssetKey("my_asset")}
    assert snapshot.asset_check_keys == {
        dg.AssetCheckKey(dg.AssetKey("my_asset"), "my_check"),
        dg.AssetCheckKey(dg.AssetKey("my_asset"), "my_other_check"),
    }


def test_execution_plan_pool_slots_round_trip():
    from dagster._core.execution.plan.plan import ExecutionPlan
    from dagster._serdes import deserialize_value, serialize_value

    @dg.op(pool="heavy", pool_slots=3)
    def heavy_op():
        pass

    @dg.op(pool="light")
    def light_op():
        pass

    @dg.job
    def pool_job():
        heavy_op()
        light_op()

    execution_plan = create_execution_plan(pool_job)
    step = execution_plan.get_step_by_key("heavy_op")
    assert step.pool == "heavy"
    assert step.pool_slots == 3
    assert execution_plan.get_step_by_key("light_op").pool_slots is None

    plan_snapshot = snapshot_from_execution_plan(
        execution_plan, pool_job.get_job_snapshot().snapshot_id
    )

    # the value survives serialization and plan rebuilds
    serialized = serialize_value(plan_snapshot)
    rebuilt_snapshot = deserialize_value(serialized, type(plan_snapshot))
    rebuilt_plan = ExecutionPlan.rebuild_from_snapshot("pool_job", rebuilt_snapshot)
    assert rebuilt_plan.get_step_by_key("heavy_op").pool_slots == 3

    # unset pool_slots is skipped during serialization, so existing snapshots are unchanged
    light_step_snap = next(s for s in plan_snapshot.steps if s.key == "light_op")
    assert light_step_snap.pool_slots is None
    assert '"pool_slots": 3' in serialized
    assert serialized.count('"pool_slots"') == 1
