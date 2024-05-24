import pytest
from dagster import AssetKey, AutoMaterializePolicy
from dagster._check import CheckError
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicyType
from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule
from dagster._core.definitions.auto_materialize_rule_evaluation import (
    AutoMaterializeRuleEvaluation,
    ParentUpdatedRuleEvaluationData,
    WaitingOnAssetsRuleEvaluationData,
)
from dagster._core.definitions.auto_materialize_rule_impls import (
    DiscardOnMaxMaterializationsExceededRule,
)
from dagster._serdes import deserialize_value, serialize_value


def test_type():
    assert AutoMaterializePolicy.eager().policy_type == AutoMaterializePolicyType.EAGER
    assert AutoMaterializePolicy.lazy().policy_type == AutoMaterializePolicyType.LAZY


def test_without_rules():
    eager = AutoMaterializePolicy.eager()

    less_eager = eager.without_rules(AutoMaterializeRule.materialize_on_missing())

    assert less_eager == AutoMaterializePolicy(
        rules={
            AutoMaterializeRule.materialize_on_parent_updated(),
            AutoMaterializeRule.materialize_on_required_for_freshness(),
            AutoMaterializeRule.skip_on_parent_outdated(),
            AutoMaterializeRule.skip_on_parent_missing(),
            AutoMaterializeRule.skip_on_required_but_nonexistent_parents(),
            AutoMaterializeRule.skip_on_backfill_in_progress(),
        }
    )

    even_less_eager = less_eager.without_rules(
        AutoMaterializeRule.materialize_on_required_for_freshness(),
        AutoMaterializeRule.materialize_on_parent_updated(),
    )

    assert even_less_eager == AutoMaterializePolicy(
        rules={
            AutoMaterializeRule.skip_on_parent_outdated(),
            AutoMaterializeRule.skip_on_parent_missing(),
            AutoMaterializeRule.skip_on_required_but_nonexistent_parents(),
            AutoMaterializeRule.skip_on_backfill_in_progress(),
        }
    )


def test_without_rules_invalid():
    simple_policy = AutoMaterializePolicy(
        rules={AutoMaterializeRule.materialize_on_parent_updated()}
    )

    with pytest.raises(
        CheckError,
        match=(
            r"Rules \[MaterializeOnMissingRule\(\), SkipOnParentOutdatedRule\(\)\] do not exist in"
            r" this policy."
        ),
    ):
        simple_policy.without_rules(
            AutoMaterializeRule.materialize_on_missing(),
            AutoMaterializeRule.skip_on_parent_outdated(),
            AutoMaterializeRule.materialize_on_parent_updated(),
        )


def test_with_rules():
    simple_policy = AutoMaterializePolicy(
        rules={AutoMaterializeRule.materialize_on_parent_updated()}
    )

    assert (
        simple_policy.with_rules(
            AutoMaterializeRule.materialize_on_missing(),
            AutoMaterializeRule.skip_on_parent_outdated(),
            AutoMaterializeRule.skip_on_parent_missing(),
            AutoMaterializeRule.materialize_on_required_for_freshness(),
            AutoMaterializeRule.skip_on_required_but_nonexistent_parents(),
            AutoMaterializeRule.skip_on_backfill_in_progress(),
        )
        == AutoMaterializePolicy.eager()
    )


def test_with_rules_override_existing_instance():
    simple_policy = AutoMaterializePolicy(
        rules={
            AutoMaterializeRule.materialize_on_parent_updated(),
            AutoMaterializeRule.skip_on_backfill_in_progress(),
        }
    )

    simple_policy_with_override = simple_policy.with_rules(
        AutoMaterializeRule.skip_on_backfill_in_progress(all_partitions=True),
    )

    assert simple_policy_with_override.rules == {
        AutoMaterializeRule.skip_on_backfill_in_progress(all_partitions=True),
        AutoMaterializeRule.materialize_on_parent_updated(),
    }


@pytest.mark.parametrize(
    "serialized_amp, expected_amp",
    [
        (
            (
                '{"__class__": "AutoMaterializePolicy", "for_freshness": true,'
                ' "max_materializations_per_minute": 1, "on_missing": true, "on_new_parent_data":'
                ' true, "time_window_partition_scope_minutes": 1e-06}'
            ),
            AutoMaterializePolicy.eager(),
        ),
        (
            (
                '{"__class__": "AutoMaterializePolicy", "for_freshness": true,'
                ' "max_materializations_per_minute": 1, "on_missing": false, "on_new_parent_data":'
                ' false, "time_window_partition_scope_minutes": 1e-06}'
            ),
            AutoMaterializePolicy.lazy(),
        ),
        (
            (
                '{"__class__": "AutoMaterializePolicy", "for_freshness": true,'
                ' "max_materializations_per_minute": 15, "on_missing": false, "on_new_parent_data":'
                ' true, "time_window_partition_scope_minutes": 1e-06}'
            ),
            AutoMaterializePolicy.eager(max_materializations_per_minute=15).without_rules(
                AutoMaterializeRule.materialize_on_missing()
            ),
        ),
    ],
)
def test_serialized_auto_materialize_backcompat(
    serialized_amp: str, expected_amp: AutoMaterializePolicy
):
    assert deserialize_value(serialized_amp) == expected_amp
    assert deserialize_value(serialize_value(expected_amp)) == expected_amp


