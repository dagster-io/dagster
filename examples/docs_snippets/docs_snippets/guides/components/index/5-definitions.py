from jaffle_platform import defs as defs_module

from dagster.components import definitions, load_defs


@definitions
def jaffle_platform_defs():
    return load_defs(defs_root=defs_module)
