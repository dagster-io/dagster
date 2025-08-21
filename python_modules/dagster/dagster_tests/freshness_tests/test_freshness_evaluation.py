import datetime
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from typing import Callable, cast

import dagster as dg
import pytest
from dagster import AssetKey, DagsterEventType, DagsterInstance
from dagster._check import CheckError
from dagster._core.definitions.freshness import FreshnessState, InternalFreshnessPolicy
from dagster._core.definitions.freshness_evaluator import (
    CronFreshnessPolicyEvaluator,
    TimeWindowFreshnessPolicyEvaluator,
)
from dagster._core.events import StepMaterializationData
from dagster._core.storage.dagster_run import make_new_run_id
from dagster._core.test_utils import create_test_daemon_workspace_context, freeze_time
from dagster._core.workspace.context import IWorkspaceProcessContext, LoadingContext

from dagster_tests.freshness_tests.utils import create_target_from_fn_and_local_scope


@contextmanager
def setup_remote_repo(
    instance: DagsterInstance,
    fn: Callable,
    location_name: str = "foo",
) -> Iterator[IWorkspaceProcessContext]:
    with create_target_from_fn_and_local_scope(location_name, fn) as target:
        with create_test_daemon_workspace_context(
            workspace_load_target=target,
            instance=instance,
        ) as workspace_context:
            yield workspace_context


@pytest.fixture
def instance() -> Generator[dg.DagsterInstance, None, None]:
    with dg.instance_for_test() as instance:
        yield instance


def store_mat(instance: DagsterInstance, asset_key: AssetKey, dt: datetime.datetime):
    instance.store_event(
        dg.EventLogEntry(
            error_info=None,
            user_message="",
            level="debug",
            run_id=make_new_run_id(),
            timestamp=dt.timestamp(),
            dagster_event=dg.DagsterEvent(
                DagsterEventType.ASSET_MATERIALIZATION.value,
                "nonce",
                event_specific_data=StepMaterializationData(
                    materialization=dg.AssetMaterialization(asset_key=asset_key),
                ),
            ),
        )
    )


