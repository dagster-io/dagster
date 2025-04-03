from jaffle_platform import defs as defs_module
from dagster.components import load_defs, definitions


@definitions
def jaffle_platform_defs():
    return load_defs(defs_root=defs_module)
