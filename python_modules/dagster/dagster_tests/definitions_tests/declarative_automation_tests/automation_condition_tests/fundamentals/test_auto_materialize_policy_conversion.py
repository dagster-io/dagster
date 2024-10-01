import dagster._check as check
from dagster import (
    AutoMaterializePolicy,
    AutomationCondition,
    Definitions,
    asset,
    deserialize_value,
    serialize_value,
)


def test_round_trip_conversion() -> None:
    assert AutomationCondition.eager().is_serializable
    policy = AutomationCondition.eager().as_auto_materialize_policy()
    serialized_policy = serialize_value(policy)
    deserialized_policy = deserialize_value(serialized_policy, AutoMaterializePolicy)
    assert policy == deserialized_policy
    assert deserialized_policy.asset_condition == AutomationCondition.eager()


def test_defs() -> None:
    @asset(auto_materialize_policy=AutomationCondition.eager().as_auto_materialize_policy())
    def my_asset() -> None: ...

    defs = Definitions(assets=[my_asset])

    asset_graph_amp = defs.get_asset_graph().get(my_asset.key).auto_materialize_policy
    assert check.not_none(asset_graph_amp).to_automation_condition() == AutomationCondition.eager()
