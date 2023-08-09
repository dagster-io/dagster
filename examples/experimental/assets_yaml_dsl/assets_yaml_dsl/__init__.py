from dagster import Definitions

from .assets_dsl import SomeSqlClient, assets_dsl_assets_defs

defs = Definitions(assets=assets_dsl_assets_defs, resources={"sql_client": SomeSqlClient()})
