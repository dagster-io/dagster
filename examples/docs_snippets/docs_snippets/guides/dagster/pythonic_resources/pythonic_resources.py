# isort: skip_file
# ruff: noqa: T201
# pylint: disable=unused-argument,reimported,unnecessary-ellipsis


def new_resource_testing() -> None:
    # start_new_resource_testing
    from dagster import ConfigurableResource

    class MyResource(ConfigurableResource):
        value: str

        def get_value(self) -> str:
            return self.value

    def test_my_resource():
        assert MyResource(value="foo").get_value() == "foo"

    # end_new_resource_testing


def new_resource_testing_with_context() -> None:
    # start_new_resource_testing_with_context
    from dagster import ConfigurableResource

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


def new_resources_assets_defs() -> None:
    # start_new_resources_assets_defs

    from dagster import asset, Definitions
    from dagster import Resource
    import requests

    from typing import Dict, Any

    @asset
    def data_from_url(data_url: Resource[str]) -> Dict[str, Any]:
        return requests.get(data_url).json()

    defs = Definitions(
        assets=[data_from_url],
        resources={"data_url": "https://dagster.io"},
    )

    # end_new_resources_assets_defs


def new_resources_ops_defs() -> None:
    # start_new_resources_ops_defs

    from dagster import op, Definitions, job, Resource
    import requests

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


def new_resources_configurable_defs() -> None:
    # start_new_resources_configurable_defs

    from dagster import asset, Definitions, ConfigurableResource
    import requests
    from requests import Response

    class MyConnectionResource(ConfigurableResource):
        username: str

        def request(self, endpoint: str) -> Response:
            return requests.get(
                f"https://my-api.com/{endpoint}",
                headers={"user-agent": "dagster"},
            )

    @asset
    def data_from_service(my_conn: MyConnectionResource) -> Dict[str, Any]:
        return my_conn.request("/fetch_data").json()

    defs = Definitions(
        assets=[data_from_service],
        resources={
            "my_conn": MyConnectionResource(username="my_user"),
        },
    )

    # end_new_resources_configurable_defs


def new_resources_configurable_defs_ops() -> None:
    # start_new_resources_configurable_defs_ops

    from dagster import Definitions, job, op, ConfigurableResource
    import requests
    from requests import Response

    class MyConnectionResource(ConfigurableResource):
        username: str

        def request(self, endpoint: str) -> Response:
            return requests.get(
                f"https://my-api.com/{endpoint}",
                headers={"user-agent": "dagster"},
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
            "my_conn": MyConnectionResource(username="my_user"),
        },
    )

    # end_new_resources_configurable_defs_ops


def new_resource_runtime() -> None:
    # start_new_resource_runtime
    from dagster import ConfigurableResource, Definitions, asset

    class DatabaseResource(ConfigurableResource):
        table: str

        def read(self):
            ...

    @asset
    def data_from_database(db_conn: DatabaseResource):
        return db_conn.read()

    defs = Definitions(
        assets=[data_from_database],
        resources={"db_conn": DatabaseResource.configure_at_launch()},
    )

    # end_new_resource_runtime

    # start_new_resource_runtime_launch
    from dagster import sensor, define_asset_job, RunRequest, RunConfig

    update_data_job = define_asset_job(name="update_data_job", selection=[data_from_database])

    @sensor(job=update_data_job)
    def table_update_sensor():
        tables = ...
        for table_name in tables:
            yield RunRequest(
                run_config=RunConfig(
                    resources={
                        "db_conn": DatabaseResource(table=table_name),
                    },
                ),
            )

    # end_new_resource_runtime_launch


def get_filestore_client(*args, **kwargs):
    pass


def new_resources_nesting() -> None:
    # start_new_resources_nesting
    from dagster import Definitions, ConfigurableResource

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
        assets=...,  # type: ignore
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
        assets=...,  # type: ignore
        resources={
            "credentials": credentials,
            "bucket": FileStoreBucket(
                credentials=credentials,
                region="us-east-1",
            ),
        },
    )

    # end_new_resource_dep_job_runtime


