# pyright: reportMissingImports=false

# start
import dagster as dg

from .resources import MyAssetConfig


@dg.asset
def greeting(config: MyAssetConfig) -> str:
    return f"hello {config.person_name}"


# end