@pytest.mark.parametrize(
    "serialized_condition, expected_rule_evaluation",
    [
        (
            (
                '{"__class__": "MissingAutoMaterializeCondition", "decision_type": {"__enum__":'
                ' "AutoMaterializeDecisionType.MATERIALIZE"}}'
            ),
            AutoMaterializeRuleEvaluation(
                rule_snapshot=AutoMaterializeRule.materialize_on_missing().to_snapshot(),
                evaluation_data=None,
            ),
        ),
        (
            (
                '{"__class__": "ParentMaterializedAutoMaterializeCondition", "decision_type":'
                ' {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "updated_asset_keys":'
                ' null, "will_update_asset_keys": null}'
            ),
            AutoMaterializeRuleEvaluation(
                rule_snapshot=AutoMaterializeRule.materialize_on_parent_updated().to_snapshot(),
                evaluation_data=ParentUpdatedRuleEvaluationData(
                    updated_asset_keys=frozenset(), will_update_asset_keys=frozenset()
                ),
            ),
        ),
        (
            (
                '{"__class__": "ParentMaterializedAutoMaterializeCondition", "decision_type":'
                ' {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}, "updated_asset_keys":'
                ' {"__set__": [{"__class__": "AssetKey", "path": ["bar"]}, {"__class__":'
                ' "AssetKey", "path": ["foo"]}]}, "will_update_asset_keys": {"__set__":'
                ' [{"__class__": "AssetKey", "path": ["bar2"]}, {"__class__": "AssetKey", "path":'
                ' ["foo2"]}]}}'
            ),
            AutoMaterializeRuleEvaluation(
                rule_snapshot=AutoMaterializeRule.materialize_on_parent_updated().to_snapshot(),
                evaluation_data=ParentUpdatedRuleEvaluationData(
                    updated_asset_keys=frozenset([AssetKey("foo"), AssetKey("bar")]),
                    will_update_asset_keys=frozenset([AssetKey("foo2"), AssetKey("bar2")]),
                ),
            ),
        ),
        (
            (
                '{"__class__": "FreshnessAutoMaterializeCondition", "decision_type": {"__enum__":'
                ' "AutoMaterializeDecisionType.MATERIALIZE"}}'
            ),
            AutoMaterializeRuleEvaluation(
                rule_snapshot=AutoMaterializeRule.materialize_on_required_for_freshness().to_snapshot(),
                evaluation_data=None,
            ),
        ),
        (
            (
                '{"__class__": "DownstreamFreshnessAutoMaterializeCondition", "decision_type":'
                ' {"__enum__": "AutoMaterializeDecisionType.MATERIALIZE"}}'
            ),
            AutoMaterializeRuleEvaluation(
                rule_snapshot=AutoMaterializeRule.materialize_on_required_for_freshness().to_snapshot(),
                evaluation_data=None,
            ),
        ),
        (
            (
                '{"__class__": "ParentOutdatedAutoMaterializeCondition", "decision_type":'
                ' {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "waiting_on_asset_keys": null}'
            ),
            AutoMaterializeRuleEvaluation(
                rule_snapshot=AutoMaterializeRule.skip_on_parent_outdated().to_snapshot(),
                evaluation_data=WaitingOnAssetsRuleEvaluationData(
                    waiting_on_asset_keys=frozenset(),
                ),
            ),
        ),
        (
            (
                '{"__class__": "ParentOutdatedAutoMaterializeCondition", "decision_type":'
                ' {"__enum__": "AutoMaterializeDecisionType.SKIP"}, "waiting_on_asset_keys":'
                ' {"__set__": [{"__class__": "AssetKey", "path": ["bar"]}, {"__class__":'
                ' "AssetKey", "path": ["foo"]}]}}'
            ),
            AutoMaterializeRuleEvaluation(
                rule_snapshot=AutoMaterializeRule.skip_on_parent_outdated().to_snapshot(),
                evaluation_data=WaitingOnAssetsRuleEvaluationData(
                    waiting_on_asset_keys=frozenset({AssetKey("foo"), AssetKey("bar")})
                ),
            ),
        ),
        (
            (
                '{"__class__": "MaxMaterializationsExceededAutoMaterializeCondition",'
                ' "decision_type": {"__enum__": "AutoMaterializeDecisionType.DISCARD"}}'
            ),
            AutoMaterializeRuleEvaluation(
                rule_snapshot=DiscardOnMaxMaterializationsExceededRule(limit=1).to_snapshot(),
                evaluation_data=None,
            ),
        ),
    ],
)
def test_serialized_auto_materialize_condition_backcompat(
    serialized_condition: str, expected_rule_evaluation: AutoMaterializeRuleEvaluation
):
    assert deserialize_value(serialized_condition) == expected_rule_evaluation
    assert deserialize_value(serialize_value(expected_rule_evaluation)) == expected_rule_evaluation
