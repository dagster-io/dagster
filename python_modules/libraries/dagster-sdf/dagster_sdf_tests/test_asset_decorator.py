from pathlib import Path

from dagster import AssetExecutionContext, AssetKey, materialize
from dagster_sdf.asset_decorator import sdf_assets
from dagster_sdf.dagster_sdf_translator import DagsterSdfTranslator
from dagster_sdf.resource import SdfCliResource
from dagster_sdf.sdf_workspace import SdfWorkspace

from .sdf_workspaces import moms_flower_shop_path


def test_asset_deps(moms_flower_shop_target_dir: Path) -> None:
    @sdf_assets(
        workspace=SdfWorkspace(
            workspace_dir=moms_flower_shop_path, target_dir=moms_flower_shop_target_dir
        )
    )
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
    @sdf_assets(
        workspace=SdfWorkspace(
            workspace_dir=moms_flower_shop_path, target_dir=moms_flower_shop_target_dir
        )
    )
    def my_sdf_assets(context: AssetExecutionContext, sdf: SdfCliResource):
        yield from sdf.cli(["run"], context=context).stream()

    result = materialize(
        [my_sdf_assets],
        resources={"sdf": SdfCliResource(workspace_dir=moms_flower_shop_path)},
    )

    assert result.success
    assert result.get_asset_materialization_events()


def test_with_custom_translater_asset_key_fn(moms_flower_shop_target_dir: Path) -> None:
    class CustomDagsterSdfTranslator(DagsterSdfTranslator):
        def get_asset_key(self, table_name: str) -> AssetKey:
            return AssetKey([f"pre-{part}-suff" for part in table_name.split(".")])

    @sdf_assets(
        workspace=SdfWorkspace(
            workspace_dir=moms_flower_shop_path, target_dir=moms_flower_shop_target_dir
        ),
        dagster_sdf_translator=CustomDagsterSdfTranslator(),
    )
    def my_flower_shop_assets(): ...

    assert my_flower_shop_assets.asset_deps == {
        AssetKey(["pre-moms_flower_shop-suff", "pre-raw-suff", "pre-raw_addresses-suff"]): set(),
        AssetKey(["pre-moms_flower_shop-suff", "pre-raw-suff", "pre-raw_customers-suff"]): set(),
        AssetKey(["pre-moms_flower_shop-suff", "pre-raw-suff", "pre-raw_inapp_events-suff"]): set(),
        AssetKey(
            ["pre-moms_flower_shop-suff", "pre-raw-suff", "pre-raw_marketing_campaign_events-suff"]
        ): set(),
        AssetKey(["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-app_installs-suff"]): {
            AssetKey(["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-inapp_events-suff"]),
            AssetKey(
                [
                    "pre-moms_flower_shop-suff",
                    "pre-raw-suff",
                    "pre-raw_marketing_campaign_events-suff",
                ]
            ),
        },
        AssetKey(["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-app_installs_v2-suff"]): {
            AssetKey(["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-inapp_events-suff"]),
            AssetKey(
                [
                    "pre-moms_flower_shop-suff",
                    "pre-raw-suff",
                    "pre-raw_marketing_campaign_events-suff",
                ]
            ),
        },
        AssetKey(["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-customers-suff"]): {
            AssetKey(["pre-moms_flower_shop-suff", "pre-raw-suff", "pre-raw_addresses-suff"]),
            AssetKey(["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-app_installs_v2-suff"]),
            AssetKey(["pre-moms_flower_shop-suff", "pre-raw-suff", "pre-raw_customers-suff"]),
        },
        AssetKey(["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-inapp_events-suff"]): {
            AssetKey(["pre-moms_flower_shop-suff", "pre-raw-suff", "pre-raw_inapp_events-suff"])
        },
        AssetKey(
            ["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-marketing_campaigns-suff"]
        ): {
            AssetKey(
                [
                    "pre-moms_flower_shop-suff",
                    "pre-raw-suff",
                    "pre-raw_marketing_campaign_events-suff",
                ]
            )
        },
        AssetKey(
            ["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-stg_installs_per_campaign-suff"]
        ): {
            AssetKey(["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-app_installs_v2-suff"])
        },
        AssetKey(
            [
                "pre-moms_flower_shop-suff",
                "pre-analytics-suff",
                "pre-agg_installs_and_campaigns-suff",
            ]
        ): {
            AssetKey(["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-app_installs_v2-suff"])
        },
        AssetKey(
            ["pre-moms_flower_shop-suff", "pre-analytics-suff", "pre-dim_marketing_campaigns-suff"]
        ): {
            AssetKey(
                ["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-marketing_campaigns-suff"]
            ),
            AssetKey(
                [
                    "pre-moms_flower_shop-suff",
                    "pre-staging-suff",
                    "pre-stg_installs_per_campaign-suff",
                ]
            ),
        },
    }