def new_resources_env_vars() -> None:
    # start_new_resources_env_vars

    from dagster import EnvVar, Definitions, ConfigurableResource

    class CredentialsResource(ConfigurableResource):
        username: str
        password: str

    defs = Definitions(
        assets=...,  # type: ignore
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
    def __init__(*args, **kwargs):
        pass

    def organization(self, name: str):
        return GitHubOrganization(name)


def raw_github_resource() -> None:
    # start_raw_github_resource

    from dagster import Definitions, asset, Resource

    # `Resource[GitHub]` is treated exactly like `GitHub` for type checking purposes,
    # and the runtime type of the github parameter is `GitHub`. The purpose of the
    # `Resource` wrapper is to let Dagster know that `github` is a resource and not an
    # upstream asset.

    @asset
    def public_github_repos(github: Resource[GitHub]):
        return github.organization("dagster-io").repositories()

    defs = Definitions(
        assets=[public_github_repos],
        resources={"github": GitHub(...)},
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


def raw_github_resource_dep() -> None:
    # start_raw_github_resource_dep

    from dagster import ConfigurableResource, ResourceDependency, Definitions

    class DBResource(ConfigurableResource):
        engine: ResourceDependency[Engine]

        def query(self, query: str):
            with self.engine.connect() as conn:
                return conn.execute(query)

    engine = create_engine(...)
    defs = Definitions(
        assets=...,  # type: ignore
        resources={"db": DBResource(engine=engine)},
    )

    # end_raw_github_resource_dep


def resource_adapter() -> None:
    # start_resource_adapter

    from dagster import (
        resource,
        Definitions,
        ResourceDefinition,
        asset,
        ConfigurableLegacyResourceAdapter,
    )

    # Old code, interface cannot be changed for back-compat purposes
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
    class WriterResource(ConfigurableLegacyResourceAdapter):
        prefix: str

        @property
        def wrapped_resource(self) -> ResourceDefinition:
            return writer_resource

    @asset
    def my_asset(writer: Writer):
        writer.output("hello, world!")

    defs = Definitions(assets=[my_asset], resources={"writer": WriterResource(prefix="greeting: ")})

    # end_resource_adapter


def io_adapter() -> None:
    # start_io_adapter

    from dagster import (
        Definitions,
        IOManagerDefinition,
        io_manager,
        IOManager,
        InputContext,
        ConfigurableLegacyIOManagerAdapter,
        OutputContext,
    )
    import os

    # Old code, interface cannot be changed for back-compat purposes
    class OldFileIOManager(IOManager):
        def __init__(self, base_path: str):
            self.base_path = base_path

        def handle_output(self, context: OutputContext, obj):
            with open(os.path.join(self.base_path, context.step_key, context.name), "w") as fd:
                fd.write(obj)

        def load_input(self, context: InputContext):
            with open(
                os.path.join(
                    self.base_path,
                    context.upstream_output.step_key,  # type: ignore
                    context.upstream_output.name,  # type: ignore
                ),
                "r",
            ) as fd:
                return fd.read()

    @io_manager(config_schema={"base_path": str})
    def old_file_io_manager(context):
        base_path = context.resource_config["base_path"]
        return OldFileIOManager(base_path)

    # New adapter layer
    class MyIOManager(ConfigurableLegacyIOManagerAdapter):
        base_path: str

        @property
        def wrapped_io_manager(self) -> IOManagerDefinition:
            return old_file_io_manager

    defs = Definitions(
        assets=...,  # type: ignore
        resources={
            "io_manager": MyIOManager(base_path="/tmp/"),
        },
    )

    # end_io_adapter


def impl_details_resolve() -> None:
    # start_impl_details_resolve

    from dagster import ConfigurableResource

    class CredentialsResource(ConfigurableResource):
        username: str
        password: str

    class FileStoreBucket(ConfigurableResource):
        credentials: CredentialsResource
        region: str

        def write(self, data: str):
            # In this context, `self.credentials` is ensured to
            # be a CredentialsResource with valid values for
            # `username` and `password`

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


def write_csv(path: str, obj: Any):
    pass


def read_csv(path: str):
    pass


def new_io_manager() -> None:
    # start_new_io_manager

    from dagster import (
        Definitions,
        AssetKey,
        OutputContext,
        InputContext,
        ConfigurableIOManager,
    )

    class MyIOManager(ConfigurableIOManager):
        root_path: str

        def _get_path(self, asset_key: AssetKey) -> str:
            return self.root_path + "/".join(asset_key.path)

        def handle_output(self, context: OutputContext, obj):
            write_csv(self._get_path(context.asset_key), obj)

        def load_input(self, context: InputContext):
            return read_csv(self._get_path(context.asset_key))

    defs = Definitions(
        assets=...,  # type: ignore
        resources={"io_manager": MyIOManager(root_path="/tmp/")},
    )

    # end_new_io_manager