class TestTimeWindowFreshnessPolicyEvaluator:
    @pytest.mark.asyncio
    async def test_freshness_pass(self, instance: DagsterInstance):
        """Test that an asset with a time window freshness policy is evaluated as fresh if its last materialization was within the fail window."""

        def create_defs() -> dg.Definitions:
            @dg.asset(
                freshness_policy=InternalFreshnessPolicy.time_window(
                    fail_window=datetime.timedelta(hours=24),
                )
            )
            def asset_with_policy():
                return 1

            return dg.Definitions(assets=[asset_with_policy])

        evaluator = TimeWindowFreshnessPolicyEvaluator()

        with setup_remote_repo(instance=instance, fn=create_defs) as workspace_context:
            asset_graph = workspace_context.create_request_context().asset_graph
            asset_key = dg.AssetKey("asset_with_policy")
            start_time = datetime.datetime.now(datetime.timezone.utc)
            frozen_time = start_time

            # Asset should be fresh immediately after materialization
            with freeze_time(frozen_time):
                store_mat(instance, asset_key, frozen_time)
                asset_node = asset_graph.remote_asset_nodes_by_key[asset_key]
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.PASS

            # Asset should still be fresh up until the very end of the fail window
            frozen_time += datetime.timedelta(hours=23, minutes=59, seconds=59)
            with freeze_time(frozen_time):
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.PASS

    @pytest.mark.asyncio
    async def test_freshness_pass_varying_fail_window(self, instance: DagsterInstance):
        """Same as test_freshness_pass, but with different fail windows ranging from minutes to months."""

        def create_defs() -> dg.Definitions:
            @dg.asset(
                freshness_policy=InternalFreshnessPolicy.time_window(
                    fail_window=datetime.timedelta(minutes=10),
                )
            )
            def asset_10min():
                return 1

            @dg.asset(
                freshness_policy=InternalFreshnessPolicy.time_window(
                    fail_window=datetime.timedelta(days=10),
                )
            )
            def asset_10days():
                return 2

            @dg.asset(
                freshness_policy=InternalFreshnessPolicy.time_window(
                    fail_window=datetime.timedelta(days=30),
                )
            )
            def asset_1month():
                return 3

            return dg.Definitions(assets=[asset_10min, asset_10days, asset_1month])

        evaluator = TimeWindowFreshnessPolicyEvaluator()

        with setup_remote_repo(instance=instance, fn=create_defs) as workspace_context:
            asset_graph = workspace_context.create_request_context().asset_graph
            asset_10min_key = dg.AssetKey("asset_10min")
            asset_10days_key = dg.AssetKey("asset_10days")
            asset_1month_key = dg.AssetKey("asset_1month")
            start_time = datetime.datetime.now(datetime.timezone.utc)
            frozen_time = start_time

            # All assets should be fresh immediately after materialization
            with freeze_time(frozen_time):
                store_mat(instance, asset_10min_key, frozen_time)
                store_mat(instance, asset_10days_key, frozen_time)
                store_mat(instance, asset_1month_key, frozen_time)

                # Check 10-minute asset
                asset_node = asset_graph.remote_asset_nodes_by_key[asset_10min_key]
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.PASS

                # Check 10-day asset
                asset_node = asset_graph.remote_asset_nodes_by_key[asset_10days_key]
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.PASS

                # Check 1-month asset
                asset_node = asset_graph.remote_asset_nodes_by_key[asset_1month_key]
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.PASS

            # Test 10-minute asset at 9 minutes and 59 seconds (still fresh)
            frozen_time_10min = frozen_time + datetime.timedelta(minutes=9, seconds=59)
            with freeze_time(frozen_time_10min):
                asset_node = asset_graph.remote_asset_nodes_by_key[asset_10min_key]
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.PASS

            # Test 10-day asset at 9 days, 23 hours, 59 minutes, 59 seconds (still fresh)
            frozen_time_10days = frozen_time + datetime.timedelta(
                days=9, hours=23, minutes=59, seconds=59
            )
            with freeze_time(frozen_time_10days):
                asset_node = asset_graph.remote_asset_nodes_by_key[asset_10days_key]
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.PASS

            # Test 1-month asset at 29 days, 23 hours, 59 minutes, 59 seconds (still fresh)
            frozen_time_1month = frozen_time + datetime.timedelta(
                days=29, hours=23, minutes=59, seconds=59
            )
            with freeze_time(frozen_time_1month):
                asset_node = asset_graph.remote_asset_nodes_by_key[asset_1month_key]
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.PASS

    @pytest.mark.asyncio
    async def test_freshness_fail(self, instance: DagsterInstance):
        """Test that an asset fails freshness if its last materialization is outside the fail window."""

        def create_defs() -> dg.Definitions:
            @dg.asset(
                freshness_policy=InternalFreshnessPolicy.time_window(
                    fail_window=datetime.timedelta(hours=24),
                )
            )
            def asset_with_policy():
                return 1

            return dg.Definitions(assets=[asset_with_policy])

        evaluator = TimeWindowFreshnessPolicyEvaluator()

        with setup_remote_repo(instance=instance, fn=create_defs) as workspace_context:
            asset_graph = workspace_context.create_request_context().asset_graph
            asset_key = dg.AssetKey("asset_with_policy")
            start_time = datetime.datetime.now(datetime.timezone.utc)
            frozen_time = start_time

            # Asset should fail freshness if last materialization is outside the fail window
            store_mat(instance, asset_key, frozen_time)

            frozen_time += datetime.timedelta(hours=24, seconds=1)
            with freeze_time(frozen_time):
                asset_node = asset_graph.remote_asset_nodes_by_key[asset_key]
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.FAIL

    @pytest.mark.asyncio
    async def test_freshness_warn(self, instance: DagsterInstance):
        """Test that an asset enters freshness warning state if its last materialization is outside the warn window but within the fail window."""

        def create_defs() -> dg.Definitions:
            @dg.asset(
                freshness_policy=InternalFreshnessPolicy.time_window(
                    fail_window=datetime.timedelta(hours=24),
                    warn_window=datetime.timedelta(hours=12),
                )
            )
            def asset_with_policy():
                return 1

            return dg.Definitions(assets=[asset_with_policy])

        evaluator = TimeWindowFreshnessPolicyEvaluator()

        with setup_remote_repo(instance=instance, fn=create_defs) as workspace_context:
            asset_graph = workspace_context.create_request_context().asset_graph
            asset_key = dg.AssetKey("asset_with_policy")
            start_time = datetime.datetime.now(datetime.timezone.utc)
            frozen_time = start_time

            store_mat(instance, asset_key, frozen_time)

            frozen_time += datetime.timedelta(hours=12, seconds=1)
            with freeze_time(frozen_time):
                asset_node = asset_graph.remote_asset_nodes_by_key[asset_key]
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.WARN

    @pytest.mark.asyncio
    async def test_freshness_unknown(self, instance: DagsterInstance):
        """Test that assets with freshness policies but no materializations are evaluated as UNKNOWN."""

        def create_defs() -> dg.Definitions:
            @dg.asset(
                freshness_policy=InternalFreshnessPolicy.time_window(
                    fail_window=datetime.timedelta(hours=24),
                )
            )
            def asset_with_policy():
                return 1

            @dg.asset(
                freshness_policy=InternalFreshnessPolicy.time_window(
                    fail_window=datetime.timedelta(hours=24),
                    warn_window=datetime.timedelta(hours=12),
                )
            )
            def asset_with_policy_2():
                return 1

            return dg.Definitions(assets=[asset_with_policy, asset_with_policy_2])

        evaluator = TimeWindowFreshnessPolicyEvaluator()

        with setup_remote_repo(instance=instance, fn=create_defs) as workspace_context:
            asset_graph = workspace_context.create_request_context().asset_graph
            ctx = cast("LoadingContext", workspace_context.create_request_context())
            for asset_node in asset_graph.remote_asset_nodes_by_key.values():
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.UNKNOWN

    @pytest.mark.asyncio
    async def test_freshness_no_policy(self, instance: DagsterInstance):
        """Raise CheckError if attempting to evaluate freshness for an asset without a freshness policy."""

        def create_defs() -> dg.Definitions:
            @dg.asset
            def asset_without_policy():
                return 1

            return dg.Definitions(assets=[asset_without_policy])

        evaluator = TimeWindowFreshnessPolicyEvaluator()

        with setup_remote_repo(instance=instance, fn=create_defs) as workspace_context:
            asset_graph = workspace_context.create_request_context().asset_graph
            ctx = cast("LoadingContext", workspace_context.create_request_context())
            for asset_node in asset_graph.remote_asset_nodes_by_key.values():
                with pytest.raises(CheckError):
                    await evaluator.evaluate_freshness(context=ctx, node=asset_node)


