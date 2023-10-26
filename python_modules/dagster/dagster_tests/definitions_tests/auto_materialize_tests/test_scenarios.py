import pytest
from dagster._core.instance import DagsterInstance
from dagster._core.instance_for_test import instance_for_test
from dagster._daemon.asset_daemon import set_auto_materialize_paused

from .asset_daemon_scenario import AssetDaemonScenario
from .updated_scenarios.basic_scenarios import basic_scenarios

all_scenarios = basic_scenarios


@pytest.fixture
def daemon_instance():
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster._core.launcher.sync_in_memory_run_launcher",
                "class": "SyncInMemoryRunLauncher",
            }
        }
    ) as the_instance:
        set_auto_materialize_paused(the_instance, False)
        yield the_instance


@pytest.mark.parametrize("scenario", all_scenarios, ids=[scenario.id for scenario in all_scenarios])
def test_scenario_fast(scenario: AssetDaemonScenario) -> None:
    scenario.evaluate_fast()


@pytest.mark.parametrize("scenario", all_scenarios, ids=[scenario.id for scenario in all_scenarios])
def test_scenario_daemon(scenario: AssetDaemonScenario, daemon_instance: DagsterInstance) -> None:
    scenario.evaluate_daemon(daemon_instance)
