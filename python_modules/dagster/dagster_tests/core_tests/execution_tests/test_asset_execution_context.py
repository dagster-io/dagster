import dagster._check as check
from dagster import OpExecutionContext, AssetExecutionContext, asset, materialize


def test_deprecation_warnings():
    # Test that every method on OpExecutionContext is either reimplemented by AssetExecutionContext
    # or throws a deprecation warning on AssetExecutionContext

    asset_execution_context_methods = [
        "op_execution_context",
        "is_asset_step",
        "asset_key",
        "asset_keys",
        "provenance",
        "provenance_by_asset_key",
        "code_version",
        "code_version_by_asset_key",
        "is_partition_step",
        "partition_key",
        "partition_key_range",
        "partition_time_window",
        "run_id",
        "job_name",
        "retry_number",
        "dagster_run",
        "pdb",
        "log",
        "log_event",
        "assets_def",
        "selected_asset_keys",
        "get_asset_provenance",
        "get_assets_code_version",
        "asset_check_spec",
        "partition_kgey_range_for_asset_key",
    ]
