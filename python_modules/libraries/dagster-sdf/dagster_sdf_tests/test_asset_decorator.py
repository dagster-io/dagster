from pathlib import Path

from dagster import AssetExecutionContext, AssetKey, materialize
from dagster_sdf.asset_decorator import sdf_assets
from dagster_sdf.information_schema import SdfInformationSchema
from dagster_sdf.resource import SdfCliResource

from .sdf_workspaces import moms_flower_shop_path


def test_asset_deps(moms_flower_shop_target_dir: Path) -> None:
    @sdf_assets(information_schema=SdfInformationSchema(target_dir=moms_flower_shop_target_dir))
    def my_flower_shop_assets(): ...

    assert my_flower_shop_assets.asset_deps == {
        AssetKey(["moms_flower_shop", "raw", "raw_addresses"]): set(),
        AssetKey(["moms_flower_shop", "raw", "raw_customers"]): set(),
        AssetKey(["moms_flower_shop", "raw", "raw_inapp_events"]): set(),
        AssetKey(["moms_flower_shop", "raw", "raw_marketing_campaign_events"]): set(),
        AssetKey(["moms_flower_shop", "staging", "app_installs"]): {
            AssetKey(["moms_flower_shop", "staging", "inapp_events"]),
            AssetKey(["moms_flower_shop", "raw", "raw_marketing_campaign_events"]),
        },
        AssetKey(["moms_flower_shop", "staging", "app_installs_v2"]): {
            AssetKey(["moms_flower_shop", "staging", "inapp_events"]),
            AssetKey(["moms_flower_shop", "raw", "raw_marketing_campaign_events"]),
        },
        AssetKey(["moms_flower_shop", "staging", "customers"]): {
            AssetKey(["moms_flower_shop", "raw", "raw_addresses"]),
            AssetKey(["moms_flower_shop", "staging", "app_installs_v2"]),
            AssetKey(["moms_flower_shop", "raw", "raw_customers"]),
        },
        AssetKey(["moms_flower_shop", "staging", "inapp_events"]): {
            AssetKey(["moms_flower_shop", "raw", "raw_inapp_events"])
        },
        AssetKey(["moms_flower_shop", "staging", "marketing_campaigns"]): {
            AssetKey(["moms_flower_shop", "raw", "raw_marketing_campaign_events"])
        },
        AssetKey(["moms_flower_shop", "staging", "stg_installs_per_campaign"]): {
            AssetKey(["moms_flower_shop", "staging", "app_installs_v2"])
        },
        AssetKey(["moms_flower_shop", "analytics", "agg_installs_and_campaigns"]): {
            AssetKey(["moms_flower_shop", "staging", "app_installs_v2"])
        },
        AssetKey(["moms_flower_shop", "analytics", "dim_marketing_campaigns"]): {
            AssetKey(["moms_flower_shop", "staging", "marketing_campaigns"]),
            AssetKey(["moms_flower_shop", "staging", "stg_installs_per_campaign"]),
        },
    }


def test_sdf_with_materialize(moms_flower_shop_target_dir: Path) -> None:
    @sdf_assets(information_schema=SdfInformationSchema(target_dir=moms_flower_shop_target_dir))
    def my_sdf_assets(context: AssetExecutionContext, sdf: SdfCliResource):
        yield from sdf.cli(["run"], context=context).stream()

    result = materialize(
        [my_sdf_assets],
        resources={"sdf": SdfCliResource(workspace_dir=moms_flower_shop_path)},
    )

    assert result.success
    assert result.get_asset_materialization_events()
