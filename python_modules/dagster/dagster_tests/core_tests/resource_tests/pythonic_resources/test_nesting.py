import contextlib
import enum
import json
from abc import ABC, abstractmethod
from typing import Any, Callable, List

import pytest
from dagster import (
    ConfigurableResource,
    Definitions,
    Field,
    ResourceDependency,
    ResourceParam,
    asset,
    resource,
)
from dagster._check import CheckError
from dagster._config.pythonic_config import (
    ConfigurableIOManager,
    ConfigurableResourceFactory,
)
from dagster._core.execution.context.init import InitResourceContext
from dagster._core.storage.io_manager import IOManager


def test_nested_resources() -> None:
    out_txt = []

    class Writer(ConfigurableResource, ABC):
        @abstractmethod
        def output(self, text: str) -> None:
            pass

    class WriterResource(Writer):
        def output(self, text: str) -> None:
            out_txt.append(text)

    class PrefixedWriterResource(Writer):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    class JsonWriterResource(
        Writer,
    ):
        base_writer: Writer
        indent: int

        def output(self, obj: Any) -> None:
            self.base_writer.output(json.dumps(obj, indent=self.indent))

    @asset
    def hello_world_asset(writer: JsonWriterResource):
        writer.output({"hello": "world"})

    # Construct a resource that is needed by another resource
    writer_resource = WriterResource()
    json_writer_resource = JsonWriterResource(indent=2, base_writer=writer_resource)

    assert (
        Definitions(
            assets=[hello_world_asset],
            resources={
                "writer": json_writer_resource,
            },
        )
        .get_implicit_global_asset_job_def()
        .execute_in_process()
        .success
    )

    assert out_txt == ['{\n  "hello": "world"\n}']

    # Do it again, with a different nested resource
    out_txt.clear()
    prefixed_writer_resource = PrefixedWriterResource(prefix="greeting: ")
    prefixed_json_writer_resource = JsonWriterResource(
        indent=2, base_writer=prefixed_writer_resource
    )

    assert (
        Definitions(
            assets=[hello_world_asset],
            resources={
                "writer": prefixed_json_writer_resource,
            },
        )
        .get_implicit_global_asset_job_def()
        .execute_in_process()
        .success
    )

    assert out_txt == ['greeting: {\n  "hello": "world"\n}']


def test_nested_resources_multiuse() -> None:
    class AWSCredentialsResource(ConfigurableResource):
        username: str
        password: str

    class S3Resource(ConfigurableResource):
        aws_credentials: AWSCredentialsResource
        bucket_name: str

    class EC2Resource(ConfigurableResource):
        aws_credentials: AWSCredentialsResource

    completed = {}

    @asset
    def my_asset(s3: S3Resource, ec2: EC2Resource):
        assert s3.aws_credentials.username == "foo"
        assert s3.aws_credentials.password == "bar"
        assert s3.bucket_name == "my_bucket"

        assert ec2.aws_credentials.username == "foo"
        assert ec2.aws_credentials.password == "bar"

        completed["yes"] = True

    aws_credentials = AWSCredentialsResource(username="foo", password="bar")
    defs = Definitions(
        assets=[my_asset],
        resources={
            "s3": S3Resource(bucket_name="my_bucket", aws_credentials=aws_credentials),
            "ec2": EC2Resource(aws_credentials=aws_credentials),
        },
    )

    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
    assert completed["yes"]


def test_nested_resources_runtime_config() -> None:
    class AWSCredentialsResource(ConfigurableResource):
        username: str
        password: str

    class S3Resource(ConfigurableResource):
        aws_credentials: AWSCredentialsResource
        bucket_name: str

    class EC2Resource(ConfigurableResource):
        aws_credentials: AWSCredentialsResource

    completed = {}

    @asset
    def my_asset(s3: S3Resource, ec2: EC2Resource):
        assert s3.aws_credentials.username == "foo"
        assert s3.aws_credentials.password == "bar"
        assert s3.bucket_name == "my_bucket"

        assert ec2.aws_credentials.username == "foo"
        assert ec2.aws_credentials.password == "bar"

        completed["yes"] = True

    aws_credentials = AWSCredentialsResource.configure_at_launch()
    defs = Definitions(
        assets=[my_asset],
        resources={
            "aws_credentials": aws_credentials,
            "s3": S3Resource(bucket_name="my_bucket", aws_credentials=aws_credentials),
            "ec2": EC2Resource(aws_credentials=aws_credentials),
        },
    )

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process(
            {
                "resources": {
                    "aws_credentials": {
                        "config": {
                            "username": "foo",
                            "password": "bar",
                        }
                    }
                }
            }
        )
        .success
    )
    assert completed["yes"]


