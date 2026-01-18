import pytest

from dagster_tests.declarative_automation_tests.legacy_tests.updated_scenarios.basic_scenarios import (
    basic_scenarios,
)
from dagster_tests.declarative_automation_tests.legacy_tests.updated_scenarios.cron_scenarios import (
    cron_scenarios,
)
from dagster_tests.declarative_automation_tests.legacy_tests.updated_scenarios.freshness_policy_scenarios import (
    freshness_policy_scenarios,
)
from dagster_tests.declarative_automation_tests.legacy_tests.updated_scenarios.latest_materialization_run_tag_scenarios import (
    latest_materialization_run_tag_scenarios,
)
from dagster_tests.declarative_automation_tests.legacy_tests.updated_scenarios.partition_scenarios import (
    partition_scenarios,
)
from dagster_tests.declarative_automation_tests.scenario_utils.asset_daemon_scenario import (
    AssetDaemonScenario,
)

all_scenarios = (
    basic_scenarios
    + cron_scenarios
    + freshness_policy_scenarios
    + partition_scenarios
    + latest_materialization_run_tag_scenarios
)


@pytest.mark.parametrize("scenario", all_scenarios, ids=[scenario.id for scenario in all_scenarios])
def test_scenario_fast(scenario: AssetDaemonScenario) -> None:
    scenario.evaluate_fast()
