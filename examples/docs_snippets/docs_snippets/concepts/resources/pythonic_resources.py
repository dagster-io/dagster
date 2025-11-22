# ruff: isort: skip_file
# ruff: noqa: T201
import dagster as dg


def new_resource_testing() -> None:
    # start_new_resource_testing
    import dagster as dg

    class MyResource(dg.ConfigurableResource):
        value: str

        def get_value(self) -> str:
            return self.value

    # end_new_resource_testing

    # start_test_my_resource
    def test_my_resource():
        assert MyResource(value="foo").get_value() == "foo"

    # end_test_my_resource

    test_my_resource()


def new_resource_testing_with_nesting() -> None:
    # start_new_resource_testing_with_nesting
    import dagster as dg

    class StringHolderResource(dg.ConfigurableResource):
        value: str

    class MyResourceRequiresAnother(dg.ConfigurableResource):
        foo: StringHolderResource
        bar: str

    # end_new_resource_testing_with_nesting

    # start_test_my_resource_with_nesting
    def test_my_resource_with_nesting():
        string_holder = StringHolderResource(value="foo")
        resource = MyResourceRequiresAnother(foo=string_holder, bar="bar")
        assert resource.foo.value == "foo"
        assert resource.bar == "bar"

    # end_test_my_resource_with_nesting

    test_my_resource_with_nesting()


from typing import Any


def new_resources_assets_defs() -> "dg.Definitions":
    # start_new_resources_assets_defs
    import requests
    import dagster as dg

    from typing import Any

    @dg.asset
    def data_from_url(data_url: dg.ResourceParam[str]) -> dict[str, Any]:
        return requests.get(data_url).json()

    @dg.definitions
    def resources():
        return dg.Definitions(
            resources={"data_url": "https://dagster.io"},
        )

    # end_new_resources_assets_defs

    return dg.Definitions(
        assets=[data_from_url],
        resources={"data_url": "https://dagster.io"},
    )


def new_resources_ops_defs() -> "dg.Definitions":
    # start_new_resources_ops_defs
    import dagster as dg
    import requests

    @dg.op
    def print_data_from_resource(data_url: dg.ResourceParam[str]):
        print(requests.get(data_url).json())

    @dg.job
    def print_data_from_url_job():
        print_data_from_resource()

    @dg.definitions
    def resources():
        return dg.Definitions(
            resources={"data_url": "https://dagster.io"},
        )

    # end_new_resources_ops_defs


def new_resources_configurable_defs() -> "dg.Definitions":
    # start_new_resources_configurable_defs
    import dagster as dg
    import requests

    from requests import Response

    class MyConnectionResource(dg.ConfigurableResource):
        username: str

        def request(self, endpoint: str) -> Response:
            return requests.get(
                f"https://my-api.com/{endpoint}",
                headers={"user-agent": "dagster"},
            )

    @dg.asset
    def data_from_service(my_conn: MyConnectionResource) -> dict[str, Any]:
        return my_conn.request("/fetch_data").json()

    # end_new_resources_configurable_defs

    # start_new_resources_configurable_defs_defs
    @dg.definitions
    def resources():
        return dg.Definitions(
            resources={
                "my_conn": MyConnectionResource(username="my_user"),
            },
        )

    # end_new_resources_configurable_defs_defs

    return dg.Definitions(
        assets=[data_from_service],
        resources={
            "my_conn": MyConnectionResource(username="my_user"),
        },
    )


def new_resources_configurable_defs_ops() -> "dg.Definitions":
    # start_new_resources_configurable_defs_ops
    import dagster as dg
    import requests

    from requests import Response

    class MyConnectionResource(dg.ConfigurableResource):
        username: str

        def request(self, endpoint: str) -> Response:
            return requests.get(
                f"https://my-api.com/{endpoint}",
                headers={"user-agent": "dagster"},
            )

    @dg.op
    def update_service(my_conn: MyConnectionResource):
        my_conn.request("/update")

    @dg.job
    def update_service_job():
        update_service()

    # end_new_resources_configurable_defs_ops

    # start_new_resources_configurable_defs_ops_defs
    @dg.definitions
    def resources():
        return dg.Definitions(
            resources={
                "my_conn": MyConnectionResource(username="my_user"),
            },
        )

    # end_new_resources_configurable_defs_ops_defs


