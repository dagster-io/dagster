# ruff: noqa: I001
# start_defs
import os

from dagster import Definitions
from dagster_dbt import DbtCliResource

from .assets import jaffle_shop_dbt_assets, raw_customers
from .artifacts import dbt_artifacts
from .schedules import schedules

defs = Definitions(
    assets=[raw_customers, jaffle_shop_dbt_assets],
    schedules=schedules,
    resources={
        "dbt": dbt_artifacts.get_cli_resource(),
    },
)

# end_defs
