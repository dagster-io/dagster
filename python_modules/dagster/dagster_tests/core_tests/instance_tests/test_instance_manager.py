import datetime

import dagster as dg
from dagster._core.instance_manager import InstanceManager


def test_instance_manager():
    @dg.asset
    def asset_1():
        return 1

    @dg.asset(deps=[asset_1])
    def asset_2():
        return 2

    @dg.asset(deps=[asset_2])
    def asset_3():
        return 3

    defs = dg.Definitions(assets=[asset_1, asset_2, asset_3])

    with InstanceManager(defs=defs, current_time=datetime.datetime(2024, 8, 16, 1, 1)) as mngr:
        # all succeed
        run = mngr.create_asset_run(asset_selection=dg.AssetSelection.all())
        assert run.dagster_run.status == dg.DagsterRunStatus.NOT_STARTED
        mngr.execute_steps_for_assets(run, asset_selection=["asset_1"])
        assert run.dagster_run.status == dg.DagsterRunStatus.STARTED
        mngr.execute_steps_for_assets(run, asset_selection=["asset_2"])
        assert run.dagster_run.status == dg.DagsterRunStatus.STARTED
        mngr.execute_steps_for_assets(run, asset_selection=["asset_3"])
        assert run.dagster_run.status == dg.DagsterRunStatus.SUCCESS

        # one fails
        run = mngr.create_asset_run(asset_selection=dg.AssetSelection.all())
        assert run.dagster_run.status == dg.DagsterRunStatus.NOT_STARTED
        mngr.execute_steps_for_assets(run, asset_selection=["asset_1"])
        assert run.dagster_run.status == dg.DagsterRunStatus.STARTED
        mngr.fail_steps_for_assets(run, asset_selection=["asset_2"])
        assert run.dagster_run.status == dg.DagsterRunStatus.FAILURE


def test_automation_conditions_with_manager() -> None:
    @dg.asset(automation_condition=dg.AutomationCondition.in_progress())
    def A() -> None: ...

    @dg.asset(automation_condition=dg.AutomationCondition.execution_failed())
    def B() -> None: ...

    defs = dg.Definitions(assets=[A, B])

    with InstanceManager(defs=defs) as mngr:
        result = dg.evaluate_automation_conditions(defs=defs, instance=mngr.instance)
        assert result.total_requested == 0

        run = mngr.create_asset_run(asset_selection=[A.key, B.key])
        mngr.start_run(run)

        # now A is in progress, as there's a run targeting it
        result = dg.evaluate_automation_conditions(
            defs=defs, instance=mngr.instance, cursor=result.cursor
        )
        assert result.total_requested == 1
        assert result.get_num_requested(A.key) == 1

        mngr.execute_steps_for_assets(run, asset_selection=[A.key])
        result = dg.evaluate_automation_conditions(
            defs=defs, instance=mngr.instance, cursor=result.cursor
        )
        assert result.total_requested == 0

        mngr.fail_steps_for_assets(run, asset_selection=[B.key])
        result = dg.evaluate_automation_conditions(
            defs=defs, instance=mngr.instance, cursor=result.cursor
        )
        assert result.total_requested == 1
        assert result.get_num_requested(B.key) == 1
