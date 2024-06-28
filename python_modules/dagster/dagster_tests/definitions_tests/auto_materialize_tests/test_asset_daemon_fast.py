import pytest
from dagster import AssetMaterialization, AssetSelection, DagsterInstance, job, op
from dagster._core.definitions.time_window_partitions import HourlyPartitionsDefinition

from .base_scenario import AssetReconciliationScenario, asset_def
from .scenarios.scenarios import ASSET_RECONCILIATION_SCENARIOS

#############################
# FAST auto materialize tests
#############################
#
# Run the auto materialize scenarios, but use an AssetGraph instead of RemoteAssetGraph to speed things up.


@pytest.mark.parametrize(
    "respect_materialization_data_versions",
    [True, False],
)
@pytest.mark.parametrize(
    "scenario",
    list(ASSET_RECONCILIATION_SCENARIOS.values()),
    ids=list(ASSET_RECONCILIATION_SCENARIOS.keys()),
)
@pytest.mark.parametrize("emit_backfills", [True, False])
def test_reconciliation(scenario, respect_materialization_data_versions, emit_backfills):
    instance = DagsterInstance.ephemeral()

    # need to override this method on the instance since it is hard-coded to False. Once we
    # determine how we want to enable the feature, we can change this
    def override_da_backfill_setting(self):
        return emit_backfills

    instance.da_emit_backfills = override_da_backfill_setting.__get__(instance, DagsterInstance)
    run_requests, _, evaluations = scenario.do_sensor_scenario(
        instance, respect_materialization_data_versions=respect_materialization_data_versions
    )

    if emit_backfills:
        assert len(run_requests) == len(scenario.expected_run_requests_for_backfill_daemon)

        if len(run_requests) > 0:
            assert len(run_requests) == 1
            assert (
                run_requests[0].asset_graph_subset
                == scenario.expected_run_requests_for_backfill_daemon[0].asset_graph_subset
            )
    else:
        assert len(run_requests) == len(scenario.expected_run_requests), evaluations

        def sort_run_request_key_fn(run_request):
            return (min(run_request.asset_selection), run_request.partition_key)

        sorted_run_requests = sorted(run_requests, key=sort_run_request_key_fn)
        sorted_expected_run_requests = sorted(
            scenario.expected_run_requests, key=sort_run_request_key_fn
        )

        for run_request, expected_run_request in zip(
            sorted_run_requests, sorted_expected_run_requests
        ):
            assert set(run_request.asset_selection) == set(expected_run_request.asset_selection)
            assert run_request.partition_key == expected_run_request.partition_key


@pytest.mark.parametrize(
    "scenario",
    [ASSET_RECONCILIATION_SCENARIOS["freshness_complex_subsettable"]],
)
def test_reconciliation_no_tags(scenario):
    # simulates an environment where asset_event_tags cannot be added
    instance = DagsterInstance.ephemeral()

    run_requests, _, _ = scenario.do_sensor_scenario(instance)

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


def test_bad_partition_key():
    hourly_partitions_def = HourlyPartitionsDefinition("2013-01-05-00:00")
    assets = [
        asset_def("hourly1", partitions_def=hourly_partitions_def),
        asset_def("hourly2", ["hourly1"], partitions_def=hourly_partitions_def),
    ]

    instance = DagsterInstance.ephemeral()

    @op
    def materialization_op(context):
        context.log_event(AssetMaterialization("hourly1", partition="bad partition key"))

    @job
    def materialization_job():
        materialization_op()

    materialization_job.execute_in_process(instance=instance)

    scenario = AssetReconciliationScenario(
        assets=assets, unevaluated_runs=[], asset_selection=AssetSelection.assets("hourly2")
    )
    run_requests, _, _ = scenario.do_sensor_scenario(instance)
    assert len(run_requests) == 0
