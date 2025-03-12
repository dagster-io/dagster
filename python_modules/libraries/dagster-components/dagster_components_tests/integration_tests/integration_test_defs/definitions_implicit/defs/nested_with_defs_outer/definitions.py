import dagster as dg

from .inner.nested_3 import nested_3  # noqa

defs = dg.Definitions(assets=[nested_3])
