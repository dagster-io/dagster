from collections.abc import Iterable

import dagster as dg
from dagster import AssetKey, AutomationCondition, DagsterInstance
from dagster._core.definitions.asset_key import CoercibleToAssetKey
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.declarative_automation.operators.any_downstream_conditions_operator import (
    AnyDownstreamConditionsCondition,
    DownstreamConditionWrapperCondition,
)
from dagster._core.definitions.declarative_automation.operators.boolean_operators import (
    AndAutomationCondition,
    OrAutomationCondition,
)


def _get_result(
    key: CoercibleToAssetKey, results: Iterable[dg.AutomationResult]
) -> dg.AutomationResult:
    key = AssetKey.from_coercible(key)
    for result in results:
        if result.key == key:
            return result
    assert False


def test_basic() -> None:
    cond1 = AutomationCondition.any_downstream_conditions()
    cond2 = AutomationCondition.eager()

    @dg.asset(auto_materialize_policy=cond1.as_auto_materialize_policy())
    def a(): ...

    @dg.asset(auto_materialize_policy=cond2.as_auto_materialize_policy(), deps=[a])
    def b(): ...

    result = dg.evaluate_automation_conditions([a, b], instance=DagsterInstance.ephemeral())

    a_result = _get_result(a.key, result.results)
    assert len(a_result.child_results) == 1
    assert a_result.child_results[0].child_results[0].condition == cond2


def test_basic_with_amp() -> None:
    cond1 = AutomationCondition.any_downstream_conditions()
    cond2 = AutoMaterializePolicy.eager()

    @dg.asset(automation_condition=cond1)
    def a(): ...

    @dg.asset(auto_materialize_policy=cond2, deps=[a])
    def b(): ...

    result = dg.evaluate_automation_conditions([a, b], instance=DagsterInstance.ephemeral())

    a_result = _get_result(a.key, result.results)
    # do not pick up child result
    assert len(a_result.child_results) == 0


def test_multiple_downstreams() -> None:
    cond1 = AutomationCondition.any_downstream_conditions()
    cond2 = AutomationCondition.in_progress()
    cond3 = AutomationCondition.missing()

    @dg.asset(auto_materialize_policy=cond1.as_auto_materialize_policy())
    def a(): ...

    # Left hand side, chain of lazy into two different policies
    @dg.asset(auto_materialize_policy=cond1.as_auto_materialize_policy(), deps=[a])
    def left1(): ...

    @dg.asset(auto_materialize_policy=cond1.as_auto_materialize_policy(), deps=[left1])
    def left2(): ...

    @dg.asset(auto_materialize_policy=cond2.as_auto_materialize_policy(), deps=[left2])
    def b(): ...

    @dg.asset(auto_materialize_policy=cond3.as_auto_materialize_policy(), deps=[left2])
    def c(): ...

    # Right hand side, same policy as b
    @dg.asset(auto_materialize_policy=cond2.as_auto_materialize_policy(), deps=[a])
    def d(): ...

    result = dg.evaluate_automation_conditions(
        [a, left1, left2, b, c, d], instance=DagsterInstance.ephemeral()
    )

    # make sure a has all downstreams
    a_result = _get_result(a.key, result.results)
    assert len(a_result.child_results) == 2

    res1 = a_result.child_results[0]
    assert res1.condition.name == "b, d"
    assert res1.child_results[0].condition == cond2

    res2 = a_result.child_results[1]
    assert res2.condition.name == "c"
    assert res2.child_results[0].condition == cond3


