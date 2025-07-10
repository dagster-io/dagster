import dagster as dg
from dagster.components.core.context import ComponentLoadContext
from dagster_dbt import DbtProjectComponent


@dg.definitions
def defs(context: ComponentLoadContext) -> dg.Definitions:
    customers_asset_key = context.component_tree.load_component_at_path(
        "jaffle_shop_dbt", expected_type=DbtProjectComponent
    ).asset_key_for_model(context, "customers")

    @dg.asset(deps={customers_asset_key})
    def downstream_of_customers():
        pass

    return dg.Definitions(assets=[downstream_of_customers])
