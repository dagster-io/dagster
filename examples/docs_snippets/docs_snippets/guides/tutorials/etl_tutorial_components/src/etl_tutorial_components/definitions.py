import etl_tutorial_components.defs
from dagster.components import definitions, load_defs


@definitions
def defs():
    return load_defs(defs_root=etl_tutorial_components.defs)
