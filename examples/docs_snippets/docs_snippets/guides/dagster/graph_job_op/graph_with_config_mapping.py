from dagster import config_mapping, graph, op


@op(config_schema=str)
def requires_config(context):
    return context.op_config


@config_mapping(config_schema=str)
def _config_mapping(outer):
    return {"requires_config": outer}


@graph(config=_config_mapping)
def nests():
    requires_config()
