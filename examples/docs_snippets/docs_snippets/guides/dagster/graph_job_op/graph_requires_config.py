from dagster import solid, graph


@solid(config_schema=str)
def requires_config(context):
    return context.solid_config


@graph
def nests_solids():
    requires_config()