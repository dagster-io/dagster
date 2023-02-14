# isort: skip_file
# pylint: disable=unused-argument,reimported,unnecessary-ellipsis
from dagster import ResourceDefinition, graph, job, Definitions, resource
import requests
from requests import Response
from typing import Generic, TypeVar


# start_new_resource_testing
from dagster._config.structured_config import ConfigurableResource, ConfigurableResourceAdapter

V = TypeVar("V")


class ResourceDependency(Generic[V]):
    def __get__(self, obj: "Resource", __owner: Any) -> V:
        return getattr(obj, self._name)


class MyResource(ConfigurableResource):
    value: str

    def get_value(self) -> str:
        return self.value


def test_my_resource():
    assert MyResource(value="foo").get_value() == "foo"


# end_new_resource_testing

# start_new_resource_testing_with_context
from dagster._config.structured_config import ConfigurableResource


class StringHolderResource(ConfigurableResource):
    value: str


class MyResourceRequiresAnother(ConfigurableResource):
    foo: StringHolderResource
    bar: str


def test_my_resource_with_context():
    string_holder = StringHolderResource(value="foo")
    resource = MyResourceRequiresAnother(foo=string_holder, bar="bar")
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


class GitHubOrganization:
    def __init__(self, name: str):
        self.name = name

    def repositories(self):
        return ["dagster", "dagit", "dagster-graphql"]


class GitHub:
    def organization(self, name: str):
        return GitHubOrganization(name)


# start_raw_github_resource


@asset
def public_github_repos(github: Resource[GitHub]):
    return github.organization("dagster-io").repositories()


defs = Definitions(
    assets=[public_github_repos],
    resources={"github": GitHub()},
)

# end_raw_github_resource

from contextlib import AbstractContextManager


class Connection(AbstractContextManager):
    def execute(self, query: str):
        return None

    def __enter__(self) -> "Connection":
        return self

    def __exit__(self, *args):
        return False


class Engine:
    def connect(self) -> Connection:
        return Connection()


def create_engine(*args, **kwargs):
    return Engine()


# start_raw_github_resource_dep


class DBResource(ConfigurableResource):
    engine: ResourceDependency[Engine]

    def query(self, query: str):
        with self.engine.connect() as conn:
            return conn.execute(query)


engine = create_engine(...)
defs = Definitions(
    assets=...,
    resources={"db": DBResource(engine=engine)},
)


# end_raw_github_resource_dep

# start_resource_adapter


# Old code, cannot be changed for back-compat purposes
class Writer:
    def __init__(self, prefix: str):
        self._prefix = prefix

    def output(self, text: str) -> None:
        print(self._prefix + text)


@resource(config_schema={"prefix": str})
def writer_resource(context):
    prefix = context.resource_config["prefix"]
    return Writer(prefix)


# New adapter layer
class WriterResource(ConfigurableResourceAdapter):
    prefix: str

    @property
    def wrapped_resource(self) -> ResourceDefinition:
        return writer_resource


@asset
def my_asset(writer: Writer):
    writer.output("hello, world!")


defs = Definitions(assets=[my_asset], resources={"writer": WriterResource(prefix="greeting: ")})

# end_resource_adapter

# start_impl_details_resolve


class CredentialsResource(ConfigurableResource):
    username: str
    password: str


class FileStoreBucket(ConfigurableResource):
    credentials: CredentialsResource
    region: str

    def write(self, data: str):
        # In this context, `self.credentials` is ensured to
        # be a CredentialsResource

        get_filestore_client(
            username=self.credentials.username,
            password=self.credentials.password,
            region=self.region,
        ).write(data)


# unconfigured_credentials_resource is typed as PartialResource[CredentialsResource]
unconfigured_credentials_resource = CredentialsResource.configure_at_launch()

# FileStoreBucket constructor accepts either a CredentialsResource or a
# PartialResource[CredentialsResource] for the `credentials` argument
bucket = FileStoreBucket(
    credentials=unconfigured_credentials_resource,
    region="us-east-1",
)

# end_impl_details_resolve

from dagster._config.structured_config import ConfigurableIOManager
from dagster import InputContext, OutputContext, AssetKey
from typing import Union


def write_csv(path: str, obj: Any):
    pass


def read_csv(path: str):
    pass


# start_new_io_manager


class MyIOManager(ConfigurableIOManager):
    root_path: str

    def _get_path(self, asset_key: AssetKey) -> str:
        return self.root_path + "/".join(asset_key.path)

    def handle_output(self, context: OutputContext, obj):
        write_csv(self._get_path(context.asset_key), obj)

    def load_input(self, context: InputContext):
        return read_csv(self._get_path(context.asset_key))

defs = Definitions(
    assets=...,
    resources={
        "io_manager": MyIOManager(root_path="/tmp/")
    },
)

# end_new_io_manager
