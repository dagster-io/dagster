from types import SimpleNamespace

from dagster._utils.tags import TagConcurrencyLimitsCounter


def _item(**tags):
    return SimpleNamespace(tags=tags)


def test_copy_is_independent():
    counter = TagConcurrencyLimitsCounter(
        [
            {"key": "database", "limit": 2},
            {"key": "team", "value": "a", "limit": 1},
            {"key": "region", "value": {"applyLimitPerUniqueValue": True}, "limit": 1},
        ],
        [_item(database="x", team="a", region="us")],
    )

    copied = counter.copy()
    copied.update_counters_with_launched_item(_item(database="y", region="eu"))

    # The copy starts from the original counts...
    assert copied.is_blocked(_item(team="a"))
    assert copied.is_blocked(_item(region="us"))
    # ...and counting on the copy leaves the original unchanged.
    assert copied.is_blocked(_item(database="z"))
    assert copied.is_blocked(_item(region="eu"))
    assert not counter.is_blocked(_item(database="z"))
    assert not counter.is_blocked(_item(region="eu"))
