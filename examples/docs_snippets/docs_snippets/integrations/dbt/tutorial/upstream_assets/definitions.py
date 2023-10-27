# ruff: noqa: I001
# start_defs
import os

from dagster import Definitions
from dagster_dbt import DbtCliResource

from .assets import jaffle_shop_dbt_assets, raw_customers
from .constants import dbt_project_dir
from .schedules import schedules

defs = Definitions(
    assets=[raw_customers, jaffle_shop_dbt_assets],
    schedules=schedules,
    resources={
        "dbt": DbtCliResource(project_dir=os.fspath(dbt_project_dir)),
    },
)

# end_defs