class TestCronFreshnessPolicyEvaluator:
    @pytest.mark.asyncio
    async def test_cron_freshness_pass(self, instance: DagsterInstance):
        """Test that an asset with a cron freshness policy is evaluated as fresh if its last materialization was within the expected time window."""

        def create_defs() -> dg.Definitions:
            @dg.asset(
                freshness_policy=InternalFreshnessPolicy.cron(
                    deadline_cron="0 9 * * *",  # Daily at 9 AM
                    lower_bound_delta=datetime.timedelta(hours=1),
                )
            )
            def asset_with_policy():
                return 1

            return dg.Definitions(assets=[asset_with_policy])

        evaluator = CronFreshnessPolicyEvaluator()

        with setup_remote_repo(instance=instance, fn=create_defs) as workspace_context:
            asset_graph = workspace_context.create_request_context().asset_graph
            asset_key = dg.AssetKey("asset_with_policy")
            asset_node = asset_graph.remote_asset_nodes_by_key[asset_key]

            # Test at 10:00 AM on Jan 1 (last completed cron tick was 9:00 AM on Jan 1, window: 8:00-9:00 AM Jan 1)
            current_time = datetime.datetime(2024, 1, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)

            # Asset materialized at 8:30 AM Jan 1 (within the 8:00-9:00 AM window)
            materialization_time = datetime.datetime(
                2024, 1, 1, 8, 30, 0, tzinfo=datetime.timezone.utc
            )
            store_mat(instance, asset_key, materialization_time)

            with freeze_time(current_time):
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.PASS

            # Asset materialized at 7:30 AM Jan 1 (before the 8:00-9:00 AM window)
            early_materialization = datetime.datetime(
                2024, 1, 1, 7, 30, 0, tzinfo=datetime.timezone.utc
            )
            store_mat(instance, asset_key, early_materialization)

            with freeze_time(current_time):
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.FAIL

            # Test that asset stays fresh until next deadline passes
            # Asset materialized at 8:45 AM Jan 1 (late in the 8:00-9:00 AM window)
            late_materialization = datetime.datetime(
                2024, 1, 1, 8, 45, 0, tzinfo=datetime.timezone.utc
            )
            store_mat(instance, asset_key, late_materialization)

            # Should be fresh at 5:00 PM same day (next deadline hasn't passed yet)
            same_day_evening = datetime.datetime(2024, 1, 1, 17, 0, 0, tzinfo=datetime.timezone.utc)
            with freeze_time(same_day_evening):
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.PASS

            # Should be stale at 10:00 AM next day (after Jan 2 9 AM deadline has passed)
            next_day = datetime.datetime(2024, 1, 2, 10, 0, 0, tzinfo=datetime.timezone.utc)
            with freeze_time(next_day):
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.FAIL

    @pytest.mark.asyncio
    async def test_cron_freshness_pass_different_schedules(self, instance: DagsterInstance):
        """Test freshness evaluation with different cron schedules and lower bounds."""

        def create_defs() -> dg.Definitions:
            @dg.asset(
                freshness_policy=InternalFreshnessPolicy.cron(
                    deadline_cron="0 */6 * * *",  # Every 6 hours
                    lower_bound_delta=datetime.timedelta(minutes=30),
                )
            )
            def asset_every_6h():
                return 1

            @dg.asset(
                freshness_policy=InternalFreshnessPolicy.cron(
                    deadline_cron="0 12 * * 1",  # Every Monday at noon
                    lower_bound_delta=datetime.timedelta(hours=2),
                )
            )
            def asset_weekly():
                return 2

            @dg.asset(
                freshness_policy=InternalFreshnessPolicy.cron(
                    deadline_cron="*/15 * * * *",  # Every 15 minutes
                    lower_bound_delta=datetime.timedelta(minutes=5),
                )
            )
            def asset_frequent():
                return 3

            return dg.Definitions(assets=[asset_every_6h, asset_weekly, asset_frequent])

        evaluator = CronFreshnessPolicyEvaluator()

        with setup_remote_repo(instance=instance, fn=create_defs) as workspace_context:
            asset_graph = workspace_context.create_request_context().asset_graph

            # Test 6-hour schedule asset at 12:00 PM (next deadline is 6:00 PM, window is 5:30-6:00 PM)
            current_time = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
            materialization_time = datetime.datetime(
                2024, 1, 1, 17, 45, 0, tzinfo=datetime.timezone.utc
            )  # 5:45 PM

            with freeze_time(current_time):
                store_mat(instance, dg.AssetKey("asset_every_6h"), materialization_time)

            # Advance to just before the deadline (5:59 PM)
            evaluation_time = datetime.datetime(2024, 1, 1, 17, 59, 0, tzinfo=datetime.timezone.utc)
            with freeze_time(evaluation_time):
                asset_node = asset_graph.remote_asset_nodes_by_key[dg.AssetKey("asset_every_6h")]
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.PASS

            # Test weekly asset on Monday at 11:00 AM (deadline is 12:00 PM, window is 10:00 AM - 12:00 PM)
            current_time = datetime.datetime(
                2024, 1, 1, 11, 0, 0, tzinfo=datetime.timezone.utc
            )  # Monday
            materialization_time = datetime.datetime(
                2024, 1, 1, 11, 30, 0, tzinfo=datetime.timezone.utc
            )  # 11:30 AM

            with freeze_time(current_time):
                store_mat(instance, dg.AssetKey("asset_weekly"), materialization_time)

            evaluation_time = datetime.datetime(2024, 1, 1, 11, 59, 0, tzinfo=datetime.timezone.utc)
            with freeze_time(evaluation_time):
                asset_node = asset_graph.remote_asset_nodes_by_key[dg.AssetKey("asset_weekly")]
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.PASS

            # Test frequent asset (every 15 minutes, next deadline at 12:15, window is 12:10-12:15)
            current_time = datetime.datetime(2024, 1, 1, 12, 5, 0, tzinfo=datetime.timezone.utc)
            materialization_time = datetime.datetime(
                2024, 1, 1, 12, 12, 0, tzinfo=datetime.timezone.utc
            )  # 12:12 PM

            with freeze_time(current_time):
                store_mat(instance, dg.AssetKey("asset_frequent"), materialization_time)

            evaluation_time = datetime.datetime(2024, 1, 1, 12, 14, 0, tzinfo=datetime.timezone.utc)
            with freeze_time(evaluation_time):
                asset_node = asset_graph.remote_asset_nodes_by_key[dg.AssetKey("asset_frequent")]
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.PASS

    @pytest.mark.asyncio
    async def test_cron_freshness_fail(self, instance: DagsterInstance):
        """Test that an asset fails freshness if its last materialization is outside the expected time window."""

        def create_defs() -> dg.Definitions:
            @dg.asset(
                freshness_policy=InternalFreshnessPolicy.cron(
                    deadline_cron="0 9 * * *",  # Daily at 9 AM
                    lower_bound_delta=datetime.timedelta(hours=1),
                )
            )
            def asset_with_policy():
                return 1

            return dg.Definitions(assets=[asset_with_policy])

        evaluator = CronFreshnessPolicyEvaluator()

        with setup_remote_repo(instance=instance, fn=create_defs) as workspace_context:
            asset_graph = workspace_context.create_request_context().asset_graph
            asset_key = dg.AssetKey("asset_with_policy")

            # Start at 9:00 AM on a specific day
            start_time = datetime.datetime(2024, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)

            # Asset should fail if materialized before the lower bound (before 8:00 AM)
            materialization_time = start_time - datetime.timedelta(
                hours=2
            )  # 7:00 AM (outside window)
            with freeze_time(start_time):
                store_mat(instance, asset_key, materialization_time)
                asset_node = asset_graph.remote_asset_nodes_by_key[asset_key]
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.FAIL

    @pytest.mark.asyncio
    async def test_cron_freshness_materialization_after_deadline(self, instance: DagsterInstance):
        """Test that an asset fails freshness if it hasn't materialized after the deadline passes, and passes once it materializes."""

        def create_defs() -> dg.Definitions:
            @dg.asset(
                freshness_policy=InternalFreshnessPolicy.cron(
                    deadline_cron="0 9 * * *",  # Daily at 9 AM
                    lower_bound_delta=datetime.timedelta(hours=1),
                )
            )
            def asset_with_policy():
                return 1

            return dg.Definitions(assets=[asset_with_policy])

        evaluator = CronFreshnessPolicyEvaluator()

        with setup_remote_repo(instance=instance, fn=create_defs) as workspace_context:
            asset_graph = workspace_context.create_request_context().asset_graph
            asset_key = dg.AssetKey("asset_with_policy")

            # Start at 9:00 AM. Last materialization was AGES ago.
            start_time = datetime.datetime(2024, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)

            store_mat(instance, asset_key, start_time - datetime.timedelta(days=30))

            # At 9:01am, the asset should be stale
            with freeze_time(start_time + datetime.timedelta(minutes=1)):
                asset_node = asset_graph.remote_asset_nodes_by_key[asset_key]
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.FAIL

            # Asset materializes at 9:05am
            materialization_time = start_time + datetime.timedelta(minutes=5)
            store_mat(instance, asset_key, materialization_time)

            # At 9:06am, the asset should be fresh
            with freeze_time(materialization_time + datetime.timedelta(minutes=1)):
                asset_node = asset_graph.remote_asset_nodes_by_key[asset_key]
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.PASS

            # Asset should still be fresh at 8:59am the next day
            with freeze_time(
                start_time + datetime.timedelta(days=1) - datetime.timedelta(minutes=1)
            ):
                asset_node = asset_graph.remote_asset_nodes_by_key[asset_key]
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.PASS

            # Asset should be stale at 9:00am the next day
            with freeze_time(
                start_time + datetime.timedelta(days=1) + datetime.timedelta(minutes=60)
            ):
                asset_node = asset_graph.remote_asset_nodes_by_key[asset_key]
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.FAIL

    @pytest.mark.asyncio
    async def test_cron_freshness_unknown(self, instance: DagsterInstance):
        """Test that assets with cron freshness policies but no materializations are evaluated as UNKNOWN."""

        def create_defs() -> dg.Definitions:
            @dg.asset(
                freshness_policy=InternalFreshnessPolicy.cron(
                    deadline_cron="0 9 * * *",  # Daily at 9 AM
                    lower_bound_delta=datetime.timedelta(hours=1),
                )
            )
            def asset_with_policy():
                return 1

            @dg.asset(
                freshness_policy=InternalFreshnessPolicy.cron(
                    deadline_cron="0 */12 * * *",  # Every 12 hours
                    lower_bound_delta=datetime.timedelta(hours=2),
                )
            )
            def asset_with_policy_2():
                return 1

            return dg.Definitions(assets=[asset_with_policy, asset_with_policy_2])

        evaluator = CronFreshnessPolicyEvaluator()

        with setup_remote_repo(instance=instance, fn=create_defs) as workspace_context:
            asset_graph = workspace_context.create_request_context().asset_graph
            ctx = cast("LoadingContext", workspace_context.create_request_context())
            for asset_node in asset_graph.remote_asset_nodes_by_key.values():
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.UNKNOWN

    @pytest.mark.asyncio
    async def test_cron_freshness_no_policy(self, instance: DagsterInstance):
        """Raise CheckError if attempting to evaluate freshness for an asset without a freshness policy."""

        def create_defs() -> dg.Definitions:
            @dg.asset
            def asset_without_policy():
                return 1

            return dg.Definitions(assets=[asset_without_policy])

        evaluator = CronFreshnessPolicyEvaluator()

        with setup_remote_repo(instance=instance, fn=create_defs) as workspace_context:
            asset_graph = workspace_context.create_request_context().asset_graph
            ctx = cast("LoadingContext", workspace_context.create_request_context())
            for asset_node in asset_graph.remote_asset_nodes_by_key.values():
                with pytest.raises(CheckError):
                    await evaluator.evaluate_freshness(context=ctx, node=asset_node)

    @pytest.mark.asyncio
    async def test_cron_freshness_with_timezone(self, instance: DagsterInstance):
        """Test cron freshness evaluation with different timezones."""

        def create_defs() -> dg.Definitions:
            @dg.asset(
                freshness_policy=InternalFreshnessPolicy.cron(
                    deadline_cron="0 9 * * *",  # Daily at 9 AM
                    lower_bound_delta=datetime.timedelta(hours=1),
                    timezone="America/New_York",
                )
            )
            def asset_with_timezone():
                return 1

            return dg.Definitions(assets=[asset_with_timezone])

        evaluator = CronFreshnessPolicyEvaluator()

        with setup_remote_repo(instance=instance, fn=create_defs) as workspace_context:
            asset_graph = workspace_context.create_request_context().asset_graph
            asset_key = dg.AssetKey("asset_with_timezone")

            # Test at 9:00 AM EST (14:00 UTC)
            start_time = datetime.datetime(2024, 1, 1, 14, 0, 0, tzinfo=datetime.timezone.utc)

            # Asset should be fresh if materialized within the expected window in NY time
            # 8:30 AM EST = 13:30 UTC
            materialization_time = datetime.datetime(
                2024, 1, 1, 13, 30, 0, tzinfo=datetime.timezone.utc
            )
            with freeze_time(start_time):
                store_mat(instance, asset_key, materialization_time)
                asset_node = asset_graph.remote_asset_nodes_by_key[asset_key]
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.PASS

    @pytest.mark.asyncio
    async def test_cron_freshness_multiple_materializations_same_window(
        self, instance: DagsterInstance
    ):
        """Test that with multiple materializations in the same cron window, the latest one is used."""

        def create_defs() -> dg.Definitions:
            @dg.asset(
                freshness_policy=InternalFreshnessPolicy.cron(
                    deadline_cron="0 9 * * *",  # Daily at 9 AM
                    lower_bound_delta=datetime.timedelta(hours=1),  # Window: 8-9 AM
                )
            )
            def asset_with_policy():
                return 1

            return dg.Definitions(assets=[asset_with_policy])

        evaluator = CronFreshnessPolicyEvaluator()

        with setup_remote_repo(instance=instance, fn=create_defs) as workspace_context:
            asset_graph = workspace_context.create_request_context().asset_graph
            asset_key = dg.AssetKey("asset_with_policy")
            asset_node = asset_graph.remote_asset_nodes_by_key[asset_key]

            # Multiple materializations in the same window
            # Evaluating at 10:00 AM Jan 1 (last completed tick was 9:00 AM Jan 1, window: 8-9 AM Jan 1)
            evaluation_time = datetime.datetime(2024, 1, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)

            # First materialization (early in window)
            early_materialization = datetime.datetime(
                2024, 1, 1, 8, 10, 0, tzinfo=datetime.timezone.utc
            )
            store_mat(instance, asset_key, early_materialization)

            # Second materialization (later in window)
            later_materialization = datetime.datetime(
                2024, 1, 1, 8, 45, 0, tzinfo=datetime.timezone.utc
            )
            store_mat(instance, asset_key, later_materialization)

            # Third materialization (latest in window)
            latest_materialization = datetime.datetime(
                2024, 1, 1, 8, 55, 0, tzinfo=datetime.timezone.utc
            )
            store_mat(instance, asset_key, latest_materialization)

            # Should use the latest materialization and be fresh
            with freeze_time(evaluation_time):
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.PASS

            # Test with a materialization outside the current window (but more recent than in-window ones)
            # The asset should still be fresh.
            out_of_window_materialization = datetime.datetime(
                2024, 1, 1, 9, 30, 0, tzinfo=datetime.timezone.utc
            )
            store_mat(instance, asset_key, out_of_window_materialization)

            evaluation_time = out_of_window_materialization + datetime.timedelta(seconds=1)
            with freeze_time(evaluation_time):
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.PASS

            # Asset should continue to be fresh until the NEXT deadline passes (9:00 am Jan 2)
            next_window_start = datetime.datetime(2024, 1, 2, 8, 0, 0, tzinfo=datetime.timezone.utc)
            with freeze_time(next_window_start):
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.PASS

            next_deadline = datetime.datetime(2024, 1, 2, 9, 0, 0, tzinfo=datetime.timezone.utc)
            with freeze_time(next_deadline):
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.FAIL

    @pytest.mark.asyncio
    async def test_cron_freshness_rapid_evaluation_cycles(self, instance: DagsterInstance):
        """Test freshness evaluation with rapid cycles (every 30 seconds like in production)."""

        def create_defs() -> dg.Definitions:
            @dg.asset(
                freshness_policy=InternalFreshnessPolicy.cron(
                    deadline_cron="0 9 * * *",  # Daily at 9 AM
                    lower_bound_delta=datetime.timedelta(hours=1),  # Window: 8-9 AM
                )
            )
            def asset_with_policy():
                return 1

            return dg.Definitions(assets=[asset_with_policy])

        evaluator = CronFreshnessPolicyEvaluator()

        with setup_remote_repo(instance=instance, fn=create_defs) as workspace_context:
            asset_graph = workspace_context.create_request_context().asset_graph
            asset_key = dg.AssetKey("asset_with_policy")
            asset_node = asset_graph.remote_asset_nodes_by_key[asset_key]

            # Asset materialized at 8:30 AM
            materialization_time = datetime.datetime(
                2024, 1, 1, 8, 30, 0, tzinfo=datetime.timezone.utc
            )
            store_mat(instance, asset_key, materialization_time)

            # Test rapid evaluations every 30 seconds around the deadline
            base_time = datetime.datetime(2024, 1, 1, 8, 58, 0, tzinfo=datetime.timezone.utc)

            # Evaluate every 30 seconds for 5 minutes around deadline
            for i in range(10):  # 10 * 30 seconds = 5 minutes
                current_time = base_time + datetime.timedelta(seconds=30 * i)

                with freeze_time(current_time):
                    ctx = cast("LoadingContext", workspace_context.create_request_context())
                    freshness_state = await evaluator.evaluate_freshness(
                        context=ctx, node=asset_node
                    )
                    # Should be fresh until 9:00 AM, then start becoming stale
                    if current_time < datetime.datetime(
                        2024, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc
                    ):
                        assert freshness_state == FreshnessState.PASS
                    else:
                        # After 9:00 AM, asset should remain fresh until next deadline
                        assert freshness_state == FreshnessState.PASS

            # Test the transition to stale state the next day
            next_day_evaluation = datetime.datetime(
                2024, 1, 2, 9, 0, 30, tzinfo=datetime.timezone.utc
            )

            with freeze_time(next_day_evaluation):
                ctx = cast("LoadingContext", workspace_context.create_request_context())
                freshness_state = await evaluator.evaluate_freshness(context=ctx, node=asset_node)
                assert freshness_state == FreshnessState.FAIL

            # Add new materialization and test rapid evaluations again
            new_materialization = datetime.datetime(
                2024, 1, 2, 8, 45, 0, tzinfo=datetime.timezone.utc
            )
            store_mat(instance, asset_key, new_materialization)

            # Test several rapid evaluations after new materialization
            for i in range(5):
                eval_time = new_materialization + datetime.timedelta(seconds=30 * i)

                with freeze_time(eval_time):
                    ctx = cast("LoadingContext", workspace_context.create_request_context())
                    freshness_state = await evaluator.evaluate_freshness(
                        context=ctx, node=asset_node
                    )
                    assert freshness_state == FreshnessState.PASS

    @pytest.mark.asyncio
    async def test_cron_freshness_evaluation_at_different_cycle_points(
        self, instance: DagsterInstance
    ):
        """Test freshness evaluation at different points in the cron cycle."""

        def create_defs() -> dg.Definitions:
            @dg.asset(
                freshness_policy=InternalFreshnessPolicy.cron(
                    deadline_cron="0 */6 * * *",  # Every 6 hours (midnight, 6am, noon, 6pm)
                    lower_bound_delta=datetime.timedelta(hours=1),  # Window: 1 hour before deadline
                )
            )
            def asset_with_policy():
                return 1

            return dg.Definitions(assets=[asset_with_policy])

        evaluator = CronFreshnessPolicyEvaluator()

        with setup_remote_repo(instance=instance, fn=create_defs) as workspace_context:
            asset_graph = workspace_context.create_request_context().asset_graph
            asset_key = dg.AssetKey("asset_with_policy")
            asset_node = asset_graph.remote_asset_nodes_by_key[asset_key]

            # Asset materialized at 5:30 AM (within the 5-6 AM window for 6 AM deadline)
            materialization_time = datetime.datetime(
                2024, 1, 1, 5, 30, 0, tzinfo=datetime.timezone.utc
            )
            store_mat(instance, asset_key, materialization_time)

            # Test evaluation at different points in the 6-hour cycle
            test_times = [
                # Just after 6 AM deadline (last completed tick is 6 AM, asset should be fresh)
                (
                    datetime.datetime(2024, 1, 1, 6, 0, 30, tzinfo=datetime.timezone.utc),
                    FreshnessState.PASS,
                ),
                # Middle of cycle (9 AM) - still looking at 6 AM tick
                (
                    datetime.datetime(2024, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc),
                    FreshnessState.PASS,
                ),
                # Near next deadline (11:30 AM) - still looking at 6 AM tick
                (
                    datetime.datetime(2024, 1, 1, 11, 30, 0, tzinfo=datetime.timezone.utc),
                    FreshnessState.PASS,
                ),
                # Just before next deadline (11:59 AM) - still looking at 6 AM tick
                (
                    datetime.datetime(2024, 1, 1, 11, 59, 0, tzinfo=datetime.timezone.utc),
                    FreshnessState.PASS,
                ),
                # Just after noon deadline (12:00:30 PM) - now looking at noon tick, should be stale
                (
                    datetime.datetime(2024, 1, 1, 12, 0, 30, tzinfo=datetime.timezone.utc),
                    FreshnessState.FAIL,
                ),
                # Later in the afternoon (2:30 PM) - still looking at noon tick, still stale
                (
                    datetime.datetime(2024, 1, 1, 14, 30, 0, tzinfo=datetime.timezone.utc),
                    FreshnessState.FAIL,
                ),
            ]

            for test_time, expected_state in test_times:
                with freeze_time(test_time):
                    ctx = cast("LoadingContext", workspace_context.create_request_context())
                    freshness_state = await evaluator.evaluate_freshness(
                        context=ctx, node=asset_node
                    )
                    assert freshness_state == expected_state, (
                        f"At {test_time}, expected {expected_state}, got {freshness_state}"
                    )

            # Add a new materialization and test different cycle points again
            new_materialization = datetime.datetime(
                2024, 1, 1, 11, 15, 0, tzinfo=datetime.timezone.utc
            )  # 11:15 AM (within 11 AM - 12 PM window for noon deadline)
            store_mat(instance, asset_key, new_materialization)

            # Test evaluation after new materialization at various points
            post_materialization_tests = [
                # Right after materialization (still before noon deadline)
                (
                    datetime.datetime(2024, 1, 1, 11, 16, 0, tzinfo=datetime.timezone.utc),
                    FreshnessState.PASS,
                ),
                # Just after noon deadline (now looking at noon tick, should be fresh)
                (
                    datetime.datetime(2024, 1, 1, 12, 0, 30, tzinfo=datetime.timezone.utc),
                    FreshnessState.PASS,
                ),
                # Early in next cycle (2 PM) - still looking at noon tick
                (
                    datetime.datetime(2024, 1, 1, 14, 0, 0, tzinfo=datetime.timezone.utc),
                    FreshnessState.PASS,
                ),
                # Late in next cycle (5:30 PM) - still looking at noon tick
                (
                    datetime.datetime(2024, 1, 1, 17, 30, 0, tzinfo=datetime.timezone.utc),
                    FreshnessState.PASS,
                ),
                # After next deadline (6:30 PM) - now looking at 6 PM tick, should be stale
                (
                    datetime.datetime(2024, 1, 1, 18, 30, 0, tzinfo=datetime.timezone.utc),
                    FreshnessState.FAIL,
                ),
            ]

            for test_time, expected_state in post_materialization_tests:
                with freeze_time(test_time):
                    ctx = cast("LoadingContext", workspace_context.create_request_context())
                    freshness_state = await evaluator.evaluate_freshness(
                        context=ctx, node=asset_node
                    )
                    assert freshness_state == expected_state, (
                        f"After new materialization at {test_time}, expected {expected_state}, got {freshness_state}"
                    )
