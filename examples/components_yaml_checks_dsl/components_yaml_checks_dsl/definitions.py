from dagster.components import definitions, load_defs

import components_yaml_checks_dsl.defs


@definitions
def defs():
    return load_defs(defs_root=components_yaml_checks_dsl.defs)
