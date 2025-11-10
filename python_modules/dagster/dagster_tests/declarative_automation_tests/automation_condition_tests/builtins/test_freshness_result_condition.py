from collections.abc import Sequence
from datetime import timedelta

import dagster as dg
import pytest
from dagster import AssetKey, AutomationCondition, DagsterInstance
from dagster._core.definitions.freshness import (
    FreshnessPolicy,
    FreshnessState,
    FreshnessStateChange,
)
from dagster._time import get_current_timestamp
from dagster_shared.check import ParameterCheckError


class TestFreshnessResultCondition:
    instance: DagsterInstance
    __state_cache: dict[AssetKey, FreshnessState]

    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.instance = DagsterInstance.ephemeral()
        self.__state_cache = {}
        yield
        self.instance = None  # pyright: ignore[reportAttributeAccessIssue]
        self.__state_cache = {}

    def report_freshness_state(self, key: AssetKey, state: FreshnessState) -> None:
        self.instance.report_runless_asset_event(
            asset_event=FreshnessStateChange(
                key=key,
                previous_state=self.__state_cache.get(key, FreshnessState.UNKNOWN),
                new_state=state,
                state_change_timestamp=get_current_timestamp(),
            )
        )
        self.__state_cache[key] = state

    @pytest.mark.parametrize(
        ["automation_condition", "synth_events", "expected_requested"],
        [
            pytest.param(
                automation_condition,
                synth_events,
                expected_requested,
                id=f"{automation_condition.name}-{[e.value for e in synth_events]}-{expected_requested}",
            )
            for automation_condition, synth_events, expected_requested in [
                (AutomationCondition.freshness_passed(), [FreshnessState.PASS], 1),
                (AutomationCondition.freshness_passed(), [FreshnessState.WARN], 0),
                (AutomationCondition.freshness_passed(), [FreshnessState.FAIL], 0),
                (AutomationCondition.freshness_passed(), [FreshnessState.UNKNOWN], 0),
                (AutomationCondition.freshness_passed(), [FreshnessState.NOT_APPLICABLE], 0),
                (
                    AutomationCondition.freshness_passed(),
                    [FreshnessState.NOT_APPLICABLE, FreshnessState.UNKNOWN, FreshnessState.PASS],
                    1,
                ),
                (
                    AutomationCondition.freshness_passed(),
                    [FreshnessState.PASS, FreshnessState.FAIL, FreshnessState.PASS],
                    1,
                ),
                (
                    AutomationCondition.freshness_passed(),
                    [FreshnessState.PASS, FreshnessState.WARN, FreshnessState.FAIL],
                    0,
                ),
                (AutomationCondition.freshness_passed(), [FreshnessState.NOT_APPLICABLE], 0),
                (AutomationCondition.freshness_warned(), [FreshnessState.PASS], 0),
                (AutomationCondition.freshness_warned(), [FreshnessState.WARN], 1),
                (AutomationCondition.freshness_warned(), [FreshnessState.FAIL], 0),
                (AutomationCondition.freshness_warned(), [FreshnessState.UNKNOWN], 0),
                (AutomationCondition.freshness_warned(), [FreshnessState.NOT_APPLICABLE], 0),
                (
                    AutomationCondition.freshness_warned(),
                    [FreshnessState.NOT_APPLICABLE, FreshnessState.UNKNOWN, FreshnessState.WARN],
                    1,
                ),
                (
                    AutomationCondition.freshness_warned(),
                    [FreshnessState.PASS, FreshnessState.FAIL, FreshnessState.WARN],
                    1,
                ),
                (
                    AutomationCondition.freshness_warned(),
                    [FreshnessState.PASS, FreshnessState.WARN, FreshnessState.FAIL],
                    0,
                ),
                (AutomationCondition.freshness_failed(), [FreshnessState.PASS], 0),
                (AutomationCondition.freshness_failed(), [FreshnessState.WARN], 0),
                (AutomationCondition.freshness_failed(), [FreshnessState.FAIL], 1),
                (AutomationCondition.freshness_failed(), [FreshnessState.UNKNOWN], 0),
                (AutomationCondition.freshness_failed(), [FreshnessState.NOT_APPLICABLE], 0),
                (
                    AutomationCondition.freshness_failed(),
                    [FreshnessState.NOT_APPLICABLE, FreshnessState.UNKNOWN, FreshnessState.FAIL],
                    1,
                ),
                (
                    AutomationCondition.freshness_failed(),
                    [FreshnessState.FAIL, FreshnessState.WARN, FreshnessState.FAIL],
                    1,
                ),
                (
                    AutomationCondition.freshness_failed(),
                    [FreshnessState.WARN, FreshnessState.FAIL, FreshnessState.PASS],
                    0,
                ),
            ]
        ],
    )
    def test_freshness_status_condition(
        self,
        automation_condition: AutomationCondition,
        synth_events: Sequence[FreshnessState],
        expected_requested: int,
    ) -> None:
        @dg.asset(
            freshness_policy=FreshnessPolicy.time_window(
                fail_window=timedelta(seconds=1, minutes=2, hours=3)
            ),
            automation_condition=automation_condition,
        )
        def _asset() -> None: ...

        # no change events - should not request
        result = dg.evaluate_automation_conditions(defs=[_asset], instance=self.instance)
        assert result.total_requested == 0

        for state in synth_events:
            self.report_freshness_state(_asset.key, state)

        # should request based on the last event
        result = dg.evaluate_automation_conditions(defs=[_asset], instance=self.instance)
        assert result.total_requested == expected_requested

        # should not change if we re-evaluate
        result = dg.evaluate_automation_conditions(defs=[_asset], instance=self.instance)
        assert result.total_requested == expected_requested

    @pytest.mark.parametrize(
        "automation_condition",
        [
            AutomationCondition.freshness_passed(),
            AutomationCondition.freshness_warned(),
            AutomationCondition.freshness_failed(),
        ],
        ids=["freshness_passed", "freshness_warned", "freshness_failed"],
    )
    def test_freshness_result_condition_no_freshness_policy(
        self, automation_condition: AutomationCondition
    ) -> None:
        @dg.asset(
            freshness_policy=None,
            automation_condition=automation_condition,
        )
        def _asset() -> None: ...

        # no freshness policy - should not request
        result = dg.evaluate_automation_conditions(defs=[_asset], instance=self.instance)
        assert result.total_requested == 0

    def test_freshness_result_condition_invalid_state_param(self) -> None:
        with pytest.raises(ParameterCheckError):
            from dagster._core.definitions.declarative_automation.operands import (
                FreshnessResultCondition,
            )

            FreshnessResultCondition(state="Fresh")  # pyright: ignore[reportArgumentType]
