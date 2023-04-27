from dagster import AutoMaterializePolicy
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicyType


def test_type():
    assert AutoMaterializePolicy.eager().policy_type == AutoMaterializePolicyType.EAGER
    assert AutoMaterializePolicy.lazy().policy_type == AutoMaterializePolicyType.LAZY
