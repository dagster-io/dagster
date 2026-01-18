import dagster as dg

from .defs1 import defs1  # noqa: TID252
from .defs2 import defs2  # noqa: TID252

defs = dg.Definitions.merge(
    defs1,
    defs2,
)
