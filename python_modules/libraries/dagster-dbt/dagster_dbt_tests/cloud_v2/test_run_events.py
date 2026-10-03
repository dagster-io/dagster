import copy

import pytest
import responses
from dagster import AssetCheckEvaluation, AssetMaterialization
from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace
from dagster_dbt.cloud_v2.run_handler import (
    COMPLETED_AT_TIMESTAMP_METADATA_KEY,
    DbtCloudJobRunResults,
)
from dateutil import parser

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


@pytest.mark.parametrize("status", ["no-op", "reused", "warn"])
def test_default_asset_events_from_run_results_non_error_statuses(
    status: str,
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
):
    """`no-op` and `reused` are terminal, non-error dbt statuses meaning the node was not rebuilt.
    The models they are reported for should still materialize rather than be dropped as failures.
    """
    run_results_json = copy.deepcopy(dict(get_sample_run_results_json()))
    for result in run_results_json["results"]:
        if result["status"] == "success":
            result["status"] = status
            # dbt does not record timings for a node it never built.
            result["timing"] = []

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

    # The status is surfaced as metadata so that it is visible that nothing was built.
    for materialization in asset_materializations:
        assert materialization.metadata["status"].value == status


def test_default_asset_events_from_run_results_error_status(
    workspace: DbtCloudWorkspace, fetch_workspace_data_api_mocks: responses.RequestsMock
):
    """Models that errored are still not materialized."""
    run_results_json = copy.deepcopy(dict(get_sample_run_results_json()))
    for result in run_results_json["results"]:
        if result["status"] == "success":
            result["status"] = "error"

    run_results = DbtCloudJobRunResults.from_run_results_json(run_results_json=run_results_json)

    events = list(
        run_results.to_default_asset_events(
            client=workspace.get_client(),
            manifest=workspace.get_or_fetch_workspace_data().manifest,
        )
    )

    assert [event for event in events if isinstance(event, AssetMaterialization)] == []


@pytest.mark.parametrize("status", ["no-op", "reused"])
def test_timing_less_results_use_the_run_generated_at_timestamp(
    status: str,
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
):
    """A node dbt never built can have no timing entries. The completion timestamp must come
    from the run's own `generated_at` rather than the current time -- the polling sensor sorts
    an asset's events by it, so a wall-clock fallback would make an older run that skipped the
    node sort ahead of a newer run that actually rebuilt it.
    """
    run_results_json = copy.deepcopy(dict(get_sample_run_results_json()))
    for result in run_results_json["results"]:
        if result["status"] == "success":
            result["status"] = status
            result["timing"] = []

    expected = parser.parse(run_results_json["metadata"]["generated_at"]).timestamp()

    run_results = DbtCloudJobRunResults.from_run_results_json(run_results_json=run_results_json)

    events = list(
        run_results.to_default_asset_events(
            client=workspace.get_client(),
            manifest=workspace.get_or_fetch_workspace_data().manifest,
        )
    )

    asset_materializations = [event for event in events if isinstance(event, AssetMaterialization)]
    assert len(asset_materializations) == 8
    for materialization in asset_materializations:
        assert materialization.metadata[COMPLETED_AT_TIMESTAMP_METADATA_KEY].value == expected
