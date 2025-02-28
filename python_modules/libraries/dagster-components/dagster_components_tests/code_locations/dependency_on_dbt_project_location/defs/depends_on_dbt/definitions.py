from pathlib import Path

import dagster as dg
from dagster_components.components.dbt_project.component import get_asset_key_for_model
from dagster_components.core.component import ComponentLoadContext

DBT_COMPONENT_PATH = Path(__file__).parent.parent / "jaffle_shop_dbt"

ctx = ComponentLoadContext.current()


@dg.asset(deps={get_asset_key_for_model(ctx, DBT_COMPONENT_PATH, "customers")})
def downstream_of_customers():
    pass