def new_resource_runtime() -> "dg.Definitions":
    # start_new_resource_runtime
    import dagster as dg

    class DatabaseResource(dg.ConfigurableResource):
        table: str

        def read(self): ...

    @dg.asset
    def data_from_database(db_conn: DatabaseResource):
        return db_conn.read()

    # end_new_resource_runtime

    # start_new_resource_runtime_defs
    @dg.definitions
    def resources():
        return dg.Definitions(
            resources={"db_conn": DatabaseResource.configure_at_launch()},
        )

    # end_new_resource_runtime_defs

    # start_new_resource_runtime_launch
    import dagster as dg

    update_data_job = dg.define_asset_job(
        name="update_data_job", selection=[data_from_database]
    )

    @dg.sensor(job=update_data_job)
    def table_update_sensor():
        tables = ...
        for table_name in tables:
            yield dg.RunRequest(
                run_config=dg.RunConfig(
                    resources={
                        "db_conn": DatabaseResource(table=table_name),
                    },
                ),
            )

    # end_new_resource_runtime_launch

    @dg.definitions
    def resources():
        return dg.Definitions(
            resources={"db_conn": DatabaseResource.configure_at_launch()},
        )

    return dg.Definitions(
        assets=[data_from_database],
        jobs=[update_data_job],
        resources={"db_conn": DatabaseResource.configure_at_launch()},
        sensors=[table_update_sensor],
    )


def get_filestore_client(*args, **kwargs):
    pass


def new_resources_nesting() -> dg.Definitions:
    import dagster as dg

    @dg.asset
    def my_asset():
        pass

    # start_new_resources_nesting
    import dagster as dg

    class CredentialsResource(dg.ConfigurableResource):
        username: str
        password: str

    class FileStoreBucket(dg.ConfigurableResource):
        credentials: dg.ResourceDependency[CredentialsResource]
        region: str

        def write(self, data: str):
            # We can access the credentials dg.resource via `self.credentials`,
            # which will be an initialized instance of `CredentialsResource`
            get_filestore_client(
                username=self.credentials.username,
                password=self.credentials.password,
                region=self.region,
            ).write(data)

    @dg.definitions
    def resources():
        return dg.Definitions(
            resources={
                "bucket": FileStoreBucket(
                    credentials=CredentialsResource(
                        username="my_user", password="my_password"
                    ),
                    region="us-east-1",
                ),
            },
        )

    # end_new_resources_nesting

    # start_new_resource_dep_job_runtime
    credentials = CredentialsResource.configure_at_launch()

    @dg.definitions
    def resources():
        return dg.Definitions(
            resources={
                "credentials": credentials,
                "bucket": FileStoreBucket(
                    credentials=credentials,
                    region="us-east-1",
                ),
            },
        )

    # end_new_resource_dep_job_runtime

    return dg.Definitions(
        assets=[my_asset],
        resources={
            "credentials": credentials,
            "bucket": FileStoreBucket(
                credentials=credentials,
                region="us-east-1",
            ),
        },
    )


def new_resources_env_vars() -> None:
    # start_new_resources_env_vars
    import dagster as dg

    class CredentialsResource(dg.ConfigurableResource):
        username: str
        password: str

    @dg.definitions
    def resources():
        return dg.Definitions(
            resources={
                "credentials": CredentialsResource(
                    username=dg.EnvVar("MY_USERNAME"),
                    password=dg.EnvVar("MY_PASSWORD"),
                )
            },
        )

    # end_new_resources_env_vars

    return dg.Definitions(
        resources={
            "credentials": CredentialsResource(
                username=dg.EnvVar("MY_USERNAME"),
                password=dg.EnvVar("MY_PASSWORD"),
            )
        },
    )


