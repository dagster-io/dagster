import copy

import responses
from dagster import AssetCheckEvaluation, AssetMaterialization
from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace
from dagster_dbt.cloud_v2.run_handler import DbtCloudJobRunResults

from dagster_dbt_tests.cloud_v2.conftest import TEST_RUN_URL, get_sample_run_results_json


def test_default_asset_events_from_run_results(
    workspace: DbtCloudWorkspace, fetch_workspace_data_api_mocks: responses.RequestsMock
):
    run_results = DbtCloudJobRunResults.from_run_results_json(
        run_results_json=get_sample_run_results_json()
    )

    events = [
        event
        for event in run_results.to_default_asset_events(
            client=workspace.get_client(), manifest=workspace.get_or_fetch_workspace_data().manifest
        )
    ]

    asset_materializations = [event for event in events if isinstance(event, AssetMaterialization)]
    asset_check_evaluations = [event for event in events if isinstance(event, AssetCheckEvaluation)]

    # 8 asset materializations
    assert len(asset_materializations) == 8
    # 20 asset check evaluations
    assert len(asset_check_evaluations) == 20

    # Sanity check
    first_mat = next(mat for mat in sorted(asset_materializations))
    assert first_mat.asset_key.path == ["customers"]
    assert first_mat.metadata["run_url"].value == TEST_RUN_URL

    first_check_eval = next(check_eval for check_eval in sorted(asset_check_evaluations))
    assert first_check_eval.check_name == "not_null_customers_customer_id"
    assert first_check_eval.asset_key.path == ["customers"]
    # dbt Core includes the `failures` count, which we surface as metadata.
    assert "dagster_dbt/failed_row_count" in first_check_eval.metadata


def test_default_asset_events_from_run_results_missing_failures_key(
    workspace: DbtCloudWorkspace, fetch_workspace_data_api_mocks: responses.RequestsMock
):
    run_results_json = copy.deepcopy(dict(get_sample_run_results_json()))
    for result in run_results_json["results"]:
        result.pop("failures", None)

    run_results = DbtCloudJobRunResults.from_run_results_json(run_results_json=run_results_json)

    events = list(
        run_results.to_default_asset_events(
            client=workspace.get_client(),
            manifest=workspace.get_or_fetch_workspace_data().manifest,
        )
    )

    asset_materializations = [event for event in events if isinstance(event, AssetMaterialization)]
    asset_check_evaluations = [event for event in events if isinstance(event, AssetCheckEvaluation)]

    assert len(asset_materializations) == 8
    assert len(asset_check_evaluations) == 20

    # Without a `failures` count, we should not attach failed row count metadata.
    for check_eval in asset_check_evaluations:
        assert "dagster_dbt/failed_row_count" not in check_eval.metadata


def test_default_asset_events_from_run_results_noop_status(
    workspace: DbtCloudWorkspace, fetch_workspace_data_api_mocks: responses.RequestsMock
):
    """dbt state-reuse produces `status: "no-op"` for models that were skipped
    because state said they were already up-to-date. Those models ARE materialized
    (they exist in the warehouse); we must yield materialization events for them
    so the Dagster asset graph reflects reality — otherwise the run appears to
    have "missed" every reused model.
    """
    run_results_json = copy.deepcopy(dict(get_sample_run_results_json()))

    # Flip every model result to no-op — simulate a state-reuse run where nothing
    # actually re-executed.
    for result in run_results_json["results"]:
        if not result["unique_id"].startswith("test."):
            result["status"] = "no-op"

    run_results = DbtCloudJobRunResults.from_run_results_json(run_results_json=run_results_json)

    events = list(
        run_results.to_default_asset_events(
            client=workspace.get_client(),
            manifest=workspace.get_or_fetch_workspace_data().manifest,
        )
    )

    asset_materializations = [event for event in events if isinstance(event, AssetMaterialization)]

    # Same count as the success case (8 models materialized) — no-op should be
    # treated as success-equivalent.
    assert len(asset_materializations) == 8, (
        f"Expected 8 materializations for no-op models (state reuse should be "
        f"treated as success), got {len(asset_materializations)}"
    )
