from pathlib import Path

import dagster as dg
from dagster.components.core.defs_module import ComponentPath
from dagster_dbt import DbtProjectComponent


@dg.definitions
def defs(context: dg.ComponentLoadContext) -> dg.Definitions:
    customers_asset_key = context.component_tree.load_component_at_path(
        ComponentPath(file_path=Path("jaffle_shop_dbt"), instance_key=0),
        expected_type=DbtProjectComponent,
    ).get_asset_key_for_model("customers")

    @dg.asset(deps={customers_asset_key})
    def downstream_of_customers():
        pass

    return dg.Definitions(assets=[downstream_of_customers])
