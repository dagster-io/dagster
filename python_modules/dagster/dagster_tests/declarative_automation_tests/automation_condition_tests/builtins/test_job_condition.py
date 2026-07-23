"""Test job automation condition operators."""

# this module intentionally exercises the operators' internal asset-resolution
# helpers (_get_root_asset_keys, _child_for_asset_key)
# ruff: noqa: SLF001

import asyncio

import dagster as dg
import pytest
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_key import AssetJobKey
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationResult,
    BuiltinAutomationCondition,
)
from dagster._core.definitions.declarative_automation.automation_condition_evaluator import (
    AutomationConditionEvaluator,
)
from dagster._core.definitions.declarative_automation.automation_context import AutomationContext
from dagster._core.definitions.declarative_automation.operators import (
    AllJobRootAssetsMatchCondition,
    AnyJobRootAssetsMatchCondition,
)
from dagster._core.definitions.declarative_automation.operators.dep_operators import (
    EntityMatchesCondition,
)
from dagster._core.remote_representation.external import RemoteRepository
from dagster._core.remote_representation.external_data import RepositorySnap
from dagster._core.remote_representation.handle import RepositoryHandle

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _local_graph(defs: dg.Definitions):
    return defs.get_repository_def().asset_graph


def _remote_graph(defs: dg.Definitions):
    remote_repo = RemoteRepository(
        RepositorySnap.from_def(defs.get_repository_def()),
        repository_handle=RepositoryHandle.for_test(location_name="loc", repository_name="repo"),
        auto_materialize_use_sensors=True,
    )
    return remote_repo.asset_graph


def _job_context(
    defs: dg.Definitions, job_name: str, instance: dg.DagsterInstance
) -> AutomationContext:
    """Build an AutomationContext for a job key without tripping the evaluator's job-key
    sentinel: the evaluator is seeded with the job's member asset keys, then the context is
    created for the job key directly.
    """
    graph = _local_graph(defs)
    evaluator = AutomationConditionEvaluator(
        entity_keys=graph.asset_keys_for_job(job_name),
        instance=instance,
        asset_graph=graph,
        cursor=AssetDaemonCursor.empty(),
        emit_backfills=False,
        evaluation_id=0,
    )
    return AutomationContext.create(key=AssetJobKey(job_name), evaluator=evaluator)


def _evaluate(
    defs: dg.Definitions, job_name: str, instance: dg.DagsterInstance
) -> AutomationResult:
    context = _job_context(defs, job_name, instance)
    return asyncio.run(context.evaluate_async())


def _materialize(instance: dg.DagsterInstance, *asset_names: str) -> None:
    for name in asset_names:
        instance.report_runless_asset_event(dg.AssetMaterialization(name))


def _diamond_defs(condition: dg.AutomationCondition) -> dg.Definitions:
    """root_a, root_b (roots) -> downstream (non-root)."""

    @dg.asset
    def root_a() -> None: ...

    @dg.asset
    def root_b() -> None: ...

    @dg.asset(deps=[root_a, root_b])
    def downstream() -> None: ...

    job = dg.define_asset_job(
        "my_job", selection=[root_a, root_b, downstream], automation_condition=condition
    )
    return dg.Definitions(assets=[root_a, root_b, downstream], jobs=[job])


# ---------------------------------------------------------------------------
# construction / serialization
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "factory,cls,prefix,operator_type",
    [
        (
            dg.AutomationCondition.all_job_root_assets_match,
            AllJobRootAssetsMatchCondition,
            "all_job_root_assets_match",
            "and",
        ),
        (
            dg.AutomationCondition.any_job_root_assets_match,
            AnyJobRootAssetsMatchCondition,
            "any_job_root_assets_match",
            "or",
        ),
    ],
)
def test_construction_and_serialization(factory, cls, prefix, operator_type) -> None:
    condition = factory(dg.AutomationCondition.missing())

    assert isinstance(condition, cls)
    assert condition.operator_type == operator_type
    assert condition.get_label() == f"{prefix}(missing)"

    assert dg.deserialize_value(dg.serialize_value(condition), cls) == condition


@pytest.mark.parametrize(
    "factory",
    [
        dg.AutomationCondition.all_job_root_assets_match,
        dg.AutomationCondition.any_job_root_assets_match,
    ],
)
def test_operand_is_a_structural_child(factory) -> None:
    # the inner condition must be a child so it participates in identity, serializability,
    # and the snapshot tree
    condition = factory(dg.AutomationCondition.missing())
    assert list(condition.children) == [condition.operand]


@pytest.mark.parametrize(
    "factory",
    [
        dg.AutomationCondition.all_job_root_assets_match,
        dg.AutomationCondition.any_job_root_assets_match,
    ],
)
def test_is_serializable_reflects_operand(factory) -> None:
    class _NonSerializable(BuiltinAutomationCondition):
        def evaluate(self, context):  # pyright: ignore[reportIncompatibleMethodOverride]
            raise NotImplementedError()

    assert factory(dg.AutomationCondition.missing()).is_serializable is True
    # a non-serializable operand must make the whole job condition non-serializable, so the
    # snapshot path (JobSnap.from_job_def) drops it rather than trying to serialize it
    assert factory(_NonSerializable()).is_serializable is False


