from dagster import load_defs

from dbt_example.components import inner as inner

defs = load_defs(defs_root=inner)
