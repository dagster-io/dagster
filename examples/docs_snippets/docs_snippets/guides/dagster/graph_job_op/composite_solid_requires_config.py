from dagster import composite_solid, solid


@solid(config_schema=str)
def requires_config(context):
    return context.solid_config


@composite_solid
def nests_solids():
    requires_config()
