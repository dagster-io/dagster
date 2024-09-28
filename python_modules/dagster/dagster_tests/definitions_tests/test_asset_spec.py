import pytest
from dagster import AssetSpec, AutoMaterializePolicy, AutomationCondition
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError


def test_validate_asset_owner() -> None:
    with pytest.raises(DagsterInvalidDefinitionError, match="Invalid owner"):
        AssetSpec(key="asset1", owners=["owner@$#&*1"])


def test_validate_group_name() -> None:
    with pytest.raises(DagsterInvalidDefinitionError, match="is not a valid name"):
        AssetSpec(key="asset1", group_name="group@$#&*1")

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Empty asset group name was provided, which is not permitted",
    ):
        AssetSpec(key="asset1", group_name="")


def test_resolve_automation_condition() -> None:
    ac_spec = AssetSpec(key="asset1", automation_condition=AutomationCondition.eager())
    assert isinstance(ac_spec.auto_materialize_policy, AutoMaterializePolicy)
    assert isinstance(ac_spec.automation_condition, AutomationCondition)

    amp_spec = AssetSpec(key="asset1", auto_materialize_policy=AutoMaterializePolicy.eager())
    assert isinstance(amp_spec.auto_materialize_policy, AutoMaterializePolicy)
    assert isinstance(amp_spec.automation_condition, AutomationCondition)

    with pytest.raises(
        DagsterInvariantViolationError,
        match="both `automation_condition` and `auto_materialize_policy`",
    ):
        AssetSpec(
            key="asset1",
            automation_condition=AutomationCondition.eager(),
            auto_materialize_policy=AutoMaterializePolicy.eager(),
        )
