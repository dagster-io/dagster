from dagster.components import definitions, load_defs


@definitions
def defs():
    import dagster_test.defs

    return load_defs(defs_root=dagster_test.defs)
