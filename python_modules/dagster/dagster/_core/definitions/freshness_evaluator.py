"""Evaluators for each freshness policy type."""

from abc import ABC, abstractmethod

import structlog

import dagster._check as check
from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetNode
from dagster._core.definitions.freshness import (
    CronFreshnessPolicy,
    FreshnessState,
    InternalFreshnessPolicy,
    TimeWindowFreshnessPolicy,
)
from dagster._core.storage.event_log.base import AssetRecord
from dagster._core.workspace.context import LoadingContext
from dagster._time import get_current_datetime, get_current_timestamp
from dagster._utils.schedules import get_latest_completed_cron_tick

logger = structlog.get_logger(__name__)


# IMPROVEME [OPER-1796] move to oss
class FreshnessPolicyEvaluator(ABC):
    """Abstract base class for freshness policy evaluators.
    Do not implement this class, implement subclasses for each policy type.
    """

    @abstractmethod
    async def evaluate_freshness(
        self, context: LoadingContext, node: BaseAssetNode
    ) -> FreshnessState:
        """Evaluate the freshness of an asset based on the freshness policy, returning the corresponding FreshnessState."""
        raise NotImplementedError("Subclasses must implement this method")


# IMPROVEME [OPER-1796] move to oss
class TimeWindowFreshnessPolicyEvaluator(FreshnessPolicyEvaluator):
    policy_type = TimeWindowFreshnessPolicy

    async def evaluate_freshness(
        self, context: LoadingContext, node: BaseAssetNode
    ) -> FreshnessState:
        """Evaluate the freshness state of an asset based on the time window freshness policy.
        If the asset has no materialization events, return UNKNOWN.
        If the asset was materialized within the policy time window, return PASS.
        If the asset was materialized outside the policy time window, return FAIL.
        If the asset was materialized within the policy time window but outside the warning time window (if provided), return WARN.
        """
        freshness_policy = check.not_none(node.freshness_policy_or_from_metadata)

        time_window_policy = check.inst(
            freshness_policy,
            self.policy_type,
            f"Expected freshness policy type {self.policy_type}, got {freshness_policy.__class__}",
        )

        record = await AssetRecord.gen(context, node.key)
        latest_materialization_event = record.asset_entry.last_materialization if record else None
        if not latest_materialization_event:
            # Freshness cannot be evaluated if there are no materialization events
            return FreshnessState.UNKNOWN

        current_timestamp = get_current_timestamp()
        latest_materialization_timestamp = latest_materialization_event.timestamp

        seconds_since_last_materialization = current_timestamp - latest_materialization_timestamp

        warn_threshold_seconds = (
            time_window_policy.warn_window.to_timedelta().total_seconds()
            if time_window_policy.warn_window
            else None
        )
        fail_threshold_seconds = time_window_policy.fail_window.to_timedelta().total_seconds()

        if seconds_since_last_materialization >= fail_threshold_seconds:
            return FreshnessState.FAIL
        elif (
            warn_threshold_seconds and seconds_since_last_materialization >= warn_threshold_seconds
        ):
            return FreshnessState.WARN
        else:
            return FreshnessState.PASS


class CronFreshnessPolicyEvaluator(FreshnessPolicyEvaluator):
    policy_type = CronFreshnessPolicy

    async def evaluate_freshness(
        self, context: LoadingContext, node: BaseAssetNode
    ) -> FreshnessState:
        """Always look at the time window around the last completed cron tick.
        Time window = [last_completed_cron_tick - lower_bound_delta, last_completed_cron_tick].

        This means that if the current time is within a cron window, we still look at the PREVIOUS window.
        Ex: deadline_cron = "0 9 * * *", lower_bound_delta = 1 hour - asset is expected to materialize between 8-9am every day
        If the current time is 8:59am, we look at YESTERDAY's 8-9am window

        If there is a materialization AFTER the lower bound of the window, asset is fresh, otherwise it is stale.

        Examples:
        asset is expected to materialize beteween 8:45 - 9am every day
        deadline_cron = "0 9 * * *"
        lower_bound_delta = 15 minutes

        Example 1: Asset is on time
        Materialization time: 8:50am
        Asset is fresh starting at 9am, and will remain fresh until at least 9am next day

        Example 2: Asset is late
        Materialization time: 9:30am
        Asset is stale starting at 9am, becomes fresh at 9:30am, will remain fresh until at least 9am next day

        Example 3: Asset is early
        Materialization time: 8:30am
        Asset is stale starting at 9am, will remain stale until it materializes again.
        """
        # Get the policy, making sure it's a cron policy
        freshness_policy = check.not_none(node.freshness_policy_or_from_metadata)

        cron_policy = check.inst(
            freshness_policy,
            self.policy_type,
            f"Expected freshness policy type {self.policy_type}, got {freshness_policy.__class__}",
        )

        # Get the latest materialization event
        record = await AssetRecord.gen(context, node.key)
        latest_materialization_event = record.asset_entry.last_materialization if record else None
        # We can't evaluate freshness if there are no materialization events
        if not latest_materialization_event:
            return FreshnessState.UNKNOWN

        # Get the current datetime, in the timezone set on the policy
        current_datetime = get_current_datetime(cron_policy.timezone)

        # Get the timestamp of the last completed cron tick, evaluated in the timezone set on the policy
        latest_completed_cron_tick = get_latest_completed_cron_tick(
            cron_policy.deadline_cron, current_datetime, cron_policy.timezone
        )

        # Get the start of the last completed cron window, evaluated in the timezone set on the policy
        # Seconds resolution is okay here since we don't allow higher than to-the-minute resolution in the deadline cron
        cron_window_start = (
            latest_completed_cron_tick.timestamp() - cron_policy.lower_bound_delta.total_seconds()
        )

        # If the latest materialization is after the lower bound of the window, the asset is fresh, otherwise it is stale.
        return (
            FreshnessState.PASS
            if latest_materialization_event.timestamp >= cron_window_start
            else FreshnessState.FAIL
        )


FRESHNESS_EVALUATORS_BY_POLICY_TYPE: dict[
    type[InternalFreshnessPolicy], type[FreshnessPolicyEvaluator]
] = {
    TimeWindowFreshnessPolicy: TimeWindowFreshnessPolicyEvaluator,
    CronFreshnessPolicy: CronFreshnessPolicyEvaluator,
}
