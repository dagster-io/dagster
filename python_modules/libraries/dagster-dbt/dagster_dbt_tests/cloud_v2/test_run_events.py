from dagster import AssetMaterialization
from dagster_dbt.cloud_v2.run_handler import DbtCloudJobRunResults
from dagster_dbt.cloud_v2.types import DbtCloudWorkspaceData

from dagster_dbt_tests.cloud_v2.conftest import get_sample_run_results_json


def test_default_asset_events_from_run_results(workspace_data: DbtCloudWorkspaceData):
    run_results = DbtCloudJobRunResults.from_run_results_json(
        run_results_json=get_sample_run_results_json()
    )

    events = [event for event in run_results.to_default_asset_events(workspace_data=workspace_data)]

    # 3 asset materializations
    assert len(events) == 3
    assert all(isinstance(event, AssetMaterialization) for event in events)

    # Sanity check
    first_mat = next(mat for mat in sorted(events))
    assert first_mat.asset_key.path == ["raw_customers"]