class GitHubOrganization:
    def __init__(self, name: str):
        self.name = name

    def repositories(self) -> Any:
        return ["dagster", "dagster-webserver", "dagster-graphql"]


class GitHub:
    def __init__(*args, **kwargs):
        pass

    def organization(self, name: str) -> GitHubOrganization:
        return GitHubOrganization(name)


def raw_github_resource() -> None:
    # start_raw_github_resource
    import dagster as dg

    # `ResourceParam[GitHub]` is treated exactly like `GitHub` for type checking purposes,
    # and the runtime type of the github parameter is `GitHub`. The purpose of the
    # `ResourceParam` wrapper is to let Dagster know that `github` is a dg.resource and not an
    # upstream dg.asset.

    @dg.asset
    def public_github_repos(github: dg.ResourceParam[GitHub]):
        return github.organization("dagster-io").repositories()

    # end_raw_github_resource

    # start_raw_github_resource_defs
    @dg.definitions
    def resources():
        return dg.Definitions(
            resources={"github": GitHub(...)},
        )

    # end_raw_github_resource_defs


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
    import dagster as dg

    class DBResource(dg.ConfigurableResource):
        engine: dg.ResourceDependency[Engine]

        def query(self, query: str):
            with self.engine.connect() as conn:
                return conn.execute(query)

    engine = create_engine(...)

    @dg.definitions
    def resources():
        return dg.Definitions(
            resources={"db": DBResource(engine=engine)},
        )

    # end_raw_github_resource_dep


def resource_adapter() -> None:
    # start_resource_adapter
    import dagster as dg

    # Old code, interface cannot be changed for back-compat purposes
    class Writer:
        def __init__(self, prefix: str):
            self._prefix = prefix

        def output(self, text: str) -> None:
            print(self._prefix + text)

    @dg.resource(config_schema={"prefix": str})
    def writer_resource(context):
        prefix = context.resource_config["prefix"]
        return Writer(prefix)

    # New adapter layer
    class WriterResource(dg.ConfigurableLegacyResourceAdapter):
        prefix: str

        @property
        def wrapped_resource(self) -> dg.ResourceDefinition:
            return writer_resource

    @dg.asset
    def my_asset(writer: Writer):
        writer.output("hello, world!")

    @dg.definitions
    def resources():
        return dg.Definitions(resources={"writer": WriterResource(prefix="greeting: ")})

    # end_resource_adapter


def io_adapter() -> None:
    # start_io_adapter
    import dagster as dg

    import os

    # Old code, interface cannot be changed for back-compat purposes
    class OldFileIOManager(dg.IOManager):
        def __init__(self, base_path: str):
            self.base_path = base_path

        def handle_output(self, context: dg.OutputContext, obj):
            with open(
                os.path.join(self.base_path, context.step_key, context.name), "w"
            ) as fd:
                fd.write(obj)

        def load_input(self, context: dg.InputContext):
            with open(
                os.path.join(
                    self.base_path,
                    context.upstream_output.step_key,  # type: ignore
                    context.upstream_output.name,  # type: ignore
                ),
            ) as fd:
                return fd.read()

    @dg.io_manager(config_schema={"base_path": str})
    def old_file_io_manager(context):
        base_path = context.resource_config["base_path"]
        return OldFileIOManager(base_path)

    # New adapter layer
    class MyIOManager(dg.ConfigurableLegacyIOManagerAdapter):
        base_path: str

        @property
        def wrapped_io_manager(self) -> dg.IOManagerDefinition:
            return old_file_io_manager

    @dg.definitions
    def resources():
        return dg.Definitions(
            resources={
                "dg.io_manager": MyIOManager(base_path="/tmp/"),
            },
        )

    # end_io_adapter


