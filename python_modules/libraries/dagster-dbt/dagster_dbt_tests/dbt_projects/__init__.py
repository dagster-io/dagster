from pathlib import Path

projects_path = Path(__file__).joinpath("..").resolve()

test_jaffle_shop_path = projects_path.joinpath("jaffle_shop")
test_asset_checks_path = projects_path.joinpath("test_dagster_asset_checks")
test_asset_key_exceptions_path = projects_path.joinpath("test_dagster_asset_key_exceptions")
test_dbt_alias_path = projects_path.joinpath("test_dagster_dbt_alias")
test_dbt_model_versions_path = projects_path.joinpath("test_dagster_dbt_model_versions")
test_dbt_python_interleaving_path = projects_path.joinpath("test_dagster_dbt_python_interleaving")
test_dbt_semantic_models_path = projects_path.joinpath("test_dagster_dbt_semantic_models")
test_duplicate_source_asset_key_path = projects_path.joinpath(
    "test_dagster_duplicate_source_asset_key"
)
test_exceptions_path = projects_path.joinpath("test_dagster_exceptions")
test_meta_config_path = projects_path.joinpath("test_dagster_meta_config")
test_metadata_path = projects_path.joinpath("test_dagster_metadata")
