# isort: skip_file
# pylint: disable=unused-argument,reimported,unnecessary-ellipsis
from dagster import ResourceDefinition, graph, job, Definitions
import requests
from requests import Response


# start_new_resource_testing
from dagster._config.structured_config import ConfigurableResource


class MyResource(ConfigurableResource):
    def get_value(self) -> str:
        return "foo"


def test_my_resource():
    assert MyResource().get_value() == "foo"


# end_new_resource_testing

# start_new_resource_testing_with_context
from dagster._config.structured_config import ConfigurableResource


class StringHolderResource(ConfigurableResource):
    value: str


class MyResourceRequiresAnother(ConfigurableResource):
    foo: StringHolderResource
    bar: str


def test_my_resource_with_context():
    resource = MyResourceRequiresAnother(foo=StringHolderResource("foo"), bar="bar")
    assert resource.foo.value == "foo"
    assert resource.bar == "bar"


# end_new_resource_testing_with_context


from typing import Dict, Any

# start_new_resources_assets_defs

from dagster import asset, Definitions
from dagster._core.definitions.resource_annotation import Resource


@asset
def data_from_url(data_url: Resource[str]) -> Dict[str, Any]:
    return requests.get(data_url).json()


defs = Definitions(
    assets=[data_from_url],
    resources={"data_url": "https://dagster.io"},
)


# end_new_resources_assets_defs


# start_new_resources_ops_defs

from dagster import op, Definitions, job
from dagster._core.definitions.resource_annotation import Resource


@op
def print_data_from_resource(data_url: Resource[str]):
    print(requests.get(data_url).json())


@job
def print_data_from_url_job():
    print_data_from_resource()


defs = Definitions(
    jobs=[print_data_from_url_job],
    resources={"data_url": "https://dagster.io"},
)


# end_new_resources_ops_defs

# start_new_resources_configurable_defs


from dagster import asset, Definitions
from dagster._config.structured_config import ConfigurableResource


class MyConnectionResource(ConfigurableResource):
    username: str
    password: str

    def request(self, endpoint: str) -> Response:
        return requests.get(
            f"https://my-api.com/{endpoint}",
            auth=(self.username, self.password),
        )


# Since MyConnectionResource extends ConfigurableResource, we don't
# need to wrap it in a Resource[] annotation.
@asset
def data_from_service(my_conn: MyConnectionResource) -> Dict[str, Any]:
    return my_conn.request("/fetch_data").json()


defs = Definitions(
    assets=[data_from_service],
    resources={
        "my_conn": MyConnectionResource(username="my_user", password="my_password"),
    },
)

# end_new_resources_configurable_defs


# start_new_resources_configurable_defs_ops


from dagster import Definitions, job, op
from dagster._config.structured_config import ConfigurableResource


class MyConnectionResource(ConfigurableResource):
    username: str
    password: str

    def request(self, endpoint: str) -> Response:
        return requests.get(
            f"https://my-api.com/{endpoint}",
            auth=(self.username, self.password),
        )


# Since MyConnectionResource extends ConfigurableResource, we don't
# need to wrap it in a Resource[] annotation.
@op
def update_service(my_conn: MyConnectionResource):
    my_conn.request("/update")


@job
def update_service_job():
    update_service()


defs = Definitions(
    jobs=[update_service_job],
    resources={
        "my_conn": MyConnectionResource(username="my_user", password="my_password"),
    },
)

# end_new_resources_configurable_defs_ops


# start_new_resource_runtime


class DatabaseResource(ConfigurableResource):
    table: str

    def read(self):
        ...


@asset
def data_from_database(db_conn: DatabaseResource):
    return db_conn.read()


defs = Definitions(
    assets=...,
    resources={"db_conn": DatabaseResource.configure_at_launch()},
)

# end_new_resource_runtime


def get_filestore_client(*args, **kwargs):
    pass


# start_new_resources_nesting
from dagster import Definitions
from dagster._config.structured_config import ConfigurableResource


class CredentialsResource(ConfigurableResource):
    username: str
    password: str


class FileStoreBucket(ConfigurableResource):
    credentials: CredentialsResource
    region: str

    def write(self, data: str):
        get_filestore_client(
            username=self.credentials.username,
            password=self.credentials.password,
            region=self.region,
        ).write(data)


credentials = CredentialsResource(username="my_user", password="my_password")
defs = Definitions(
    assets=...,
    resources={
        "bucket": FileStoreBucket(
            credentials=credentials,
            region="us-east-1",
        ),
    },
)
# end_new_resources_nesting


# start_new_resource_dep_job_runtime
credentials = CredentialsResource.configure_at_launch()


defs = Definitions(
    assets=...,
    resources={
        "credentials": credentials,
        "bucket": FileStoreBucket(
            credentials=credentials,
            region="us-east-1",
        ),
    },
)

# end_new_resource_dep_job_runtime

# start_new_resources_env_vars

from dagster._config.field_utils import EnvVar
from dagster import Definitions
from dagster._config.structured_config import ConfigurableResource


class CredentialsResource(ConfigurableResource):
    username: str
    password: str


defs = Definitions(
    assets=...,
    resources={
        "credentials": CredentialsResource(
            username=EnvVar("MY_USERNAME"),
            password=EnvVar("MY_PASSWORD"),
        )
    },
)
# end_new_resources_env_vars
