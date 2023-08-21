from dagster import Definitions

from .assets_dsl import SomeSqlClient, get_asset_dsl_example_defs
from .stocks_dsl import get_stocks_dsl_example_defs

defs = Definitions(
    assets=get_asset_dsl_example_defs() + get_stocks_dsl_example_defs(),
    resources={"sql_client": SomeSqlClient()},
)
