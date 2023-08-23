import pytest
from dagster import AutoMaterializePolicy
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicyType
from dagster._serdes import deserialize_value


def test_type():
    assert AutoMaterializePolicy.eager().policy_type == AutoMaterializePolicyType.EAGER
    assert AutoMaterializePolicy.lazy().policy_type == AutoMaterializePolicyType.LAZY


@pytest.mark.parametrize(
    "future_serialized_policy,expected_policy",
    [
        (
            (
                '{"__class__": "AutoMaterializePolicy", "max_materializations_per_minute": 1,'
                ' "rules": {"__frozenset__": [{"__class__": "MaterializeOnMissingRule"},'
                ' {"__class__": "MaterializeOnParentUpdatedRule"}, {"__class__":'
                ' "MaterializeOnRequiredForFreshnessRule"}, {"__class__":'
                ' "SkipOnParentOutdatedRule"}]}, "time_window_partition_scope_minutes": 1e-06}'
            ),
            AutoMaterializePolicy.eager(),
        ),
        (
            (
                '{"__class__": "AutoMaterializePolicy", "max_materializations_per_minute": 1,'
                ' "rules": {"__frozenset__": [{"__class__":'
                ' "MaterializeOnRequiredForFreshnessRule"}, {"__class__":'
                ' "SkipOnParentOutdatedRule"}]}, "time_window_partition_scope_minutes": 1e-06}'
            ),
            AutoMaterializePolicy.lazy(),
        ),
    ],
)
def test_forwards_compat(future_serialized_policy, expected_policy):
    assert deserialize_value(future_serialized_policy) == expected_policy
