import dagster as dg
from dagster_components.components.dbt_project.component import get_component_asset_key_for_model
from dagster_components.core.component import ComponentLoadContext
from dependency_on_dbt_project_location.defs import jaffle_shop_dbt

ctx = ComponentLoadContext.current()


@dg.asset(deps={get_component_asset_key_for_model(ctx, jaffle_shop_dbt, "customers")})
def downstream_of_customers():
    pass
