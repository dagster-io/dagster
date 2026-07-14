import dagster as dg
import pytest
from dagster import DagsterInstance
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_key import AssetJobKey
from dagster._core.definitions.assets.graph.asset_graph import AssetGraph
from dagster._core.definitions.declarative_automation.automation_condition_evaluator import (
    AutomationConditionEvaluator,
)


def test_evaluator_rejects_job_keys() -> None:
    """Job-condition evaluation is not implemented yet; asking the evaluator to evaluate a
    job key must fail loudly rather than silently skipping it.
    """

    @dg.asset(automation_condition=dg.AutomationCondition.eager())
    def my_asset() -> None: ...

    asset_graph = AssetGraph.from_assets([my_asset])

    def make_evaluator(entity_keys):
        return AutomationConditionEvaluator(
            entity_keys=entity_keys,
            instance=DagsterInstance.ephemeral(),
            asset_graph=asset_graph,
            cursor=AssetDaemonCursor.empty(),
            emit_backfills=False,
            evaluation_id=0,
        )

    # asset keys alone are fine
    make_evaluator({my_asset.key})

    with pytest.raises(NotImplementedError, match="my_job"):
        make_evaluator({my_asset.key, AssetJobKey("my_job")})


def test_repo_with_conditioned_job_still_evaluates_assets() -> None:
    """A repository containing an automation-conditioned job must not break asset
    evaluation. The daemon/sensor path resolves entity keys from asset selections, which
    never yield job keys, so the job node in the repo's asset graph is simply ignored
    rather than tripping the evaluator's job-key rejection.
    """

    # missing() is deterministically true for a never-materialized asset
    @dg.asset(automation_condition=dg.AutomationCondition.missing())
    def missing_asset() -> None: ...

    conditioned_job = dg.define_asset_job(
        name="conditioned_job",
        selection=[missing_asset],
        automation_condition=dg.AutomationCondition.eager(),
    )
    defs = dg.Definitions(assets=[missing_asset], jobs=[conditioned_job])

    # the graph being evaluated does contain the job node
    assert defs.resolve_asset_graph().has(AssetJobKey("conditioned_job"))

    result = dg.evaluate_automation_conditions(defs=defs, instance=DagsterInstance.ephemeral())
    # the never-materialized asset is requested; only the asset key was evaluated
    assert result.total_requested == 1
    assert {r.key for r in result.results} == {missing_asset.key}
