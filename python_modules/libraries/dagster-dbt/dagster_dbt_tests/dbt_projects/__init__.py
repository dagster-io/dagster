from pathlib import Path

projects_path = Path(__file__).joinpath("..").resolve()

test_jaffle_shop_path = projects_path.joinpath("jaffle_shop")
test_asset_checks_path = projects_path.joinpath("test_dagster_asset_checks")
test_asset_key_exceptions_path = projects_path.joinpath("test_dagster_asset_key_exceptions")
test_dbt_alias_path = projects_path.joinpath("test_dagster_dbt_alias")
test_dbt_model_versions_path = projects_path.joinpath("test_dagster_dbt_model_versions")
test_dbt_python_interleaving_path = projects_path.joinpath("test_dagster_dbt_python_interleaving")
test_dbt_semantic_models_path = projects_path.joinpath("test_dagster_dbt_semantic_models")
test_dbt_source_freshness_path = projects_path.joinpath("test_dagster_dbt_source_freshness")
test_dbt_unit_tests_path = projects_path.joinpath("test_dagster_dbt_unit_tests")
test_duplicate_source_asset_key_path = projects_path.joinpath(
    "test_dagster_duplicate_source_asset_key"
)
test_exceptions_path = projects_path.joinpath("test_dagster_exceptions")
test_meta_config_path = projects_path.joinpath("test_dagster_meta_config")
test_metadata_path = projects_path.joinpath("test_dagster_metadata")
test_last_update_freshness_path = projects_path.joinpath("test_dagster_last_update_freshness")
test_last_update_freshness_multiple_assets_defs_path = projects_path.joinpath(
    "test_dagster_last_update_freshness_multiple_assets_defs"
)
test_time_partition_freshness_path = projects_path.joinpath("test_dagster_time_partition_freshness")
test_time_partition_freshness_multiple_assets_defs_path = projects_path.joinpath(
    "test_dagster_time_partition_freshness_multiple_assets_defs"
)
test_dagster_dbt_mixed_freshness_path = projects_path.joinpath("test_dagster_dbt_mixed_freshness")
test_jaffle_with_profile_vars_path = projects_path.joinpath("test_jaffle_with_profile_vars")
test_dependencies_path = projects_path.joinpath("test_dagster_dbt_dependencies")