@pytest.mark.parametrize(
    "factory",
    [
        dg.AutomationCondition.all_job_root_assets_match,
        dg.AutomationCondition.any_job_root_assets_match,
    ],
)
def test_unique_id_depends_on_operand(factory) -> None:
    # different inner conditions must yield different identities (the operand participates
    # in the unique-id hash via children)
    a = factory(dg.AutomationCondition.missing())
    b = factory(dg.AutomationCondition.cron_tick_passed("@daily", "UTC"))
    assert a.get_unique_id() != b.get_unique_id()


# ---------------------------------------------------------------------------
# asset resolution
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("graph_from_defs", [_local_graph, _remote_graph], ids=["local", "remote"])
def test_asset_keys_for_job(graph_from_defs) -> None:
    graph = graph_from_defs(
        _diamond_defs(
            dg.AutomationCondition.all_job_root_assets_match(dg.AutomationCondition.missing())
        )
    )
    assert graph.asset_keys_for_job("my_job") == {
        dg.AssetKey("root_a"),
        dg.AssetKey("root_b"),
        dg.AssetKey("downstream"),
    }


def test_asset_keys_for_job_unknown_job_is_empty() -> None:
    # a job with no automation condition has no graph node, so no asset keys are resolved
    @dg.asset
    def a() -> None: ...

    plain_job = dg.define_asset_job("plain_job", selection=[a])
    defs = dg.Definitions(assets=[a], jobs=[plain_job])
    graph = _local_graph(defs)

    assert graph.asset_keys_for_job("plain_job") == set()
    assert graph.asset_keys_for_job("does_not_exist") == set()


def _operator(condition: dg.AutomationCondition):
    # with_label returns the operator itself (not a wrapper), so the factory result is the op
    assert isinstance(condition, (AllJobRootAssetsMatchCondition, AnyJobRootAssetsMatchCondition))
    return condition


def test_root_asset_keys_diamond() -> None:
    condition = dg.AutomationCondition.all_job_root_assets_match(dg.AutomationCondition.missing())
    graph = _local_graph(_diamond_defs(condition))
    op = _operator(condition)
    key = AssetJobKey("my_job")

    assert op._get_root_asset_keys(key, graph) == {dg.AssetKey("root_a"), dg.AssetKey("root_b")}
    assert op._get_asset_keys(key, graph) == {
        dg.AssetKey("root_a"),
        dg.AssetKey("root_b"),
        dg.AssetKey("downstream"),
    }


def test_root_asset_keys_linear_chain_single_root() -> None:
    @dg.asset
    def a() -> None: ...

    @dg.asset(deps=[a])
    def b() -> None: ...

    @dg.asset(deps=[b])
    def c() -> None: ...

    condition = dg.AutomationCondition.all_job_root_assets_match(dg.AutomationCondition.missing())
    job = dg.define_asset_job("chain", selection=[a, b, c], automation_condition=condition)
    graph = _local_graph(dg.Definitions(assets=[a, b, c], jobs=[job]))

    assert _operator(condition)._get_root_asset_keys(AssetJobKey("chain"), graph) == {
        dg.AssetKey("a")
    }


def test_root_asset_keys_all_independent() -> None:
    @dg.asset
    def x() -> None: ...

    @dg.asset
    def y() -> None: ...

    condition = dg.AutomationCondition.all_job_root_assets_match(dg.AutomationCondition.missing())
    job = dg.define_asset_job("indep", selection=[x, y], automation_condition=condition)
    graph = _local_graph(dg.Definitions(assets=[x, y], jobs=[job]))

    # no in-job dependencies, so every asset is a root
    assert _operator(condition)._get_root_asset_keys(AssetJobKey("indep"), graph) == {
        dg.AssetKey("x"),
        dg.AssetKey("y"),
    }


def test_root_asset_keys_parent_outside_job_still_root() -> None:
    @dg.asset
    def external() -> None: ...

    @dg.asset(deps=[external])
    def in_job() -> None: ...

    condition = dg.AutomationCondition.all_job_root_assets_match(dg.AutomationCondition.missing())
    # `external` is not part of the job, so `in_job`'s only parent is out-of-job -> in_job is a root
    job = dg.define_asset_job("j", selection=[in_job], automation_condition=condition)
    graph = _local_graph(dg.Definitions(assets=[external, in_job], jobs=[job]))

    assert _operator(condition)._get_root_asset_keys(AssetJobKey("j"), graph) == {
        dg.AssetKey("in_job")
    }


# ---------------------------------------------------------------------------
# child context construction
# ---------------------------------------------------------------------------


