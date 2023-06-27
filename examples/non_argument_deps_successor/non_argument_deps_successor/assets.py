import profile
from dagster_dbt import load_assets_from_dbt_project
from dagster import asset, AssetKey
from dagster._utils import file_relative_path

DBT_PROJECT_DIR = file_relative_path(__file__, "../jaffle_shop")
DBT_PROFILES_DIR = file_relative_path(__file__, "../jaffle_shop/config")
DBT_MANIFEST = file_relative_path(__file__, "../jaffle_shop/target/manifest.json")

# dbt_assets = load_assets_from_dbt_project(project_dir=DBT_PROJECT_DIR, profiles_dir=DBT_PROFILES_DIR)

# @asset(
#     deps=[AssetKey(["customers"]), AssetKey(["stg_customers"])],
#     group_name="staging"
# )
# def downstream_of_dbt():
#     return None

from dagster_dbt.cli import DbtCli, DbtManifest
from dagster_dbt.asset_decorator import dbt_assets

manifest = DbtManifest.read(path=DBT_MANIFEST)


@dbt_assets(
    manifest=manifest,
    select="stg_customers stg_orders customers",
)
def jaffle_shop_dbt_assets(context, dbt: DbtCli):
    yield from dbt.cli(["run"], manifest=manifest, context=context).stream()


@asset(deps=[manifest.get_asset_key_for_model("customers")], group_name="staging")
def downstream_of_dbt():
    return None
