import dagster as dg


class MyDatabaseConnection:
    def __init__(self, url):
        self.url = url


# start_marker
@dg.op(config_schema={"person_name": str})
def op_using_config(context: dg.OpExecutionContext):
    return f"hello {context.op_config['person_name']}"


@dg.asset(config_schema={"person_name": str})
def asset_using_config(context: dg.AssetExecutionContext):
    # Note how dg.asset config is accessed with context.op_execution_context.op_config
    return f"hello {context.op_execution_context.op_config['person_name']}"


@dg.resource(config_schema={"url": str})
def resource_using_config(context: dg.InitResourceContext):
    return MyDatabaseConnection(context.resource_config["url"])


# end_marker


@dg.job
def job_using_config():
    op_using_config()


@dg.repository
def repo():
    return [job_using_config]
