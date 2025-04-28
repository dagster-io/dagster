from dagster.components import definitions, load_defs

import asset_check_suite_example.defs


@definitions
def defs():
    return load_defs(defs_root=asset_check_suite_example.defs)