def test_nested_resources_runtime_config_complex() -> None:
    class CredentialsResource(ConfigurableResource):
        username: str
        password: str

    class DBConfigResource(ConfigurableResource):
        creds: CredentialsResource
        host: str
        database: str

    class DBResource(ConfigurableResource):
        config: DBConfigResource

    completed = {}

    @asset
    def my_asset(db: DBResource):
        assert db.config.creds.username == "foo"
        assert db.config.creds.password == "bar"
        assert db.config.host == "localhost"
        assert db.config.database == "my_db"
        completed["yes"] = True

    credentials = CredentialsResource.configure_at_launch()
    db_config = DBConfigResource.configure_at_launch(creds=credentials)
    db = DBResource(config=db_config)

    defs = Definitions(
        assets=[my_asset],
        resources={
            "credentials": credentials,
            "db_config": db_config,
            "db": db,
        },
    )

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process(
            {
                "resources": {
                    "credentials": {
                        "config": {
                            "username": "foo",
                            "password": "bar",
                        }
                    },
                    "db_config": {
                        "config": {
                            "host": "localhost",
                            "database": "my_db",
                        }
                    },
                }
            }
        )
        .success
    )
    assert completed["yes"]

    credentials = CredentialsResource.configure_at_launch()
    db_config = DBConfigResource(creds=credentials, host="localhost", database="my_db")
    db = DBResource(config=db_config)

    defs = Definitions(
        assets=[my_asset],
        resources={
            "credentials": credentials,
            "db": db,
        },
    )

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process(
            {
                "resources": {
                    "credentials": {
                        "config": {
                            "username": "foo",
                            "password": "bar",
                        }
                    },
                }
            }
        )
        .success
    )
    assert completed["yes"]


def test_nested_function_resource() -> None:
    out_txt = []

    @resource
    def writer_resource(context):
        def output(text: str) -> None:
            out_txt.append(text)

        return output

    class PostfixWriterResource(ConfigurableResourceFactory[Callable[[str], None]]):
        writer: ResourceDependency[Callable[[str], None]]
        postfix: str

        def create_resource(self, context) -> Callable[[str], None]:
            def output(text: str):
                self.writer(f"{text}{self.postfix}")

            return output

    @asset
    def my_asset(writer: ResourceParam[Callable[[str], None]]):
        writer("foo")
        writer("bar")

    defs = Definitions(
        assets=[my_asset],
        resources={
            "writer": PostfixWriterResource(writer=writer_resource, postfix="!"),
        },
    )

    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
    assert out_txt == ["foo!", "bar!"]


def test_nested_function_resource_configured() -> None:
    out_txt = []

    @resource(config_schema={"prefix": Field(str, default_value="")})
    def writer_resource(context):
        prefix = context.resource_config["prefix"]

        def output(text: str) -> None:
            out_txt.append(f"{prefix}{text}")

        return output

    class PostfixWriterResource(ConfigurableResourceFactory[Callable[[str], None]]):
        writer: ResourceDependency[Callable[[str], None]]
        postfix: str

        def create_resource(self, context) -> Callable[[str], None]:
            def output(text: str):
                self.writer(f"{text}{self.postfix}")

            return output

    @asset
    def my_asset(writer: ResourceParam[Callable[[str], None]]):
        writer("foo")
        writer("bar")

    defs = Definitions(
        assets=[my_asset],
        resources={
            "writer": PostfixWriterResource(writer=writer_resource, postfix="!"),
        },
    )

    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
    assert out_txt == ["foo!", "bar!"]

    out_txt.clear()

    defs = Definitions(
        assets=[my_asset],
        resources={
            "writer": PostfixWriterResource(
                writer=writer_resource.configured({"prefix": "msg: "}), postfix="!"
            ),
        },
    )

    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
    assert out_txt == ["msg: foo!", "msg: bar!"]


