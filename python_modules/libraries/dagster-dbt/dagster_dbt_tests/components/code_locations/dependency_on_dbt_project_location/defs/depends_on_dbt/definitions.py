import dagster as dg
from dagster.components.core.context import ComponentLoadContext
from dagster_dbt.asset_utils import get_asset_key_for_model


@dg.definitions
def defs(context: ComponentLoadContext) -> dg.Definitions:
    dbt_assets = (
        context.component_tree.build_defs_at_path("jaffle_shop_dbt")
        .resolve_asset_graph()
        .assets_defs
    )

    @dg.asset(deps={get_asset_key_for_model(dbt_assets, "customers")})
    def downstream_of_customers():
        pass

    return dg.Definitions(assets=[downstream_of_customers])
