import pytest
from dagster import DagsterInstance
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._daemon.asset_daemon import set_auto_materialize_paused

from .auto_materialize_policy_scenarios import auto_materialize_policy_scenarios
from .multi_code_location_scenarios import multi_code_location_scenarios
from .scenarios import ASSET_RECONCILIATION_SCENARIOS


@pytest.mark.parametrize(
    "scenario_item",
    list(ASSET_RECONCILIATION_SCENARIOS.items()),
    ids=list(ASSET_RECONCILIATION_SCENARIOS.keys()),
)
def test_reconcile_with_external_asset_graph(scenario_item):
    scenario_name, scenario = scenario_item
    instance = DagsterInstance.ephemeral()
    run_requests, _ = scenario.do_sensor_scenario(
        instance, scenario_name=scenario_name, with_external_asset_graph=True
    )

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


daemon_scenarios = {**auto_materialize_policy_scenarios, **multi_code_location_scenarios}


@pytest.fixture
def daemon_not_paused_instance():
    instance = DagsterInstance.ephemeral()
    set_auto_materialize_paused(instance, False)
    yield instance


@pytest.mark.parametrize(
    "scenario_item",
    list(daemon_scenarios.items()),
    ids=list(daemon_scenarios.keys()),
)
def test_daemon(scenario_item, daemon_not_paused_instance):
    scenario_name, scenario = scenario_item
    scenario.do_daemon_scenario(daemon_not_paused_instance, scenario_name=scenario_name)

    runs = daemon_not_paused_instance.get_runs()

    assert len(runs) == len(
        scenario.expected_run_requests
        + scenario.unevaluated_runs
        + (scenario.cursor_from.unevaluated_runs if scenario.cursor_from else [])
    )

    for run in runs:
        assert run.status == DagsterRunStatus.SUCCESS

    def sort_run_request_key_fn(run_request):
        return (min(run_request.asset_selection), run_request.partition_key)

    def sort_run_key_fn(run):
        return (min(run.asset_selection), run.tags.get(PARTITION_NAME_TAG))

    sorted_runs = sorted(runs[: len(scenario.expected_run_requests)], key=sort_run_key_fn)
    sorted_expected_run_requests = sorted(
        scenario.expected_run_requests, key=sort_run_request_key_fn
    )
    for run, expected_run_request in zip(sorted_runs, sorted_expected_run_requests):
        assert run.asset_selection is not None
        assert set(run.asset_selection) == set(expected_run_request.asset_selection)
        assert run.tags.get(PARTITION_NAME_TAG) == expected_run_request.partition_key


def test_daemon_run_tags():
    scenario_name = "auto_materialize_policy_eager_with_freshness_policies"
    scenario = auto_materialize_policy_scenarios[scenario_name]

    instance = DagsterInstance.ephemeral(
        settings={"auto_materialize": {"run_tags": {"foo": "bar"}}}
    )
    set_auto_materialize_paused(instance, False)
    scenario.do_daemon_scenario(instance, scenario_name=scenario_name)

    runs = instance.get_runs()

    assert len(runs) == len(
        scenario.expected_run_requests
        + scenario.unevaluated_runs
        + (scenario.cursor_from.unevaluated_runs if scenario.cursor_from else [])
    )

    for run in runs:
        assert run.status == DagsterRunStatus.SUCCESS

    def sort_run_request_key_fn(run_request):
        return (min(run_request.asset_selection), run_request.partition_key)

    def sort_run_key_fn(run):
        return (min(run.asset_selection), run.tags.get(PARTITION_NAME_TAG))

    sorted_runs = sorted(runs[: len(scenario.expected_run_requests)], key=sort_run_key_fn)
    sorted_expected_run_requests = sorted(
        scenario.expected_run_requests, key=sort_run_request_key_fn
    )
    for run, expected_run_request in zip(sorted_runs, sorted_expected_run_requests):
        assert run.asset_selection is not None
        assert set(run.asset_selection) == set(expected_run_request.asset_selection)
        assert run.tags.get(PARTITION_NAME_TAG) == expected_run_request.partition_key
        assert run.tags["foo"] == "bar"


def test_daemon_paused():
    scenario_name = "auto_materialize_policy_eager_with_freshness_policies"
    scenario = auto_materialize_policy_scenarios[scenario_name]

    instance = DagsterInstance.ephemeral()
    scenario.do_daemon_scenario(instance, scenario_name=scenario_name)

    runs = instance.get_runs()

    # daemon is paused by default , so no new runs should have been created
    assert len(runs) == len(
        scenario.unevaluated_runs
        + (scenario.cursor_from.unevaluated_runs if scenario.cursor_from else [])
    )

    instance.wipe()
    set_auto_materialize_paused(instance, False)
    scenario.do_daemon_scenario(instance, scenario_name=scenario_name)
    runs = instance.get_runs()

    assert len(runs) == len(
        scenario.expected_run_requests
        + scenario.unevaluated_runs
        + (scenario.cursor_from.unevaluated_runs if scenario.cursor_from else [])
    )
