import dagster as dg

import snowflake_medallion.defs as defs_module

defs = dg.components.load_defs(defs_module)
