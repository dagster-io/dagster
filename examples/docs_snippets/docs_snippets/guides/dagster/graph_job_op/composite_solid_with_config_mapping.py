from dagster import composite_solid, solid


@solid(config_schema=str)
def requires_config(context):
    return context.solid_config


def _config_mapping(outer):
    return {"solids": {"requires_config": outer}}


@composite_solid(config_fn=_config_mapping, config_schema=str)
def nests():
    requires_config()
