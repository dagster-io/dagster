"""Tests that CronTickPassedCondition evaluations sharing a cron schedule are memoized
within a single automation tick.
"""

import datetime
from unittest import mock

import dagster as dg
from dagster import AutomationCondition
from dagster._core.asset_graph_view import asset_graph_view as agv_module
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView


def test_compute_previous_cron_tick_is_cached_per_view() -> None:
    """Direct unit test: AssetGraphView.compute_previous_cron_tick caches by
    (cron_schedule, cron_timezone) for the lifetime of the view.
    """
    effective_dt = datetime.datetime(2024, 6, 1, 12, 30, tzinfo=datetime.timezone.utc)
    view = AssetGraphView.for_test(dg.Definitions(), effective_dt=effective_dt)

    with mock.patch.object(
        agv_module, "reverse_cron_string_iterator", wraps=agv_module.reverse_cron_string_iterator
    ) as spy:
        tick_a1 = view.compute_previous_cron_tick(cron_schedule="0 * * * *", cron_timezone="UTC")
        tick_a2 = view.compute_previous_cron_tick(cron_schedule="0 * * * *", cron_timezone="UTC")
        assert tick_a1 == tick_a2
        assert spy.call_count == 1

        # Different schedule -> separate cache entry, one additional call.
        view.compute_previous_cron_tick(cron_schedule="*/15 * * * *", cron_timezone="UTC")
        assert spy.call_count == 2

        # Same schedule, different timezone -> separate cache entry.
        view.compute_previous_cron_tick(
            cron_schedule="0 * * * *", cron_timezone="America/Los_Angeles"
        )
        assert spy.call_count == 3

    # A fresh view (== a fresh tick) discards the cache.
    fresh_view = AssetGraphView.for_test(dg.Definitions(), effective_dt=effective_dt)
    with mock.patch.object(
        agv_module, "reverse_cron_string_iterator", wraps=agv_module.reverse_cron_string_iterator
    ) as spy:
        fresh_view.compute_previous_cron_tick(cron_schedule="0 * * * *", cron_timezone="UTC")
        assert spy.call_count == 1


def test_cron_tick_passed_shared_across_assets_in_one_tick() -> None:
    """Multiple assets sharing a cron schedule should trigger a single cron computation
    per tick (per unique schedule + timezone).
    """
    shared = AutomationCondition.cron_tick_passed(cron_schedule="0 * * * *", cron_timezone="UTC")
    other = AutomationCondition.cron_tick_passed(cron_schedule="*/30 * * * *", cron_timezone="UTC")

    @dg.asset(automation_condition=shared)
    def A() -> None: ...

    @dg.asset(automation_condition=shared)
    def B() -> None: ...

    @dg.asset(automation_condition=shared)
    def C() -> None: ...

    @dg.asset(automation_condition=other)
    def D() -> None: ...

    instance = dg.DagsterInstance.ephemeral()

    with mock.patch.object(
        agv_module, "reverse_cron_string_iterator", wraps=agv_module.reverse_cron_string_iterator
    ) as spy:
        # Tick that crosses both schedules.
        dg.evaluate_automation_conditions(
            defs=[A, B, C, D],
            instance=instance,
            evaluation_time=datetime.datetime(2020, 2, 2, 1, 5),
        )
        # Two unique (schedule, timezone) keys across four assets -> exactly two calls.
        assert spy.call_count == 2
