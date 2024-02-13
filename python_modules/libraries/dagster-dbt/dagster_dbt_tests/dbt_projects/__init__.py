from pathlib import Path

projects_path = Path(__file__).joinpath("..").resolve()

test_asset_checks_path = projects_path.joinpath("test_dagster_asset_checks")
test_asset_key_exceptions_path = projects_path.joinpath("test_dagster_asset_key_exceptions")
test_dbt_python_interleaving_path = projects_path.joinpath("test_dagster_dbt_python_interleaving")
test_exceptions_path = projects_path.joinpath("test_dagster_exceptions")
test_meta_config_path = projects_path.joinpath("test_dagster_meta_config")
