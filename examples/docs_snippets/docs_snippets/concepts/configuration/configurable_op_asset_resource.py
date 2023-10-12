from dagster import asset, job, op, repository, resource, OpExecutionContext, AssetExecutionContext, InitResourceContext


class MyDatabaseConnection:
    def __init__(self, url):
        self.url = url


# start_marker
@op(config_schema={"person_name": str})
def op_using_config(context: OpExecutionContext):
    return f'hello {context.op_config["person_name"]}'


@asset(config_schema={"person_name": str})
def asset_using_config(context: AssetExecutionContext):
    # Note how asset config is also accessed with context.op_config
    return f'hello {context.op_config["person_name"]}'


@resource(config_schema={"url": str})
def resource_using_config(context: InitResourceContext):
    return MyDatabaseConnection(context.resource_config["url"])


# end_marker


@job
def job_using_config():
    op_using_config()


@repository
def repo():
    return [job_using_config]