def test_nested_function_resource_runtime_config() -> None:
    out_txt = []

    @resource(config_schema={"prefix": str})
    def writer_resource(context):
        prefix = context.resource_config["prefix"]

        def output(text: str) -> None:
            out_txt.append(f"{prefix}{text}")

        return output

    class PostfixWriterResource(ConfigurableResourceFactory[Callable[[str], None]]):
        writer: ResourceDependency[Callable[[str], None]]
        postfix: str

        def create_resource(self, context) -> Callable[[str], None]:
            def output(text: str):
                self.writer(f"{text}{self.postfix}")

            return output

    @asset
    def my_asset(writer: ResourceParam[Callable[[str], None]]):
        writer("foo")
        writer("bar")

    with pytest.raises(
        CheckError,
        match="Any partially configured, nested resources must be provided to Definitions",
    ):
        # errors b/c writer_resource is not configured
        # and not provided as a top-level resource to Definitions
        defs = Definitions(
            assets=[my_asset],
            resources={
                "writer": PostfixWriterResource(writer=writer_resource, postfix="!"),
            },
        )

    defs = Definitions(
        assets=[my_asset],
        resources={
            "base_writer": writer_resource,
            "writer": PostfixWriterResource(writer=writer_resource, postfix="!"),
        },
    )

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process(
            {
                "resources": {
                    "base_writer": {
                        "config": {
                            "prefix": "msg: ",
                        },
                    },
                },
            }
        )
        .success
    )
    assert out_txt == ["msg: foo!", "msg: bar!"]


def test_nested_resource_raw_value() -> None:
    class MyResourceWithDep(ConfigurableResource):
        a_string: ResourceDependency[str]

    @resource
    def string_resource(context) -> str:
        return "foo"

    executed = {}

    @asset
    def my_asset(my_resource: MyResourceWithDep):
        assert my_resource.a_string == "foo"
        executed["yes"] = True

    defs = Definitions(
        assets=[my_asset],
        resources={
            "my_resource": MyResourceWithDep(a_string=string_resource),
        },
    )
    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
    assert executed["yes"]

    executed.clear()

    defs = Definitions(
        assets=[my_asset],
        resources={"my_resource": MyResourceWithDep(a_string="foo")},
    )
    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
    assert executed["yes"]


def test_nested_resource_raw_value_io_manager() -> None:
    class MyMultiwriteIOManager(ConfigurableIOManager):
        base_io_manager: ResourceDependency[IOManager]
        mirror_io_manager: ResourceDependency[IOManager]

        def handle_output(self, context, obj) -> None:
            self.base_io_manager.handle_output(context, obj)
            self.mirror_io_manager.handle_output(context, obj)

        def load_input(self, context) -> Any:
            return self.base_io_manager.load_input(context)

    log = []

    class ConfigIOManager(ConfigurableIOManager):
        path_prefix: List[str]

        def handle_output(self, context, obj) -> None:
            log.append(
                "ConfigIOManager handle_output "
                + "/".join(self.path_prefix + list(context.asset_key.path))
            )

        def load_input(self, context) -> Any:
            log.append(
                "ConfigIOManager load_input "
                + "/".join(self.path_prefix + list(context.asset_key.path))
            )
            return "foo"

    class RawIOManager(IOManager):
        def handle_output(self, context, obj) -> None:
            log.append("RawIOManager handle_output " + "/".join(list(context.asset_key.path)))

        def load_input(self, context) -> Any:
            log.append("RawIOManager load_input " + "/".join(list(context.asset_key.path)))
            return "foo"

    @asset
    def my_asset() -> str:
        return "foo"

    @asset
    def my_downstream_asset(my_asset: str) -> str:
        return my_asset + "bar"

    defs = Definitions(
        assets=[my_asset, my_downstream_asset],
        resources={
            "io_manager": MyMultiwriteIOManager(
                base_io_manager=ConfigIOManager(path_prefix=["base"]),
                mirror_io_manager=RawIOManager(),
            ),
        },
    )

    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
    assert log == [
        "ConfigIOManager handle_output base/my_asset",
        "RawIOManager handle_output my_asset",
        "ConfigIOManager load_input base/my_asset",
        "ConfigIOManager handle_output base/my_downstream_asset",
        "RawIOManager handle_output my_downstream_asset",
    ]


