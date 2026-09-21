# pyright: reportMissingImports=false

# start
import dagster as dg

from .resources import MyOpConfig  # ty: ignore[unresolved-import]


@dg.op
def print_greeting(config: MyOpConfig):
    print(f"hello {config.person_name}")  # noqa: T201


# end