def test_multiple_downstreams_nested() -> None:
    cond1 = AutomationCondition.any_downstream_conditions()
    # combine the lazy condition with another condition, ensure we don't infinite loop
    cond2 = AutomationCondition.any_downstream_conditions() & ~AutomationCondition.in_progress()
    cond3 = AutomationCondition.eager()

    @dg.asset(auto_materialize_policy=cond1.as_auto_materialize_policy())
    def a(): ...

    @dg.asset(auto_materialize_policy=cond2.as_auto_materialize_policy(), deps=[a])
    def b(): ...

    @dg.asset(auto_materialize_policy=cond1.as_auto_materialize_policy(), deps=[b])
    def c(): ...

    # Right hand side, same policy as b
    @dg.asset(auto_materialize_policy=cond3.as_auto_materialize_policy(), deps=[c])
    def d(): ...

    result = dg.evaluate_automation_conditions([a, b, c, d], instance=DagsterInstance.ephemeral())

    # make sure a has all downstreams
    a_result = _get_result(a.key, result.results)
    # b's condition ``adc() & ~in_progress()`` folds to FALSE under the downstream-union
    # simplification (the inner adc() is subsumed by the outer one, so the conjunction with
    # FALSE annihilates), and the entry is dropped. d's eager() is preserved verbatim
    # because it carries the ``eager`` label and is treated as an opaque atom.
    assert len(a_result.child_results) == 1

    only_child = a_result.child_results[0]
    assert only_child.condition.name == "d"
    assert only_child.child_results[0].condition == cond3


def test_collapses_or_with_any_downstream_conditions() -> None:
    """When a downstream asset's condition is ``X | any_downstream_conditions()``, the inner
    ``any_downstream_conditions()`` is redundant from the perspective of an ancestor's
    ``any_downstream_conditions()`` and should be stripped — otherwise the evaluation tree
    grows exponentially deep as the pattern propagates through a long dependency chain.

    Setup:
        A -> B -> C
        Each asset's condition is ``on_cron(<distinct schedule>) | any_downstream_conditions()``.

    Expectation at the root (asset A):
        - A's top-level OR has two children: ``on_cron(a)`` and the ``adc()`` expansion.
        - The ``adc()`` child has one DCWC per distinct downstream key set (B, C).
        - Each DCWC wraps a *flat*, non-recursive condition: just the ``on_cron`` atom.
          It should NOT contain a nested OR with another ``adc()`` inside.
    """
    adc = AutomationCondition.any_downstream_conditions
    cond_a = AutomationCondition.on_cron("@daily") | adc()
    cond_b = AutomationCondition.on_cron("@hourly") | adc()
    cond_c = AutomationCondition.on_cron("0 12 * * *") | adc()

    @dg.asset(automation_condition=cond_a)
    def a(): ...

    @dg.asset(automation_condition=cond_b, deps=[a])
    def b(): ...

    @dg.asset(automation_condition=cond_c, deps=[b])
    def c(): ...

    result = dg.evaluate_automation_conditions([a, b, c], instance=DagsterInstance.ephemeral())

    a_result = _get_result(a.key, result.results)
    assert isinstance(a_result.condition, OrAutomationCondition)
    assert len(a_result.child_results) == 2

    # First child of the top-level OR is on_cron("@daily") — unaffected by collapse.
    on_cron_a_result = a_result.child_results[0]
    assert on_cron_a_result.condition.get_label() == "on_cron(@daily, UTC)"

    # Second child is the any_downstream_conditions() expansion.
    adc_result = a_result.child_results[1]
    assert isinstance(adc_result.condition, AnyDownstreamConditionsCondition)

    # Each downstream key set (B, C) should produce exactly one DCWC child.
    assert len(adc_result.child_results) == 2
    dcwc_by_name = {r.condition.name: r for r in adc_result.child_results}
    assert set(dcwc_by_name.keys()) == {"b", "c"}

    for downstream_name, expected_cron_label in [
        ("b", "on_cron(@hourly, UTC)"),
        ("c", "on_cron(0 12 * * *, UTC)"),
    ]:
        dcwc_result = dcwc_by_name[downstream_name]
        assert isinstance(dcwc_result.condition, DownstreamConditionWrapperCondition)
        # exactly one wrapped operand
        assert len(dcwc_result.child_results) == 1
        wrapped_result = dcwc_result.child_results[0]
        # The wrapped operand should be a flat on_cron atom — NOT an OR containing
        # another any_downstream_conditions().
        assert wrapped_result.condition.get_label() == expected_cron_label, (
            f"Expected DCWC for downstream {downstream_name!r} to wrap a flat "
            f"{expected_cron_label!r} after collapsing the inner adc(), but got "
            f"{wrapped_result.condition!r}"
        )
        # Sanity: no nested adc() should appear anywhere underneath the DCWC.
        _assert_no_nested_adc(wrapped_result)


