import asyncio
import logging
import sys

import dagster as dg
import pytest
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.definitions.automation_tick_evaluation_context import build_run_requests
from dagster._core.definitions.reconstruct import ReconstructableRepository
from dagster._core.execution.api import execute_run
from dagster._core.execution.submit_asset_runs import _create_asset_run
from dagster._core.remote_origin import InProcessCodeLocationOrigin
from dagster._core.test_utils import (
    InProcessTestWorkspaceLoadTarget,
    create_test_daemon_workspace_context,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin


@dg.asset(automation_condition=dg.AutomationCondition.missing())
def checked_asset() -> None: ...


@dg.asset_check(
    asset=checked_asset, automation_condition=dg.AutomationCondition.on_cron("0 8 * * *")
)
def independently_scheduled_check() -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=True)


def get_defs() -> dg.Definitions:
    return dg.Definitions(assets=[checked_asset], asset_checks=[independently_scheduled_check])


@pytest.mark.parametrize(
    "check_selection", [None, [], [independently_scheduled_check.check_key], "automation"]
)
def test_create_asset_run_preserves_check_selection(check_selection):
    if check_selection == "automation":
        defs = get_defs()
        asset_graph_view = AssetGraphView.for_test(defs)
        run_requests = build_run_requests(
            entity_subsets=[asset_graph_view.get_full_subset(key=checked_asset.key)],
            asset_graph=defs.resolve_asset_graph(),
            run_tags={},
            emit_backfills=False,
        )
        assert len(run_requests) == 1
        run_request = run_requests[0]
        assert run_request.asset_check_keys == []
        check_selection = []
    else:
        run_request = dg.RunRequest(
            asset_selection=[checked_asset.key], asset_check_keys=check_selection
        )
    with dg.instance_for_test() as instance:
        load_target = InProcessTestWorkspaceLoadTarget(
            InProcessCodeLocationOrigin(
                LoadableTargetOrigin(
                    executable_path=sys.executable, module_name=__name__, attribute="get_defs"
                )
            )
        )
        with create_test_daemon_workspace_context(load_target, instance) as workspace_context:
            run = asyncio.run(
                _create_asset_run(
                    run_id=None,
                    run_request=run_request,
                    run_request_index=0,
                    instance=instance,
                    run_request_execution_data_cache={},
                    workspace_process_context=workspace_context,
                    workspace=workspace_context.create_request_context(),
                    debug_crash_flags={},
                    logger=logging.getLogger("test_submit_asset_runs"),
                )
            )

        expected_selection = None if check_selection is None else frozenset(check_selection)
        assert run.asset_check_selection == expected_selection
        stored_run = instance.get_run_by_id(run.run_id)
        assert stored_run is not None
        assert stored_run.asset_check_selection == expected_selection
        execution_plan = instance.get_execution_plan_snapshot(run.execution_plan_snapshot_id)
        assert execution_plan is not None
        expected_steps = {"checked_asset"}
        if check_selection is None or check_selection:
            expected_steps.add("checked_asset_independently_scheduled_check")
        assert set(execution_plan.step_keys_to_execute) == expected_steps

        result = execute_run(
            ReconstructableRepository.for_module(__name__, "get_defs").get_reconstructable_job(
                run.job_name
            ),
            stored_run,
            instance,
            raise_on_error=True,
        )
        assert result.success
        started_steps = {event.step_key for event in result.all_events if event.is_step_start}
        assert started_steps == expected_steps
        evaluations = result.get_asset_check_evaluations()
        assert len(evaluations) == (0 if check_selection == [] else 1)
