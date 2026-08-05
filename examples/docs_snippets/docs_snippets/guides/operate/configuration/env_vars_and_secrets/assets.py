# pyright: reportMissingImports=false

# start
import dagster as dg

from .resources import SomeResource  # ty: ignore[unresolved-import]


@dg.asset
def my_asset(some_resource: SomeResource) -> None: ...


# end
