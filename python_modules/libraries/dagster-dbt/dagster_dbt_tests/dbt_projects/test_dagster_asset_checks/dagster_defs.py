from pathlib import Path

import dagster as dg
import dagster_dbt as dg_dbt

# Set env vars:
# export DAGSTER_DBT_PYTEST_XDIST_DUCKDB_DBFILE_NAME=master_jaffle_shop
# export DAGSTER_DBT_PYTEST_XDIST_DUCKDB_DBFILE_PATH=target/master_jaffle_shop.duckdb


project = dg_dbt.DbtProject(
    project_dir=Path(__file__).parent.resolve(),
)
project.prepare_if_dev()


@dg_dbt.dbt_assets(
    project=project,
    manifest=project.manifest_path,
    dagster_dbt_translator=dg_dbt.DagsterDbtTranslator(
        dg_dbt.DagsterDbtTranslatorSettings(enable_source_tests_as_checks=True)
    ),
)
def my_dbt_assets(context: dg.AssetExecutionContext, dbt: dg_dbt.DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


# @dg.multi_asset(specs=[dg.AssetSpec(key="abc", deps=["upstream"])], check_specs=[dg.AssetCheckSpec(name="my_check", asset="upstream")], _disable_check_specs_target_relevant_asset_keys=True)
# def my_asset():
#     pass

# # simulates having a check targeting an upstream asset
# @dg.multi_asset(specs=[dg.AssetSpec(key="unrelated", deps=["upstream"])], check_specs=[dg.AssetCheckSpec(name="my_check", asset="upstream")], _disable_check_specs_target_relevant_asset_keys=True)
# def my_unrelated_asset():
#     pass


print(" I AM LOADING THE DAGSTER DEFS")

defs = dg.Definitions(
    assets=[my_dbt_assets],
    resources={"dbt": dg_dbt.DbtCliResource(project_dir=project.project_dir)},
)
