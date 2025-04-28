import dagster as dg
from dagster.components.core.context import ComponentLoadContext
from dagster_dbt.components.dbt_project.component import get_asset_key_for_model_from_module
from dependency_on_dbt_project_location.defs import jaffle_shop_dbt  # type: ignore

ctx = ComponentLoadContext.current()


@dg.asset(deps={get_asset_key_for_model_from_module(ctx, jaffle_shop_dbt, "customers")})
def downstream_of_customers():
    pass
