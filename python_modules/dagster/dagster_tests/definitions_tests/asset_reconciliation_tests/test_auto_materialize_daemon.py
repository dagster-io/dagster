import pytest
from dagster import DagsterInstance

from .scenarios import ASSET_RECONCILIATION_SCENARIOS

AUTO_MATERIALIZE_DAEMON_SCENARIOS = ASSET_RECONCILIATION_SCENARIOS.copy()

# These cases use asset_selections, which the daemon does not support
AUTO_MATERIALIZE_DAEMON_SCENARIOS.pop("freshness_many_to_one_roots_unselectable")
AUTO_MATERIALIZE_DAEMON_SCENARIOS.pop("freshness_complex_subsettable")


@pytest.mark.parametrize(
    "scenario_item",
    list(AUTO_MATERIALIZE_DAEMON_SCENARIOS.items()),
    ids=list(AUTO_MATERIALIZE_DAEMON_SCENARIOS.keys()),
)
def test_daemon(scenario_item):
    scenario_name, scenario = scenario_item
    instance = DagsterInstance.ephemeral()
    run_requests, _ = scenario.do_scenario(instance, scenario_name=scenario_name, with_daemon=True)

    assert len(run_requests) == len(scenario.expected_run_requests)

    def sort_run_request_key_fn(run_request):
        return (min(run_request.asset_selection), run_request.partition_key)

    sorted_run_requests = sorted(run_requests, key=sort_run_request_key_fn)
    sorted_expected_run_requests = sorted(
        scenario.expected_run_requests, key=sort_run_request_key_fn
    )

    for run_request, expected_run_request in zip(sorted_run_requests, sorted_expected_run_requests):
        assert set(run_request.asset_selection) == set(expected_run_request.asset_selection)
        assert run_request.partition_key == expected_run_request.partition_key
