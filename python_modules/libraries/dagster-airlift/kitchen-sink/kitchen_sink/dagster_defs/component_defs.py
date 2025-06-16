from dagster import load_defs

import kitchen_sink.dagster_defs.inner_component_defs as inner_component_defs

defs = load_defs(defs_root=inner_component_defs)
