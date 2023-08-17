from dagster import AutoMaterializePolicy
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicyType
from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule
from dagster._check import CheckError
import pytest


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
        }
    )

    even_less_eager = less_eager.without_rules(
        AutoMaterializeRule.materialize_on_required_for_freshness(),
        AutoMaterializeRule.materialize_on_parent_updated(),
    )

    assert even_less_eager == AutoMaterializePolicy(
        rules={AutoMaterializeRule.skip_on_parent_outdated()}
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
            AutoMaterializeRule.materialize_on_required_for_freshness(),
        )
        == AutoMaterializePolicy.eager()
    )


def test_serialized_auto_materialize_backcompat():
    serialized_amp = ""
    assert deserialize_json_to_dagster_namedtuple(serialized_amp) == AutoMaterializePolicy.eager()