def test_enum_nested_resource_no_run_config() -> None:
    class MyEnum(enum.Enum):
        A = "a_value"
        B = "b_value"

    class ResourceWithEnum(ConfigurableResource):
        my_enum: MyEnum

    class OuterResourceWithResourceWithEnum(ConfigurableResource):
        resource_with_enum: ResourceWithEnum

    @asset
    def asset_with_outer_resource(outer_resource: OuterResourceWithResourceWithEnum):
        return outer_resource.resource_with_enum.my_enum.value

    defs = Definitions(
        assets=[asset_with_outer_resource],
        resources={
            "outer_resource": OuterResourceWithResourceWithEnum(
                resource_with_enum=ResourceWithEnum(my_enum=MyEnum.A)
            )
        },
    )

    a_job = defs.get_implicit_global_asset_job_def()

    result = a_job.execute_in_process()
    assert result.success
    assert result.output_for_node("asset_with_outer_resource") == "a_value"


def test_enum_nested_resource_run_config_override() -> None:
    class MyEnum(enum.Enum):
        A = "a_value"
        B = "b_value"

    class ResourceWithEnum(ConfigurableResource):
        my_enum: MyEnum

    class OuterResourceWithResourceWithEnum(ConfigurableResource):
        resource_with_enum: ResourceWithEnum

    @asset
    def asset_with_outer_resource(outer_resource: OuterResourceWithResourceWithEnum):
        return outer_resource.resource_with_enum.my_enum.value

    resource_with_enum = ResourceWithEnum.configure_at_launch()
    defs = Definitions(
        assets=[asset_with_outer_resource],
        resources={
            "resource_with_enum": resource_with_enum,
            "outer_resource": OuterResourceWithResourceWithEnum(
                resource_with_enum=resource_with_enum
            ),
        },
    )

    a_job = defs.get_implicit_global_asset_job_def()

    # Case: I'm re-specifying the nested enum at runtime - expect the runtime config to override the resource config
    result = a_job.execute_in_process(
        run_config={"resources": {"resource_with_enum": {"config": {"my_enum": "B"}}}}
    )
    assert result.success
    assert result.output_for_node("asset_with_outer_resource") == "b_value"


def test_nested_resource_raw_value_io_manager_with_setup_teardown() -> None:
    log = []

    class MyMultiwriteIOManager(ConfigurableIOManager):
        base_io_manager: ResourceDependency[IOManager]
        mirror_io_manager: ResourceDependency[IOManager]

        def handle_output(self, context, obj) -> None:
            self.base_io_manager.handle_output(context, obj)
            self.mirror_io_manager.handle_output(context, obj)

        def load_input(self, context) -> Any:
            return self.base_io_manager.load_input(context)

        def setup_for_execution(self, context: InitResourceContext) -> None:
            log.append("MyMultiwriteIOManager setup_for_execution")

        def teardown_after_execution(self, context: InitResourceContext) -> None:
            log.append("MyMultiwriteIOManager teardown_after_execution")

    class ConfigIOManager(ConfigurableIOManager):
        path_prefix: List[str]

        def setup_for_execution(self, context: InitResourceContext) -> None:
            log.append("ConfigIOManager setup_for_execution")

        def teardown_after_execution(self, context: InitResourceContext) -> None:
            log.append("ConfigIOManager teardown_after_execution")

        def handle_output(self, context, obj) -> None:
            log.append(
                "ConfigIOManager handle_output "
                + "/".join(self.path_prefix + list(context.asset_key.path))
            )

        def load_input(self, context) -> Any:
            log.append(
                "ConfigIOManager load_input "
                + "/".join(self.path_prefix + list(context.asset_key.path))
            )
            return "foo"

    class RawIOManager(IOManager):
        def handle_output(self, context, obj) -> None:
            log.append("RawIOManager handle_output " + "/".join(list(context.asset_key.path)))

        def load_input(self, context) -> Any:
            log.append("RawIOManager load_input " + "/".join(list(context.asset_key.path)))
            return "foo"

    @asset
    def my_asset() -> str:
        return "foo"

    @asset
    def my_downstream_asset(my_asset: str) -> str:
        return my_asset + "bar"

    defs = Definitions(
        assets=[my_asset, my_downstream_asset],
        resources={
            "io_manager": MyMultiwriteIOManager(
                base_io_manager=ConfigIOManager(path_prefix=["base"]),
                mirror_io_manager=RawIOManager(),
            ),
        },
    )

    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
    assert log == [
        "ConfigIOManager setup_for_execution",
        "MyMultiwriteIOManager setup_for_execution",
        "ConfigIOManager handle_output base/my_asset",
        "RawIOManager handle_output my_asset",
        "ConfigIOManager load_input base/my_asset",
        "ConfigIOManager handle_output base/my_downstream_asset",
        "RawIOManager handle_output my_downstream_asset",
        "MyMultiwriteIOManager teardown_after_execution",
        "ConfigIOManager teardown_after_execution",
    ]


