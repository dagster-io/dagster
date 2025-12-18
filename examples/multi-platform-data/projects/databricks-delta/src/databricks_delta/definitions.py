import dagster as dg

import databricks_delta.defs as defs_module

defs = dg.components.load_defs(defs_module)