def impl_details_resolve() -> None:
    # start_impl_details_resolve
    import dagster as dg

    class CredentialsResource(dg.ConfigurableResource):
        username: str
        password: str

    class FileStoreBucket(dg.ConfigurableResource):
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
    import dagster as dg

    class MyIOManager(dg.ConfigurableIOManager):
        root_path: str

        def _get_path(self, asset_key: dg.AssetKey) -> str:
            return self.root_path + "/".join(asset_key.path)

        def handle_output(self, context: dg.OutputContext, obj):
            write_csv(self._get_path(context.asset_key), obj)

        def load_input(self, context: dg.InputContext):
            return read_csv(self._get_path(context.asset_key))

    @dg.definitions
    def resources():
        return dg.Definitions(
            resources={"dg.io_manager": MyIOManager(root_path="/tmp/")},
        )

    # end_new_io_manager


def raw_github_resource_factory() -> None:
    # start_raw_github_resource_factory
    import dagster as dg

    class GitHubResource(dg.ConfigurableResourceFactory[GitHub]):
        access_token: str

        def create_resource(self, _context) -> GitHub:
            return GitHub(self.access_token)

    @dg.asset
    def public_github_repos(github: dg.Resource[GitHub]):
        return github.organization("dagster-io").repositories()

    @dg.definitions
    def resources():
        return dg.Definitions(
            resources={
                "github": GitHubResource(access_token=dg.EnvVar("GITHUB_ACCESS_TOKEN"))
            },
        )

    # end_raw_github_resource_factory


def new_resource_testing_with_context():
    # start_new_resource_testing_with_context
    import dagster as dg

    from typing import Optional

    class MyContextResource(dg.ConfigurableResource[GitHub]):
        base_path: Optional[str] = None

        def effective_base_path(self) -> str:
            if self.base_path:
                return self.base_path
            instance = self.get_resource_context().instance
            assert instance
            return instance.storage_directory()

    # end_new_resource_testing_with_context

    # start_test_my_context_resource
    def test_my_context_resource():
        with dg.DagsterInstance.ephemeral() as instance:
            context = dg.build_init_resource_context(instance=instance)
            assert (
                MyContextResource(base_path=None)
                .with_resource_context(context)
                .effective_base_path()
                == instance.storage_directory()
            )

    # end_test_my_context_resource


def with_state_example() -> None:
    # start_with_state_example
    import dagster as dg
    import requests

    from pydantic import PrivateAttr

    class MyClientResource(dg.ConfigurableResource):
        username: str
        password: str

        _api_token: str = PrivateAttr()

        def setup_for_execution(self, context: dg.InitResourceContext) -> None:
            # Fetch and set up an API token based on the username and password
            self._api_token = requests.get(
                "https://my-api.com/token", auth=(self.username, self.password)
            ).text

        def get_all_users(self):
            return requests.get(
                "https://my-api.com/users",
                headers={"Authorization": self._api_token},
            )

    @dg.asset
    def my_asset(client: MyClientResource):
        return client.get_all_users()

    # end_with_state_example


def with_complex_state_example() -> None:
    # start_with_complex_state_example
    import dagster as dg

    from contextlib import contextmanager
    from pydantic import PrivateAttr

    class DBConnection:
        ...

        def query(self, body: str): ...

    @contextmanager  # type: ignore
    def get_database_connection(username: str, password: str): ...

    class MyClientResource(dg.ConfigurableResource):
        username: str
        password: str

        _db_connection: DBConnection = PrivateAttr()

        @contextmanager
        def yield_for_execution(self, context: dg.InitResourceContext):
            # keep connection open for the duration of the execution
            with get_database_connection(self.username, self.password) as conn:
                # set up the connection attribute so it can be used in the execution
                self._db_connection = conn

                # yield, allowing execution to occur
                yield self

        def query(self, body: str):
            return self._db_connection.query(body)

    @dg.asset
    def my_asset(client: MyClientResource):
        client.query("SELECT * FROM my_table")

    # end_with_complex_state_example