def test_nested_resource_raw_value_io_manager_with_cm_setup_teardown() -> None:
    log = []

    class MyMultiwriteIOManager(ConfigurableIOManager):
        base_io_manager: ResourceDependency[IOManager]
        mirror_io_manager: ResourceDependency[IOManager]

        def handle_output(self, context, obj) -> None:
            self.base_io_manager.handle_output(context, obj)
            self.mirror_io_manager.handle_output(context, obj)

        def load_input(self, context) -> Any:
            return self.base_io_manager.load_input(context)

        def setup_for_execution(self, context: InitResourceContext) -> None:
            log.append("MyMultiwriteIOManager setup_for_execution")

        def teardown_after_execution(self, context: InitResourceContext) -> None:
            log.append("MyMultiwriteIOManager teardown_after_execution")

    class ConfigIOManager(ConfigurableIOManager):
        path_prefix: List[str]

        @contextlib.contextmanager
        def yield_for_execution(self, context: InitResourceContext):
            log.append("ConfigIOManager cm setup")
            yield self
            log.append("ConfigIOManager cm teardown")

        def handle_output(self, context, obj) -> None:
            log.append(
                "ConfigIOManager handle_output "
                + "/".join(self.path_prefix + list(context.asset_key.path))
            )

        def load_input(self, context) -> Any:
            log.append(
                "ConfigIOManager load_input "
                + "/".join(self.path_prefix + list(context.asset_key.path))
            )
            return "foo"

    class RawIOManager(IOManager):
        def handle_output(self, context, obj) -> None:
            log.append("RawIOManager handle_output " + "/".join(list(context.asset_key.path)))

        def load_input(self, context) -> Any:
            log.append("RawIOManager load_input " + "/".join(list(context.asset_key.path)))
            return "foo"

    @resource
    @contextlib.contextmanager
    def raw_io_manager(context):
        log.append("RawIOManager cm setup")
        yield RawIOManager()
        log.append("RawIOManager cm teardown")

    @asset
    def my_asset() -> str:
        return "foo"

    @asset
    def my_downstream_asset(my_asset: str) -> str:
        return my_asset + "bar"

    defs = Definitions(
        assets=[my_asset, my_downstream_asset],
        resources={
            "io_manager": MyMultiwriteIOManager(
                base_io_manager=ConfigIOManager(path_prefix=["base"]),
                mirror_io_manager=raw_io_manager,
            ),
        },
    )

    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
    assert log == [
        "ConfigIOManager cm setup",
        "RawIOManager cm setup",
        "MyMultiwriteIOManager setup_for_execution",
        "ConfigIOManager handle_output base/my_asset",
        "RawIOManager handle_output my_asset",
        "ConfigIOManager load_input base/my_asset",
        "ConfigIOManager handle_output base/my_downstream_asset",
        "RawIOManager handle_output my_downstream_asset",
        "MyMultiwriteIOManager teardown_after_execution",
        "RawIOManager cm teardown",
        "ConfigIOManager cm teardown",
    ]
