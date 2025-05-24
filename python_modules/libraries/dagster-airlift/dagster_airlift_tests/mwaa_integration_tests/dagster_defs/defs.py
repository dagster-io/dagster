from dagster import load_defs

from dagster_airlift_tests.mwaa_integration_tests.dagster_defs import inner as inner

defs_obj = load_defs(defs_root=inner)