def new_resource_testing_with_state_ops() -> None:
    # start_new_resource_testing_with_state_ops
    import dagster as dg

    from unittest import mock

    class MyClient:
        ...

        def query(self, body: str): ...

    class MyClientResource(dg.ConfigurableResource):
        username: str
        password: str

        def get_client(self):
            return MyClient(self.username, self.password)

    @dg.op
    def my_op(client: MyClientResource):
        return client.get_client().query("SELECT * FROM my_table")

    def test_my_op():
        class FakeClient:
            def query(self, body: str):
                assert body == "SELECT * FROM my_table"
                return "my_result"

        mocked_client_resource = mock.Mock()
        mocked_client_resource.get_client.return_value = FakeClient()

        assert my_op(mocked_client_resource) == "my_result"

    # end_new_resource_testing_with_state_ops


def new_resource_on_sensor() -> None:
    # start_new_resource_on_sensor
    import dagster as dg

    import requests

    class UsersAPI(dg.ConfigurableResource):
        url: str

        def fetch_users(self) -> list[str]:
            return requests.get(self.url).json()

    @dg.job
    def process_user(): ...

    @dg.sensor(job=process_user)
    def process_new_users_sensor(
        context: dg.SensorEvaluationContext,
        users_api: UsersAPI,
    ):
        last_user = int(context.cursor) if context.cursor else 0
        users = users_api.fetch_users()

        num_users = len(users)
        for user_id in users[last_user:]:
            yield dg.RunRequest(
                run_key=user_id,
                tags={"user_id": user_id},
            )

        context.update_cursor(str(num_users))

    # end_new_resource_on_sensor

    # start_new_resource_on_sensor_defs
    @dg.definitions
    def resources():
        return dg.Definitions(
            resources={"users_api": UsersAPI(url="https://my-api.com/users")},
        )

    # end_new_resource_on_sensor_defs

    # start_test_resource_on_sensor

    import dagster as dg

    def test_process_new_users_sensor():
        class FakeUsersAPI:
            def fetch_users(self) -> list[str]:
                return ["1", "2", "3"]

        with dg.build_sensor_context() as context:
            run_requests = process_new_users_sensor(context, users_api=FakeUsersAPI())
            assert len(run_requests) == 3

        # end_test_resource_on_sensor


def new_resource_on_schedule() -> None:
    # start_new_resource_on_schedule
    import dagster as dg

    from datetime import datetime

    class DateFormatter(dg.ConfigurableResource):
        format: str

        def strftime(self, dt: datetime) -> str:
            return dt.strftime(self.format)

    @dg.job
    def process_data(): ...

    @dg.schedule(job=process_data, cron_schedule="* * * * *")
    def process_data_schedule(
        context: dg.ScheduleEvaluationContext,
        date_formatter: DateFormatter,
    ):
        formatted_date = date_formatter.strftime(context.scheduled_execution_time)

        return dg.RunRequest(
            run_key=None,
            tags={"date": formatted_date},
        )

    # end_new_resource_on_schedule

    # start_new_resource_on_schedule_defs
    @dg.definitions
    def resources():
        return dg.Definitions(
            resources={"date_formatter": DateFormatter(format="%Y-%m-%d")},
        )

    # end_new_resource_on_schedule_defs

    # start_test_resource_on_schedule
    import dagster as dg

    def test_process_data_schedule():
        with dg.build_schedule_context(
            scheduled_execution_time=datetime.datetime(2020, 1, 1)
        ) as context:
            run_request = process_data_schedule(
                context, date_formatter=DateFormatter(format="%Y-%m-%d")
            )
            assert (
                run_request.run_config["ops"]["fetch_data"]["config"]["date"]
                == "2020-01-01"
            )

    # end_test_resource_on_schedule