def _assert_no_nested_adc(result: dg.AutomationResult) -> None:
    assert not isinstance(result.condition, AnyDownstreamConditionsCondition), (
        f"Found nested any_downstream_conditions() under DCWC: {result.condition!r}"
    )
    for child in result.child_results:
        _assert_no_nested_adc(child)


def test_drops_downstream_with_and_adc() -> None:
    """When a downstream condition has the form ``X & adc()``, its unique contribution to the
    enclosing ``adc()``'s union is always FALSE (the inner ``adc()`` is TRUE exactly when some
    other downstream condition is, which already covers that partition). The entry should
    therefore be dropped from the DCWC list entirely.

    Setup:
        A -> B, A -> C
        B: ``on_cron("@hourly") & any_downstream_conditions()``  -- should be dropped
        C: ``on_cron("0 12 * * *")``                              -- should appear

    Expectation: A's ``adc()`` expansion has exactly one DCWC, for C.
    """
    adc = AutomationCondition.any_downstream_conditions
    cond_b = AutomationCondition.on_cron("@hourly") & adc()
    cond_c = AutomationCondition.on_cron("0 12 * * *")

    @dg.asset(automation_condition=adc())
    def a(): ...

    @dg.asset(automation_condition=cond_b, deps=[a])
    def b(): ...

    @dg.asset(automation_condition=cond_c, deps=[a])
    def c(): ...

    result = dg.evaluate_automation_conditions([a, b, c], instance=DagsterInstance.ephemeral())
    a_result = _get_result(a.key, result.results)

    assert isinstance(a_result.condition, AnyDownstreamConditionsCondition)
    assert len(a_result.child_results) == 1
    only_child = a_result.child_results[0]
    assert isinstance(only_child.condition, DownstreamConditionWrapperCondition)
    assert only_child.condition.name == "c"
    assert only_child.child_results[0].condition.get_label() == "on_cron(0 12 * * *, UTC)"


def test_strips_adc_nested_inside_and() -> None:
    """When a downstream condition has the form ``(X | adc()) & Y``, the inner ``adc()`` should
    be substituted with FALSE and folded, producing ``X & Y``. This validates the recursive
    simplification through unlabeled AND/OR nodes.
    """
    adc = AutomationCondition.any_downstream_conditions
    x = AutomationCondition.on_cron("@hourly")
    y = AutomationCondition.on_cron("0 12 * * *")
    cond_b = (x | adc()) & y

    @dg.asset(automation_condition=adc())
    def a(): ...

    @dg.asset(automation_condition=cond_b, deps=[a])
    def b(): ...

    result = dg.evaluate_automation_conditions([a, b], instance=DagsterInstance.ephemeral())
    a_result = _get_result(a.key, result.results)

    assert isinstance(a_result.condition, AnyDownstreamConditionsCondition)
    assert len(a_result.child_results) == 1
    dcwc_result = a_result.child_results[0]
    assert isinstance(dcwc_result.condition, DownstreamConditionWrapperCondition)
    # The wrapped condition should be `X & Y` — an AND of the two on_crons, with no nested adc.
    wrapped = dcwc_result.child_results[0]
    assert isinstance(wrapped.condition, AndAutomationCondition)
    labels = {child.condition.get_label() for child in wrapped.child_results}
    assert labels == {"on_cron(@hourly, UTC)", "on_cron(0 12 * * *, UTC)"}
    _assert_no_nested_adc(dcwc_result)


def test_preserves_labeled_conditions() -> None:
    """A labeled OR/AND should be treated as an opaque atom — we don't peer inside it,
    so even if its definition contains an ``adc()`` underneath, the label tells us it's
    user-defined and should be preserved verbatim.
    """
    adc = AutomationCondition.any_downstream_conditions
    labeled = (AutomationCondition.on_cron("@hourly") | adc()).with_label("my_custom_policy")

    @dg.asset(automation_condition=adc())
    def a(): ...

    @dg.asset(automation_condition=labeled, deps=[a])
    def b(): ...

    result = dg.evaluate_automation_conditions([a, b], instance=DagsterInstance.ephemeral())
    a_result = _get_result(a.key, result.results)

    assert isinstance(a_result.condition, AnyDownstreamConditionsCondition)
    assert len(a_result.child_results) == 1
    dcwc_result = a_result.child_results[0]
    wrapped = dcwc_result.child_results[0]
    # The labeled OR is preserved verbatim, including its inner adc().
    assert wrapped.condition.get_label() == "my_custom_policy"
    assert isinstance(wrapped.condition, OrAutomationCondition)


