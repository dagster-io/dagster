import dagster as dg
import pytest
from dagster import AutomationCondition, DagsterInstance


@pytest.mark.parametrize(
    "condition,expected_name",
    [
        (
            AutomationCondition.executed_with_tags(tag_keys={"foo"}),
            "executed_with_tags(tag_keys={foo})",
        ),
        (
            AutomationCondition.executed_with_tags(tag_values={"foo": "bar", "baz": "1"}),
            "executed_with_tags(tag_values={baz:1,foo:bar})",
        ),
        (
            AutomationCondition.executed_with_tags(
                tag_keys={"a", "b"}, tag_values={"foo": "bar", "baz": "1"}
            ),
            "executed_with_tags(tag_keys={a,b}, tag_values={baz:1,foo:bar})",
        ),
    ],
)
def test_name(condition: AutomationCondition, expected_name: str) -> None:
    assert condition.name == expected_name


def test_executed_with_tag_keys() -> None:
    @dg.asset(
        automation_condition=AutomationCondition.newly_updated()
        & AutomationCondition.executed_with_tags(tag_keys={"target_tag"})
    )
    def A() -> None: ...

    defs = dg.Definitions(assets=[A])
    instance = DagsterInstance.ephemeral()
    job = defs.resolve_implicit_global_asset_job_def()

    # hasn't newly updated
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 0

    # now updates, no tags
    job.execute_in_process(instance=instance)
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # now updates via automation system
    job.execute_in_process(instance=instance, tags={"target_tag": "true"})
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # no longer newly updated
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # updates, but not via automation system
    instance.report_runless_asset_event(dg.AssetMaterialization("A"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # updates via automation system
    job.execute_in_process(instance=instance, tags={"target_tag": "true"})
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # updates via automation system
    job.execute_in_process(
        instance=instance, tags={"target_tag": "true", "non_target_tag": "false"}
    )
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    job.execute_in_process(instance=instance, tags={"non_target_tag": "false"})
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0


def test_executed_with_tag_values() -> None:
    @dg.asset(
        automation_condition=AutomationCondition.newly_updated()
        & AutomationCondition.executed_with_tags(tag_values={"target_tag": "a"})
    )
    def A() -> None: ...

    defs = dg.Definitions(assets=[A])
    instance = DagsterInstance.ephemeral()
    job = defs.resolve_implicit_global_asset_job_def()

    # hasn't newly updated
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance)
    assert result.total_requested == 0

    # now updates, but it was a manual run
    job.execute_in_process(instance=instance)
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # now updates with tag, but wrong value
    job.execute_in_process(instance=instance, tags={"target_tag": "b"})
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # now updates with tag, correct value
    job.execute_in_process(instance=instance, tags={"target_tag": "a"})
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    # no longer newly updated
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # updates, no run
    instance.report_runless_asset_event(dg.AssetMaterialization("A"))
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0

    # updates via automation system
    job.execute_in_process(instance=instance, tags={"target_tag": "a"})
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    job.execute_in_process(instance=instance, tags={"target_tag": "a", "non_target_tag": "b"})
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 1

    job.execute_in_process(instance=instance, tags={"non_target_tag": "b"})
    result = dg.evaluate_automation_conditions(defs=defs, instance=instance, cursor=result.cursor)
    assert result.total_requested == 0
