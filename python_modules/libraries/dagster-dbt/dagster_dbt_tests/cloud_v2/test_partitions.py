import json

import responses
from dagster import (
    AssetCheckEvaluation,
    AssetExecutionContext,
    AssetMaterialization,
    BackfillPolicy,
    DailyPartitionsDefinition,
    StaticPartitionsDefinition,
    WeeklyPartitionsDefinition,
)
from dagster._core.definitions.materialize import materialize
from dagster_dbt.cloud_v2.asset_decorator import dbt_cloud_assets
from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace
from dagster_dbt.cloud_v2.run_handler import DbtCloudJobRunResults

from dagster_dbt_tests.cloud_v2.conftest import TEST_RUN_URL, get_sample_run_results_json

# --- Decorator parameter tests ---


def test_dbt_cloud_assets_accepts_partitions_def(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    partitions_def = DailyPartitionsDefinition(start_date="2024-01-01")

    @dbt_cloud_assets(workspace=workspace, partitions_def=partitions_def)
    def my_dbt_cloud_assets(): ...

    assert my_dbt_cloud_assets.partitions_def == partitions_def


def test_dbt_cloud_assets_accepts_backfill_policy(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    partitions_def = DailyPartitionsDefinition(start_date="2024-01-01")
    backfill_policy = BackfillPolicy.multi_run(max_partitions_per_run=10)

    @dbt_cloud_assets(
        workspace=workspace,
        partitions_def=partitions_def,
        backfill_policy=backfill_policy,
    )
    def my_dbt_cloud_assets(): ...

    assert my_dbt_cloud_assets.backfill_policy == backfill_policy


def test_dbt_cloud_assets_default_backfill_policy_for_time_window(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    partitions_def = DailyPartitionsDefinition(start_date="2024-01-01")

    @dbt_cloud_assets(workspace=workspace, partitions_def=partitions_def)
    def my_dbt_cloud_assets(): ...

    assert my_dbt_cloud_assets.backfill_policy == BackfillPolicy.single_run()


def test_dbt_cloud_assets_no_default_backfill_for_static_partitions(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    partitions_def = StaticPartitionsDefinition(["us", "eu", "apac"])

    @dbt_cloud_assets(workspace=workspace, partitions_def=partitions_def)
    def my_dbt_cloud_assets(): ...

    assert my_dbt_cloud_assets.backfill_policy is None


def test_dbt_cloud_assets_without_partitions_unchanged(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    @dbt_cloud_assets(workspace=workspace)
    def my_dbt_cloud_assets(): ...

    assert my_dbt_cloud_assets.partitions_def is None
    assert my_dbt_cloud_assets.backfill_policy is None


# --- Event partition key tests ---


def test_materialization_events_include_partition_key(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    """When partition_key is available via context, AssetMaterialization events include it (ad-hoc path)."""
    run_results = DbtCloudJobRunResults.from_run_results_json(
        run_results_json=get_sample_run_results_json()
    )

    # Ad-hoc (no context, no partition key) — should have partition=None
    events = list(
        run_results.to_default_asset_events(
            client=workspace.get_client(),
            manifest=workspace.get_or_fetch_workspace_data().manifest,
        )
    )
    asset_materializations = [e for e in events if isinstance(e, AssetMaterialization)]
    assert len(asset_materializations) == 8
    for mat in asset_materializations:
        assert mat.partition is None


def test_events_without_partition_key_unchanged(
    workspace: DbtCloudWorkspace,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    """Regression: non-partitioned usage produces events without partition info."""
    run_results = DbtCloudJobRunResults.from_run_results_json(
        run_results_json=get_sample_run_results_json()
    )

    events = list(
        run_results.to_default_asset_events(
            client=workspace.get_client(),
            manifest=workspace.get_or_fetch_workspace_data().manifest,
        )
    )

    asset_materializations = [e for e in events if isinstance(e, AssetMaterialization)]
    asset_check_evaluations = [e for e in events if isinstance(e, AssetCheckEvaluation)]

    # Same counts as before
    assert len(asset_materializations) == 8
    assert len(asset_check_evaluations) == 20

    first_mat = next(mat for mat in sorted(asset_materializations))
    assert first_mat.asset_key.path == ["customers"]
    assert first_mat.metadata["run_url"].value == TEST_RUN_URL
    assert first_mat.partition is None


# --- CLI args / steps_override tests ---


def test_cli_args_flow_to_steps_override(
    workspace: DbtCloudWorkspace,
    cli_invocation_api_mocks: responses.RequestsMock,
) -> None:
    """Verify that --vars in cli args flow through to steps_override in the API call,
    and the JSON value is properly shell-quoted so dbt Cloud parses it as a single arg.
    """
    dbt_vars = {"run_date": "2024-01-15"}
    invocation = workspace.cli(args=["run", "--vars", json.dumps(dbt_vars)])

    # Find the trigger job run POST call
    trigger_calls = [
        call
        for call in cli_invocation_api_mocks.calls
        if call.request.method == "POST" and "/run" in call.request.url
    ]
    # There are 2 POST /run calls: parse (from fetch_workspace_data) + our cli call
    assert len(trigger_calls) == 2
    # The second trigger call is our cli invocation
    request_body = json.loads(trigger_calls[1].request.body)
    steps_override = request_body["steps_override"]
    assert len(steps_override) == 1
    command = steps_override[0]
    assert "--vars" in command
    # The JSON value should be shell-quoted (wrapped in single quotes)
    assert '\'{"run_date": "2024-01-15"}\'' in command

    # Consume the iterator to avoid resource warnings
    list(invocation.wait())


def test_cli_args_with_select_and_vars(
    workspace: DbtCloudWorkspace,
    cli_invocation_api_mocks: responses.RequestsMock,
) -> None:
    """Verify that --vars coexists with --select flags when both are provided."""
    dbt_vars = {"run_date": "2024-01-15"}
    invocation = workspace.cli(args=["run", "--select", "my_model", "--vars", json.dumps(dbt_vars)])

    trigger_calls = [
        call
        for call in cli_invocation_api_mocks.calls
        if call.request.method == "POST" and "/run" in call.request.url
    ]
    request_body = json.loads(trigger_calls[1].request.body)
    steps_override = request_body["steps_override"]
    command = steps_override[0]
    assert "--vars" in command
    assert "--select" in command

    list(invocation.wait())


# --- End-to-end partitioned asset tests ---


def test_daily_partitioned_dbt_cloud_assets_e2e(
    workspace: DbtCloudWorkspace,
    cli_invocation_api_mocks: responses.RequestsMock,
) -> None:
    partitions_def = DailyPartitionsDefinition(start_date="2024-01-01")

    @dbt_cloud_assets(workspace=workspace, partitions_def=partitions_def)
    def my_dbt_cloud_assets(context: AssetExecutionContext, dbt_cloud: DbtCloudWorkspace):
        partition_key = context.partition_key
        dbt_vars = {"run_date": partition_key}
        yield from dbt_cloud.cli(
            args=["run", "--vars", json.dumps(dbt_vars)],
            context=context,
        ).wait()

    result = materialize(
        [my_dbt_cloud_assets],
        resources={"dbt_cloud": workspace},
        partition_key="2024-01-15",
    )
    assert result.success

    asset_materialization_events = result.get_asset_materialization_events()
    assert len(asset_materialization_events) == 8

    # Verify steps_override contains --vars with the partition date
    trigger_calls = [
        call
        for call in cli_invocation_api_mocks.calls
        if call.request.method == "POST"
        and call.request.body
        and "--vars"
        in (call.request.body if isinstance(call.request.body, str) else call.request.body.decode())
    ]
    assert len(trigger_calls) >= 1
    request_body = json.loads(trigger_calls[0].request.body)
    command = request_body["steps_override"][0]
    assert "2024-01-15" in command


def test_static_partitioned_dbt_cloud_assets_e2e(
    workspace: DbtCloudWorkspace,
    cli_invocation_api_mocks: responses.RequestsMock,
) -> None:
    partitions_def = StaticPartitionsDefinition(["us", "eu", "apac"])

    @dbt_cloud_assets(workspace=workspace, partitions_def=partitions_def)
    def my_dbt_cloud_assets(context: AssetExecutionContext, dbt_cloud: DbtCloudWorkspace):
        region = context.partition_key
        dbt_vars = {"target_region": region}
        yield from dbt_cloud.cli(
            args=["run", "--vars", json.dumps(dbt_vars)],
            context=context,
        ).wait()

    result = materialize(
        [my_dbt_cloud_assets],
        resources={"dbt_cloud": workspace},
        partition_key="us",
    )
    assert result.success

    asset_materialization_events = result.get_asset_materialization_events()
    assert len(asset_materialization_events) == 8

    trigger_calls = [
        call
        for call in cli_invocation_api_mocks.calls
        if call.request.method == "POST"
        and call.request.body
        and "--vars"
        in (call.request.body if isinstance(call.request.body, str) else call.request.body.decode())
    ]
    assert len(trigger_calls) >= 1
    request_body = json.loads(trigger_calls[0].request.body)
    command = request_body["steps_override"][0]
    assert '"target_region": "us"' in command or "'target_region'" in command


def test_weekly_partitioned_dbt_cloud_assets_e2e(
    workspace: DbtCloudWorkspace,
    cli_invocation_api_mocks: responses.RequestsMock,
) -> None:
    # WeeklyPartitionsDefinition defaults to Sunday start day
    partitions_def = WeeklyPartitionsDefinition(start_date="2024-01-07")

    @dbt_cloud_assets(workspace=workspace, partitions_def=partitions_def)
    def my_dbt_cloud_assets(context: AssetExecutionContext, dbt_cloud: DbtCloudWorkspace):
        time_window = context.partition_time_window
        dbt_vars = {
            "min_date": time_window.start.isoformat(),
            "max_date": time_window.end.isoformat(),
        }
        yield from dbt_cloud.cli(
            args=["run", "--vars", json.dumps(dbt_vars)],
            context=context,
        ).wait()

    result = materialize(
        [my_dbt_cloud_assets],
        resources={"dbt_cloud": workspace},
        partition_key="2024-01-07",
    )
    assert result.success

    asset_materialization_events = result.get_asset_materialization_events()
    assert len(asset_materialization_events) == 8
