import dagster as dg
from dagster_components.components.dbt_project.component import get_asset_key_for_model_from_module
from dagster_components.core.component import DefsModuleLoadContext
from dependency_on_dbt_project_location.defs import jaffle_shop_dbt  # type: ignore

ctx = DefsModuleLoadContext.current()


@dg.asset(deps={get_asset_key_for_model_from_module(ctx, jaffle_shop_dbt, "customers")})
def downstream_of_customers():
    pass
