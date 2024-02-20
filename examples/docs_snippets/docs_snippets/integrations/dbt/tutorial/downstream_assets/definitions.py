# ruff: noqa: I001
# start_defs
import os

from dagster import Definitions
from dagster_dbt import DbtCliResource

from .assets import jaffle_shop_dbt_assets, order_count_chart, raw_customers
from .project import jaffle_shop_project
from .schedules import schedules

defs = Definitions(
    assets=[raw_customers, jaffle_shop_dbt_assets, order_count_chart],
    schedules=schedules,
    resources={
        "dbt": DbtCliResource(jaffle_shop_project),
    },
)

# end_defs