def test_collapses_tangled_graph_with_three_unique_conditions() -> None:
    r"""Tangled multi-path graph (with diamonds and shared descendants) where seven downstream
    assets share only three distinct ``X | adc()`` conditions. After simplification, A's
    outer ``adc()`` should produce exactly three DCWC children — one per distinct
    condition — with the correct merged asset-key sets.

    Edges: A->B, A->C, B->D, B->E, C->D, C->F, D->G, E->G, F->H, G->H

    Condition assignments::

        cond_hourly   = on_cron("@hourly")  | adc()   used by: D, H
        cond_daily    = on_cron("@daily")   | adc()   used by: B, E, G
        cond_minutely = on_cron("*/5 * * *") | adc()  used by: C, F

    After collapse, A's ``adc()`` should yield three DCWC children. Importantly, the
    transitive descendants behind each DCWC's ``downstream_keys`` reflect *every* asset
    using that condition — not just the direct children of A.
    """
    adc = AutomationCondition.any_downstream_conditions
    cond_hourly = AutomationCondition.on_cron("@hourly") | adc()
    cond_daily = AutomationCondition.on_cron("@daily") | adc()
    cond_minutely = AutomationCondition.on_cron("*/5 * * * *") | adc()

    @dg.asset(automation_condition=adc())
    def a(): ...

    @dg.asset(automation_condition=cond_daily, deps=[a])
    def b(): ...

    @dg.asset(automation_condition=cond_minutely, deps=[a])
    def c(): ...

    @dg.asset(automation_condition=cond_hourly, deps=[b, c])
    def d(): ...

    @dg.asset(automation_condition=cond_daily, deps=[b])
    def e(): ...

    @dg.asset(automation_condition=cond_minutely, deps=[c])
    def f(): ...

    @dg.asset(automation_condition=cond_daily, deps=[d, e])
    def g(): ...

    @dg.asset(automation_condition=cond_hourly, deps=[f, g])
    def h(): ...

    result = dg.evaluate_automation_conditions(
        [a, b, c, d, e, f, g, h], instance=DagsterInstance.ephemeral()
    )
    a_result = _get_result(a.key, result.results)

    # A's condition is plain adc(), so the top-level result *is* the outer adc() expansion.
    assert isinstance(a_result.condition, AnyDownstreamConditionsCondition)

    # Exactly three DCWC children — one per distinct downstream condition. No matter how
    # many assets share a condition, they collapse into a single DCWC entry.
    assert len(a_result.child_results) == 3

    # Index by the simplified atom's label so we can assert independent of iteration order.
    by_label: dict[str, tuple[set, dg.AutomationResult]] = {}
    for dcwc_result in a_result.child_results:
        assert isinstance(dcwc_result.condition, DownstreamConditionWrapperCondition)
        wrapped = dcwc_result.child_results[0]
        label = wrapped.condition.get_label()
        assert label is not None, (
            f"Each DCWC should wrap a flat labeled on_cron atom; got {wrapped.condition!r}"
        )
        by_label[label] = (set(dcwc_result.condition.downstream_keys), wrapped)

    assert set(by_label.keys()) == {
        "on_cron(@hourly, UTC)",
        "on_cron(@daily, UTC)",
        "on_cron(*/5 * * * *, UTC)",
    }

    # Each DCWC's downstream_keys is the merged set of *all* descendants of A that share
    # the condition — including transitive descendants reached through multiple paths.
    assert by_label["on_cron(@hourly, UTC)"][0] == {d.key, h.key}
    assert by_label["on_cron(@daily, UTC)"][0] == {b.key, e.key, g.key}
    assert by_label["on_cron(*/5 * * * *, UTC)"][0] == {c.key, f.key}

    # Every wrapped operand should be a flat on_cron atom with no residual nested adc().
    for _, wrapped in by_label.values():
        _assert_no_nested_adc(wrapped)
