import pytest

from .asset_daemon_scenario import AssetDaemonScenario
from .updated_scenarios.basic_scenarios import basic_scenarios

all_scenarios = basic_scenarios


@pytest.mark.parametrize("scenario", all_scenarios, ids=[scenario.id for scenario in all_scenarios])
def test_scenario(scenario: AssetDaemonScenario) -> None:
    scenario.evaluate()
