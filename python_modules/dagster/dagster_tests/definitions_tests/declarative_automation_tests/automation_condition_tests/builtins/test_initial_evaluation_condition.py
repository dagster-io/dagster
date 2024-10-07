from typing import Optional, Sequence

import dagster as dg
from dagster._core.definitions.declarative_automation.automation_condition_tester import (
    EvaluateAutomationConditionsResult,
)


def test_update_on_partitions_def_change() -> None:
    """We should update whenever the partitions definition changes."""

    def _get_defs(pd: Optional[dg.PartitionsDefinition]) -> dg.Definitions:
        @dg.asset(
            partitions_def=pd, automation_condition=dg.AutomationCondition.initial_evaluation()
        )
        def a() -> None: ...

        return dg.Definitions(assets=[a])

    instance = dg.DagsterInstance.ephemeral()
    unpartitioned_defs = _get_defs(None)
    static_partitioned_defs = _get_defs(dg.StaticPartitionsDefinition(["a", "b"]))

    result = dg.evaluate_automation_conditions(defs=unpartitioned_defs, instance=instance)
    assert result.total_requested == 1

    result = dg.evaluate_automation_conditions(
        defs=unpartitioned_defs, instance=instance, cursor=result.cursor
    )
    assert result.total_requested == 0

    result = dg.evaluate_automation_conditions(
        defs=unpartitioned_defs, instance=instance, cursor=result.cursor
    )
    assert result.total_requested == 0

    # change partitions definition
    result = dg.evaluate_automation_conditions(
        defs=static_partitioned_defs, instance=instance, cursor=result.cursor
    )
    assert result.total_requested == 2

    result = dg.evaluate_automation_conditions(
        defs=static_partitioned_defs, instance=instance, cursor=result.cursor
    )
    assert result.total_requested == 0

    # change it back
    result = dg.evaluate_automation_conditions(
        defs=unpartitioned_defs, instance=instance, cursor=result.cursor
    )
    assert result.total_requested == 1


def _get_initial_evaluation_count(result: EvaluateAutomationConditionsResult) -> int:
    def _result_iter(r):
        yield r
        for cr in r.child_results:
            yield from _result_iter(cr)

    assert len(result.results) == 1
    initial_evaluation_result = next(
        r
        for r in _result_iter(result.results[0])
        if type(r.condition) == type(dg.AutomationCondition.initial_evaluation())
    )
    return initial_evaluation_result.true_subset.size


def test_update_on_condition_change() -> None:
    """We should update whenever the condition is changed in any way."""

    def _get_defs(ac: dg.AutomationCondition) -> dg.Definitions:
        @dg.asset(automation_condition=ac, deps=["up"])
        def a() -> None: ...

        return dg.Definitions(assets=[a])

    instance = dg.DagsterInstance.ephemeral()
    base_condition = dg.AutomationCondition.initial_evaluation()

    # initial evaluation
    base_result = dg.evaluate_automation_conditions(
        defs=_get_defs(base_condition), instance=instance
    )
    assert _get_initial_evaluation_count(base_result) == 1

    for condition in [
        # add condition before
        ~dg.AutomationCondition.any_deps_in_progress() & base_condition,
        # add condition after
        base_condition & ~dg.AutomationCondition.any_deps_missing(),
        # sandwich!
        ~dg.AutomationCondition.any_deps_in_progress()
        & base_condition
        & dg.AutomationCondition.code_version_changed(),
        # weird cases
        base_condition.newly_true(),
        base_condition.since(base_condition),
        dg.AutomationCondition.any_deps_match(base_condition),
    ]:
        # first tick, should recognize the change
        result = dg.evaluate_automation_conditions(
            # note: doing relative to the base result cursor
            defs=_get_defs(condition),
            instance=instance,
            cursor=base_result.cursor,
        )
        assert _get_initial_evaluation_count(result) == 1

        # second tick, new normal
        result = dg.evaluate_automation_conditions(
            defs=_get_defs(condition), instance=instance, cursor=result.cursor
        )
        assert _get_initial_evaluation_count(result) == 0


def test_no_update_on_new_deps() -> None:
    def _get_defs(deps: Sequence[str]) -> dg.Definitions:
        @dg.multi_asset(specs=[dg.AssetSpec(d) for d in deps])
        def m(): ...

        @dg.asset(
            automation_condition=dg.AutomationCondition.initial_evaluation()
            & dg.AutomationCondition.any_deps_in_progress(),
            deps=deps,
        )
        def downstream() -> None: ...

        return dg.Definitions(assets=[downstream, m])

    instance = dg.DagsterInstance.ephemeral()

    # initial evaluation
    base_result = dg.evaluate_automation_conditions(defs=_get_defs(["a", "b"]), instance=instance)
    assert _get_initial_evaluation_count(base_result) == 1

    for deps in [[], ["a"], ["c"], ["a", "b", "c"]]:
        # no changes should be recognized
        result = dg.evaluate_automation_conditions(
            # note: doing relative to the base result cursor
            defs=_get_defs(deps),
            instance=instance,
            cursor=base_result.cursor,
        )
        assert _get_initial_evaluation_count(result) == 0
