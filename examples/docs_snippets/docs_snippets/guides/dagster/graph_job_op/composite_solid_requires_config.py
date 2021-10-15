from dagster import solid, composite_solid


@solid(config_schema=str)
def requires_config(context):
    return context.solid_config


@composite_solid
def nests_solids():
    requires_config()