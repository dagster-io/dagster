from dagster import asset, job, op, repository, resource


class MyDatabaseConnection:
    def __init__(self, url):
        self.url = url


# start_marker
from dagster._config.structured_config import Config


class MyOpConfig(Config):
    person_name: str


@op
def op_using_config(config: MyOpConfig):
    return f"hello {config.person_name}"


class MyAssetConfig(Config):
    person_name: str


@asset
def asset_using_config(config: MyAssetConfig):
    return f"hello {config.person_name}"


# end_marker

# start_resource_marker
from dagster._config.structured_config import Resource


class ResourceUsingConfig(Resource):
    url: str

    def db_connection(self):
        return MyDatabaseConnection(self.url)


# end_resource_marker


@job
def job_using_config():
    op_using_config()


@repository
def repo():
    return [job_using_config]
