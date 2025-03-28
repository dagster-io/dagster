import dagster as dg

from .asset import defs_obj_outer  # noqa
from .inner.asset import defs_obj_inner  # noqa

defs = dg.Definitions(assets=[defs_obj_inner, defs_obj_outer])
