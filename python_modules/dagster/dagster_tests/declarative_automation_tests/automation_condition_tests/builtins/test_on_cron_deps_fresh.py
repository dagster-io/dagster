from collections.abc import Sequence
from datetime import datetime, timedelta

import dagster as dg
import pytest
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_key import CoercibleToAssetKey
from dagster._core.definitions.declarative_automation.automation_condition_tester import (
    EvaluateAutomationConditionsResult,
)
from dagster._core.definitions.freshness import FreshnessState, FreshnessStateChange
from dagster._time import get_current_timestamp


class TestOnCronDepsFresh:
    instance: dg.DagsterInstance
    defs: dg.Definitions
    __state_cache: dict[dg.AssetKey, FreshnessState]

    def test_defs(self) -> dg.Definitions:
        @dg.asset(
            automation_condition=dg.AutomationCondition.on_cron_deps_fresh(
                "@hourly", allow_missing_freshness_policy=False
            ),
            freshness_policy=dg.FreshnessPolicy.time_window(
                warn_window=timedelta(hours=24), fail_window=timedelta(hours=26)
            ),
        )
        def raw_1() -> None: ...

        @dg.asset(
            automation_condition=dg.AutomationCondition.on_cron_deps_fresh("@hourly"),
            freshness_policy=dg.FreshnessPolicy.time_window(
                warn_window=timedelta(hours=24), fail_window=timedelta(hours=26)
            ),
        )
        def raw_2() -> None: ...

        @dg.asset(
            deps=[raw_1, raw_2],
            automation_condition=dg.AutomationCondition.on_cron_deps_fresh("@hourly"),
            freshness_policy=dg.FreshnessPolicy.time_window(
                warn_window=timedelta(hours=24), fail_window=timedelta(hours=26)
            ),
        )
        def staging() -> None: ...

        return dg.Definitions(assets=[raw_1, raw_2, staging])

    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.instance = dg.DagsterInstance.ephemeral()
        self.__state_cache = {}
        self.defs = self.test_defs()
        yield
        self.instance = None  # pyright: ignore[reportAttributeAccessIssue]
        self.__state_cache = {}
        self.defs = None  # pyright: ignore[reportAttributeAccessIssue]

    def report_freshness_state(self, key: CoercibleToAssetKey, state: FreshnessState) -> None:
        asset_key = dg.AssetKey.from_coercible(key)
        self.instance.report_runless_asset_event(
            asset_event=FreshnessStateChange(
                key=asset_key,
                previous_state=self.__state_cache.get(asset_key, FreshnessState.UNKNOWN),
                new_state=state,
                state_change_timestamp=get_current_timestamp(),
            )
        )
        self.__state_cache[asset_key] = state

    def evaluate(
        self,
        evaluation_time: datetime,
        cursor: AssetDaemonCursor | None = None,
        keys: Sequence[str] | None = None,
    ) -> EvaluateAutomationConditionsResult:
        return dg.evaluate_automation_conditions(
            defs=self.defs,
            instance=self.instance,
            asset_selection=dg.AssetSelection.assets(*keys) if keys else None,
            evaluation_time=evaluation_time,
            cursor=cursor,
        )

    def test_deps(self) -> None:
        current_time = datetime(2024, 8, 16, 4, 35)

        # hasn't passed a cron tick
        result = self.evaluate(current_time)
        assert result.total_requested == 0

        # not passed a cron tick
        current_time += timedelta(minutes=5)
        result = self.evaluate(current_time, cursor=result.cursor)
        assert result.total_requested == 0

        # passed a cron tick and no deps on assets in selection
        current_time += timedelta(hours=1)
        result = self.evaluate(current_time, cursor=result.cursor, keys=["raw_1", "raw_2"])
        assert result.total_requested == 2

    def test_staging(self) -> None:
        current_time = datetime(2024, 8, 16, 4, 35)

        # hasn't passed a cron tick
        result = self.evaluate(current_time, keys=["staging"])
        assert result.total_requested == 0

        # not passed a cron tick
        current_time += timedelta(minutes=5)
        result = self.evaluate(current_time, cursor=result.cursor, keys=["staging"])
        assert result.total_requested == 0

        # not passed a cron tick, raw_1 is fresh but raw_2 is UNKNOWN
        self.report_freshness_state("raw_1", FreshnessState.PASS)
        result = self.evaluate(current_time, cursor=result.cursor, keys=["staging"])
        assert result.total_requested == 0

        # passed a cron tick, raw_1 is fresh and raw_2 is FAIL
        current_time += timedelta(hours=1)
        self.report_freshness_state("raw_2", FreshnessState.FAIL)
        result = self.evaluate(current_time, cursor=result.cursor, keys=["staging"])
        assert result.total_requested == 0

        # already passed a cron tick, raw_1 is fresh and raw_2 is now WARN (which counts as fresh)
        current_time += timedelta(minutes=1)
        self.report_freshness_state("raw_2", FreshnessState.WARN)
        result = self.evaluate(current_time, cursor=result.cursor, keys=["staging"])
        assert result.total_requested == 1

        # not passed a cron tick, raw_1 is fresh and raw_2 is WARN (which is fresh)
        current_time += timedelta(minutes=1)
        result = self.evaluate(current_time, cursor=result.cursor, keys=["staging"])
        assert result.total_requested == 0

        # not passed a cron tick, raw_1 is fresh and raw_2 is PASS
        current_time += timedelta(minutes=1)
        self.report_freshness_state("raw_2", FreshnessState.PASS)
        result = self.evaluate(current_time, cursor=result.cursor, keys=["staging"])
        assert result.total_requested == 0

        # passed a cron tick, raw_1 is fresh and raw_2 is PASS
        current_time += timedelta(minutes=20)
        result = self.evaluate(current_time, cursor=result.cursor, keys=["staging"])
        assert result.total_requested == 1

        # passed a cron tick, raw_1 is FAIL and raw_2 is FAIL
        current_time += timedelta(hours=1)
        self.report_freshness_state("raw_1", FreshnessState.FAIL)
        self.report_freshness_state("raw_2", FreshnessState.FAIL)
        result = self.evaluate(current_time, cursor=result.cursor, keys=["staging"])
        assert result.total_requested == 0

    def test_all(self) -> None:
        current_time = datetime(2024, 8, 16, 4, 35)

        # hasn't passed a cron tick
        result = self.evaluate(current_time)
        assert result.total_requested == 0

        # not passed a cron tick
        current_time += timedelta(minutes=5)
        result = self.evaluate(current_time, cursor=result.cursor)
        assert result.total_requested == 0

        # passed a cron tick and all assets are selected, so should request all
        current_time += timedelta(hours=1)
        result = self.evaluate(current_time, cursor=result.cursor)
        assert result.total_requested == 3
