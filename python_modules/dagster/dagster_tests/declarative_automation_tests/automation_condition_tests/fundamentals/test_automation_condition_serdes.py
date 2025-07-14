import dagster as dg


def test_deserialize_no_imports() -> None:
    serialized = """
    {"__class__": "AndAssetCondition", "operands": [{"__class__": "InLatestTimeWindowCondition", "serializable_lookback_timedelta": null}, {"__class__": "SinceCondition", "reset_condition": {"__class__": "NewlyRequestedCondition"}, "trigger_condition": {"__class__": "CronTickPassedCondition", "cron_schedule": "0 * * * *", "cron_timezone": "UTC"}}, {"__class__": "AllDepsCondition", "allow_selection": null, "ignore_selection": null, "operand": {"__class__": "OrAssetCondition", "operands": [{"__class__": "SinceCondition", "reset_condition": {"__class__": "CronTickPassedCondition", "cron_schedule": "0 * * * *", "cron_timezone": "UTC"}, "trigger_condition": {"__class__": "NewlyUpdatedCondition"}}, {"__class__": "WillBeRequestedCondition"}]}}]}
    """
    deserialized = dg.deserialize_value(serialized)

    # defer import so AutomationCondition doesn't get whitelisted incidentally

    assert isinstance(deserialized, dg.AutomationCondition)
