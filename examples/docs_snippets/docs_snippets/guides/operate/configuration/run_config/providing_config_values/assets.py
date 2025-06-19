# pyright: reportMissingImports=false

# start
import dagster as dg

from .resources import MyAssetConfig


@dg.asset
def greeting(config: MyAssetConfig) -> str:
    return f"hello {config.person_name}"


asset_result = dg.materialize(
    [greeting],
    run_config=dg.RunConfig({"greeting": MyAssetConfig(person_name="Alice")}),
)
# end
