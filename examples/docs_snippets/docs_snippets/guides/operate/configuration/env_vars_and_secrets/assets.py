# pyright: reportMissingImports=false

# start
import dagster as dg

from .resources import SomeResource


@dg.asset
def my_asset(some_resource: SomeResource) -> None: ...


# end