def test_child_for_asset_key_builds_entity_matches_condition() -> None:
    condition = dg.AutomationCondition.all_job_root_assets_match(dg.AutomationCondition.missing())
    defs = _diamond_defs(condition)
    context = _job_context(defs, "my_job", dg.DagsterInstance.ephemeral())

    child = _operator(condition)._child_for_asset_key(context, 0, dg.AssetKey("root_a"))

    assert isinstance(child.condition, EntityMatchesCondition)
    assert child.condition.key == dg.AssetKey("root_a")
    assert child.condition.operand == condition.operand


# ---------------------------------------------------------------------------
# evaluate()
# ---------------------------------------------------------------------------


def test_all_job_root_assets_match_fires_when_all_roots_missing() -> None:
    defs = _diamond_defs(
        dg.AutomationCondition.all_job_root_assets_match(dg.AutomationCondition.missing())
    )
    instance = dg.DagsterInstance.ephemeral()

    # both roots missing -> all match -> job requested
    assert _evaluate(defs, "my_job", instance).true_subset.size == 1

    # one root materialized -> not all roots missing -> not requested
    _materialize(instance, "root_a")
    assert _evaluate(defs, "my_job", instance).true_subset.size == 0


def test_any_job_root_assets_match_fires_until_all_roots_present() -> None:
    defs = _diamond_defs(
        dg.AutomationCondition.any_job_root_assets_match(dg.AutomationCondition.missing())
    )
    instance = dg.DagsterInstance.ephemeral()

    # both roots missing -> at least one matches -> requested
    assert _evaluate(defs, "my_job", instance).true_subset.size == 1

    # one root still missing -> still requested
    _materialize(instance, "root_a")
    assert _evaluate(defs, "my_job", instance).true_subset.size == 1

    # no roots missing -> not requested
    _materialize(instance, "root_b")
    assert _evaluate(defs, "my_job", instance).true_subset.size == 0


def test_only_roots_are_evaluated() -> None:
    # roots materialized, downstream still missing: only roots are evaluated, so the
    # still-missing downstream does not keep the condition true
    instance = dg.DagsterInstance.ephemeral()
    _materialize(instance, "root_a", "root_b")

    defs = _diamond_defs(
        dg.AutomationCondition.any_job_root_assets_match(dg.AutomationCondition.missing())
    )
    assert _evaluate(defs, "my_job", instance).true_subset.size == 0


def _job_defs(condition: dg.AutomationCondition) -> dg.Definitions:
    @dg.asset
    def root_a() -> None: ...

    @dg.asset
    def root_b() -> None: ...

    @dg.asset(deps=[root_a, root_b])
    def downstream() -> None: ...

    job = dg.define_asset_job(
        "my_job", selection=[root_a, root_b, downstream], automation_condition=condition
    )
    return dg.Definitions(assets=[root_a, root_b, downstream], jobs=[job])


def test_all_job_root_assets_match_missing() -> None:
    defs = _job_defs(
        dg.AutomationCondition.all_job_root_assets_match(dg.AutomationCondition.missing())
    )
    instance = dg.DagsterInstance.ephemeral()

    # all roots missing -> all match -> job requested
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 1

    # materialize one root -> not all roots missing -> job not requested
    instance.report_runless_asset_event(dg.AssetMaterialization("root_a"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0


def test_all_job_root_assets_match_ignores_non_root_child() -> None:
    # a materialized non-root asset must NOT drag the result down: both roots still
    # missing -> all roots match -> job still requested, even though the downstream
    # child is present (only roots are evaluated)
    defs = _job_defs(
        dg.AutomationCondition.all_job_root_assets_match(dg.AutomationCondition.missing())
    )
    instance = dg.DagsterInstance.ephemeral()

    instance.report_runless_asset_event(dg.AssetMaterialization("downstream"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 1


def test_any_job_root_assets_match_missing() -> None:
    defs = _job_defs(
        dg.AutomationCondition.any_job_root_assets_match(dg.AutomationCondition.missing())
    )
    instance = dg.DagsterInstance.ephemeral()

    # both roots missing -> at least one matches -> requested
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 1

    # one root still missing -> still requested
    instance.report_runless_asset_event(dg.AssetMaterialization("root_a"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # both roots materialized -> none missing -> not requested
    instance.report_runless_asset_event(dg.AssetMaterialization("root_b"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0


def test_only_roots_count_for_requests() -> None:
    # After both roots are materialized, only the non-root `downstream` is still missing.
    # Only roots are evaluated, so the still-missing downstream does not keep any() true.
    defs = _job_defs(
        dg.AutomationCondition.any_job_root_assets_match(dg.AutomationCondition.missing())
    )
    instance = dg.DagsterInstance.ephemeral()

    # everything missing -> requested
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 1

    instance.report_runless_asset_event(dg.AssetMaterialization("root_a"))
    instance.report_runless_asset_event(dg.AssetMaterialization("root_b"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0
