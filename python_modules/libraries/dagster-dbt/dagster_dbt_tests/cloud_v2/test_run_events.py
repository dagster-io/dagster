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


def test_default_asset_events_handles_missing_failures(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
):
    run_results_json = get_sample_run_results_json()

    for result in run_results_json["results"]:
        if result.get("unique_id", "").startswith("test."):
            result.pop("failures", None)
            result["status"] = "skipped"
            break

    run_results = DbtCloudJobRunResults.from_run_results_json(
        run_results_json=run_results_json
    )

    events = list(
        run_results.to_default_asset_events(
            client=workspace.get_client(),
            manifest=workspace.get_or_fetch_workspace_data().manifest,
        )
    )

    assert len(events) > 0

    check_evals = [e for e in events if isinstance(e, AssetCheckEvaluation)]
    skipped_evals = [e for e in check_evals if e.metadata.get("status") == "skipped"]

    if skipped_evals:
        assert "dagster_dbt/failed_row_count" not in skipped_evals[0].metadata