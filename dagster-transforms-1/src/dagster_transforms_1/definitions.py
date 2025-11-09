import dagster_transforms_1.defs

from dagster.components import definitions, load_defs


@definitions
def defs():
    return load_defs(defs_root=dagster_transforms_1.defs)
