import enum
import json
import os
import re
import subprocess
import sys
import tempfile
from abc import ABC, abstractmethod
from typing import Any, Callable, List, Mapping, Optional, cast

import mock
import pytest
from dagster import (
    BindResourcesToJobs,
    DagsterInstance,
    IOManager,
    JobDefinition,
    RunRequest,
    ScheduleDefinition,
    asset,
    job,
    op,
    repository,
    resource,
    sensor,
)
from dagster._check import CheckError
from dagster._config.field import Field
from dagster._config.field_utils import EnvVar
from dagster._config.pythonic_config import (
    Config,
    ConfigurableIOManager,
    ConfigurableIOManagerFactory,
    ConfigurableLegacyIOManagerAdapter,
    ConfigurableResource,
    ConfigurableResourceFactory,
    IAttachDifferentObjectToOpContext,
    ResourceDependency,
)
from dagster._core.definitions.assets_job import build_assets_job
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.repository_definition.repository_data_builder import (
    build_caching_repository_data_from_dict,
)
from dagster._core.definitions.resource_annotation import ResourceParam
from dagster._core.definitions.run_config import RunConfig
from dagster._core.errors import (
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
)
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.execution.context.init import InitResourceContext, build_init_resource_context
from dagster._core.execution.context.invocation import build_op_context
from dagster._core.storage.io_manager import IOManagerDefinition, io_manager
from dagster._core.test_utils import environ
from dagster._utils.cached_method import cached_method
from pydantic import (
    Field as PyField,
    SecretStr,
    ValidationError,
)


def test_basic_structured_resource():
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @op
    def hello_world_op(writer: WriterResource):
        writer.output("hello, world!")

    @job(resource_defs={"writer": WriterResource(prefix="")})
    def no_prefix_job():
        hello_world_op()

    assert no_prefix_job.execute_in_process().success
    assert out_txt == ["hello, world!"]

    out_txt.clear()

    @job(resource_defs={"writer": WriterResource(prefix="greeting: ")})
    def prefix_job():
        hello_world_op()

    assert prefix_job.execute_in_process().success
    assert out_txt == ["greeting: hello, world!"]


def test_basic_structured_resource_assets() -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @asset
    def hello_world_asset(writer: WriterResource):
        writer.output("hello, world!")

    defs = Definitions(
        assets=[hello_world_asset], resources={"writer": WriterResource(prefix="greeting: ")}
    )

    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
    assert out_txt == ["greeting: hello, world!"]


def test_invalid_config() -> None:
    class MyResource(ConfigurableResource):
        foo: int

    with pytest.raises(
        ValidationError,
    ):
        # pyright: reportGeneralTypeIssues=false
        MyResource(foo="why")


@pytest.mark.skipif(sys.version_info < (3, 8), reason="requires python3.8")
def test_caching_within_resource():
    called = {"greeting": 0, "get_introduction": 0}

    from functools import cached_property

    class GreetingResource(ConfigurableResource):
        name: str

        @cached_property
        def greeting(self) -> str:
            called["greeting"] += 1
            return f"Hello, {self.name}"

        # Custom decorator which caches an instance method
        @cached_method
        def get_introduction(self, verbose: bool) -> str:
            called["get_introduction"] += 1
            return f"My name is {self.name}" if verbose else f"I'm {self.name}"

    @op
    def hello_world_op(greeting: GreetingResource):
        assert greeting.greeting == "Hello, Dagster"
        assert greeting.get_introduction(verbose=True) == "My name is Dagster"
        assert greeting.get_introduction(verbose=False) == "I'm Dagster"

    @op
    def another_op(greeting: GreetingResource):
        assert greeting.greeting == "Hello, Dagster"
        assert greeting.get_introduction(verbose=True) == "My name is Dagster"
        assert greeting.get_introduction(verbose=False) == "I'm Dagster"

    @job(resource_defs={"greeting": GreetingResource(name="Dagster")})
    def hello_world_job():
        hello_world_op()
        another_op()

    assert hello_world_job.execute_in_process().success

    # Each should only be called once, because of the caching
    assert called["greeting"] == 1
    assert called["get_introduction"] == 2

    called = {"greeting": 0, "get_introduction": 0}

    @asset
    def hello_world_asset(greeting: GreetingResource):
        assert greeting.greeting == "Hello, Dagster"
        assert greeting.get_introduction(verbose=True) == "My name is Dagster"
        assert greeting.get_introduction(verbose=False) == "I'm Dagster"
        return greeting.greeting

    @asset
    def another_asset(greeting: GreetingResource, hello_world_asset):
        assert hello_world_asset == "Hello, Dagster"
        assert greeting.greeting == "Hello, Dagster"
        assert greeting.get_introduction(verbose=True) == "My name is Dagster"
        assert greeting.get_introduction(verbose=False) == "I'm Dagster"

    assert (
        build_assets_job(
            "blah",
            [hello_world_asset, another_asset],
            resource_defs={"greeting": GreetingResource(name="Dagster")},
        )
        .execute_in_process()
        .success
    )

    assert called["greeting"] == 1
    assert called["get_introduction"] == 2


def test_abc_resource():
    out_txt = []

    class Writer(ConfigurableResource, ABC):
        @abstractmethod
        def output(self, text: str) -> None:
            pass

    class PrefixedWriterResource(Writer):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    class RepetitiveWriterResource(Writer):
        repetitions: int

        def output(self, text: str) -> None:
            out_txt.append(f"{text} " * self.repetitions)

    @op
    def hello_world_op(writer: Writer):
        writer.output("hello, world!")

    # Can't instantiate abstract class
    with pytest.raises(TypeError):
        Writer()

    @job(resource_defs={"writer": PrefixedWriterResource(prefix="greeting: ")})
    def prefixed_job():
        hello_world_op()

    assert prefixed_job.execute_in_process().success
    assert out_txt == ["greeting: hello, world!"]

    out_txt.clear()

    @job(resource_defs={"writer": RepetitiveWriterResource(repetitions=3)})
    def repetitive_writer_job():
        hello_world_op()

    assert repetitive_writer_job.execute_in_process().success
    assert out_txt == ["hello, world! " * 3]


def test_yield_in_resource_function():
    called = []

    class ResourceWithCleanup(ConfigurableResourceFactory[bool]):
        idx: int

        def create_resource(self, context):
            called.append(f"creation_{self.idx}")
            yield True
            called.append(f"cleanup_{self.idx}")

    @op
    def check_resource_created(
        resource_with_cleanup_1: ResourceParam[bool], resource_with_cleanup_2: ResourceParam[bool]
    ):
        assert resource_with_cleanup_1 is True
        assert resource_with_cleanup_2 is True
        called.append("op")

    @job(
        resource_defs={
            "resource_with_cleanup_1": ResourceWithCleanup(idx=1),
            "resource_with_cleanup_2": ResourceWithCleanup(idx=2),
        }
    )
    def the_job():
        check_resource_created()

    assert the_job.execute_in_process().success

    assert called == ["creation_1", "creation_2", "op", "cleanup_2", "cleanup_1"]


def test_migration_attach_bare_object_to_context() -> None:
    executed = {}

    class MyClient:
        def foo(self) -> str:
            return "foo"

    class MyClientResource(ConfigurableResource, IAttachDifferentObjectToOpContext):
        def get_client(self) -> MyClient:
            return MyClient()

        def get_object_to_set_on_execution_context(self) -> MyClient:
            return self.get_client()

    @asset(required_resource_keys={"my_client"})
    def uses_client_asset_unmigrated(context) -> str:
        assert context.resources.my_client
        assert context.resources.my_client.foo() == "foo"
        executed["unmigrated"] = True
        return "foo"

    @asset
    def uses_client_asset_migrated(my_client: MyClientResource) -> str:
        assert my_client
        assert my_client.get_client().foo() == "foo"
        executed["migrated"] = True
        return "foo"

    defs = Definitions(
        assets=[uses_client_asset_migrated, uses_client_asset_unmigrated],
        resources={"my_client": MyClientResource()},
    )

    asset_job = defs.get_implicit_global_asset_job_def()
    assert asset_job
    assert asset_job.execute_in_process().success
    assert executed["unmigrated"]
    assert executed["migrated"]


class AnIOManagerImplementation(IOManager):
    def __init__(self, a_config_value: str):
        self.a_config_value = a_config_value

    def load_input(self, _):
        pass

    def handle_output(self, _, obj):
        pass


def test_io_manager_adapter():
    @io_manager(config_schema={"a_config_value": str})
    def an_io_manager(context: InitResourceContext) -> AnIOManagerImplementation:
        return AnIOManagerImplementation(context.resource_config["a_config_value"])

    class AdapterForIOManager(ConfigurableLegacyIOManagerAdapter):
        a_config_value: str

        @property
        def wrapped_io_manager(self) -> IOManagerDefinition:
            return an_io_manager

    executed = {}

    @asset
    def an_asset(context: OpExecutionContext):
        assert context.resources.io_manager.a_config_value == "passed-in-configured"
        executed["yes"] = True

    defs = Definitions(
        assets=[an_asset],
        resources={"io_manager": AdapterForIOManager(a_config_value="passed-in-configured")},
    )
    defs.get_implicit_global_asset_job_def().execute_in_process()

    assert executed["yes"]


def test_io_manager_factory_class():
    # now test without the adapter
    class AnIOManagerFactory(ConfigurableIOManagerFactory):
        a_config_value: str

        def create_io_manager(self, _) -> IOManager:
            """Implement as one would implement a @io_manager decorator function."""
            return AnIOManagerImplementation(self.a_config_value)

    executed = {}

    @asset
    def another_asset(context: OpExecutionContext):
        assert context.resources.io_manager.a_config_value == "passed-in-factory"
        executed["yes"] = True

    defs = Definitions(
        assets=[another_asset],
        resources={"io_manager": AnIOManagerFactory(a_config_value="passed-in-factory")},
    )
    defs.get_implicit_global_asset_job_def().execute_in_process()

    assert executed["yes"]


def test_structured_resource_runtime_config():
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @asset
    def hello_world_asset(writer: WriterResource):
        writer.output("hello, world!")

    defs = Definitions(
        assets=[hello_world_asset],
        resources={"writer": WriterResource.configure_at_launch()},
    )

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process({"resources": {"writer": {"config": {"prefix": ""}}}})
        .success
    )
    assert out_txt == ["hello, world!"]

    out_txt.clear()

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process({"resources": {"writer": {"config": {"prefix": "greeting: "}}}})
        .success
    )
    assert out_txt == ["greeting: hello, world!"]


def test_runtime_config_run_config_obj():
    # Use RunConfig to specify resource config
    # in a structured format at runtime rather than using a dict

    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @asset
    def hello_world_asset(writer: WriterResource):
        writer.output("hello, world!")

    defs = Definitions(
        assets=[hello_world_asset],
        resources={"writer": WriterResource.configure_at_launch()},
    )

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process(RunConfig(resources={"writer": WriterResource(prefix="greeting: ")}))
        .success
    )
    assert out_txt == ["greeting: hello, world!"]


def test_nested_resources():
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


def test_nested_resources_multiuse():
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


def test_nested_resources_runtime_config():
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


def test_nested_resources_runtime_config_complex():
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


def test_resources_which_return():
    class StringResource(ConfigurableResourceFactory[str]):
        a_string: str

        def create_resource(self, context) -> str:
            return self.a_string

    class MyResource(ConfigurableResource):
        string_from_resource: ResourceDependency[str]

    completed = {}

    @asset
    def my_asset(my_resource: MyResource):
        assert my_resource.string_from_resource == "foo"
        completed["yes"] = True

    str_resource = StringResource(a_string="foo")
    my_resource = MyResource(string_from_resource=str_resource)

    defs = Definitions(
        assets=[my_asset],
        resources={
            "my_resource": my_resource,
        },
    )

    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
    assert completed["yes"]

    str_resource_partial = StringResource.configure_at_launch()
    my_resource = MyResource(string_from_resource=str_resource_partial)

    defs = Definitions(
        assets=[my_asset],
        resources={
            "str_resource_partial": str_resource_partial,
            "my_resource": my_resource,
        },
    )

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process(
            {
                "resources": {
                    "str_resource_partial": {
                        "config": {
                            "a_string": "foo",
                        },
                    }
                }
            }
        )
        .success
    )
    assert completed["yes"]


def test_nested_function_resource():
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


def test_nested_function_resource_configured():
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


def test_nested_function_resource_runtime_config():
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


def get_pyright_reveal_type_output(filename) -> List[str]:
    stdout = subprocess.check_output(["pyright", filename]).decode("utf-8")
    match = re.findall(r'Type of "(?:[^"]+)" is "([^"]+)"', stdout)
    assert match
    return match


def get_mypy_type_output(filename) -> List[str]:
    stdout = subprocess.check_output(["mypy", filename]).decode("utf-8")
    match = re.findall(r'note: Revealed type is "([^"]+)"', stdout)
    assert match
    return match


# you can specify the -m "typesignature" flag to run these tests, they're
# slow so we don't want to run them by default
@pytest.mark.typesignature
def test_type_signatures_constructor_nested_resource():
    with tempfile.TemporaryDirectory() as tempdir:
        filename = os.path.join(tempdir, "test.py")

        with open(filename, "w") as f:
            f.write(
                """
from dagster import ConfigurableResource

class InnerResource(ConfigurableResource):
    a_string: str

class OuterResource(ConfigurableResource):
    inner: InnerResource
    a_bool: bool

reveal_type(InnerResource.__init__)
reveal_type(OuterResource.__init__)

my_outer = OuterResource(inner=InnerResource(a_string="foo"), a_bool=True)
reveal_type(my_outer.inner)
"""
            )

        pyright_out = get_pyright_reveal_type_output(filename)
        mypy_out = get_mypy_type_output(filename)

        # Ensure constructor signature is correct (mypy doesn't yet support Pydantic model constructor type hints)
        assert pyright_out[0] == "(self: InnerResource, *, a_string: str) -> None"
        assert (
            pyright_out[1]
            == "(self: OuterResource, *, inner: InnerResource | PartialResource[InnerResource],"
            " a_bool: bool) -> None"
        )

        # Ensure that the retrieved type is the same as the type of the resource (no partial)
        assert pyright_out[2] == "InnerResource"
        assert mypy_out[2] == "test.InnerResource"


@pytest.mark.typesignature
def test_type_signatures_config_at_launch():
    with tempfile.TemporaryDirectory() as tempdir:
        filename = os.path.join(tempdir, "test.py")

        with open(filename, "w") as f:
            f.write(
                """
from dagster import ConfigurableResource

class MyResource(ConfigurableResource):
    a_string: str

reveal_type(MyResource.configure_at_launch())
"""
            )

        pyright_out = get_pyright_reveal_type_output(filename)
        mypy_out = get_mypy_type_output(filename)

        # Ensure partial resource is correctly parameterized
        assert pyright_out[0] == "PartialResource[MyResource]"
        assert mypy_out[0].endswith("PartialResource[test.MyResource]")


@pytest.mark.typesignature
def test_type_signatures_constructor_resource_dependency():
    with tempfile.TemporaryDirectory() as tempdir:
        filename = os.path.join(tempdir, "test.py")

        with open(filename, "w") as f:
            f.write(
                """
from dagster import ConfigurableResource, ResourceDependency

class StringDependentResource(ConfigurableResource):
    a_string: ResourceDependency[str]

reveal_type(StringDependentResource.__init__)

my_str_resource = StringDependentResource(a_string="foo")
reveal_type(my_str_resource.a_string)
"""
            )

        pyright_out = get_pyright_reveal_type_output(filename)
        mypy_out = get_mypy_type_output(filename)

        # Ensure constructor signature supports str Resource, PartialResource, raw str, or a
        # resource function that returns a str
        assert (
            pyright_out[0]
            == "(self: StringDependentResource, *, a_string: ConfigurableResourceFactory[str] |"
            " PartialResource[str] | ResourceDefinition | str) -> None"
        )

        # Ensure that the retrieved type is str
        assert pyright_out[1] == "str"
        assert mypy_out[1] == "builtins.str"


@pytest.mark.typesignature
def test_type_signatures_alias():
    with tempfile.TemporaryDirectory() as tempdir:
        filename = os.path.join(tempdir, "test.py")

        with open(filename, "w") as f:
            f.write(
                """
from dagster import ConfigurableResource
from pydantic import Field

class ResourceWithAlias(ConfigurableResource):
    _schema: str = Field(alias="schema")

reveal_type(ResourceWithAlias.__init__)

my_resource = ResourceWithAlias(schema="foo")
"""
            )

        pyright_out = get_pyright_reveal_type_output(filename)

        # Ensure constructor signature shows schema as the alias
        assert pyright_out[0] == "(self: ResourceWithAlias, *, schema: str) -> None"


def test_nested_config_class() -> None:
    # Validate that we can nest Config classes in a pythonic resource

    class User(Config):
        name: str
        age: int

    class UsersResource(ConfigurableResource):
        users: List[User]

    executed = {}

    @asset
    def an_asset(users_resource: UsersResource):
        assert len(users_resource.users) == 2
        assert users_resource.users[0].name == "Bob"
        assert users_resource.users[0].age == 25
        assert users_resource.users[1].name == "Alice"
        assert users_resource.users[1].age == 30

        executed["yes"] = True

    defs = Definitions(
        assets=[an_asset],
        resources={
            "users_resource": UsersResource(
                users=[
                    User(name="Bob", age=25),
                    User(name="Alice", age=30),
                ]
            )
        },
    )

    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
    assert executed["yes"]


def test_env_var():
    with environ(
        {
            "ENV_VARIABLE_FOR_TEST": "SOME_VALUE",
        }
    ):

        class ResourceWithString(ConfigurableResource):
            a_str: str

        executed = {}

        @asset
        def an_asset(a_resource: ResourceWithString):
            assert a_resource.a_str == "SOME_VALUE"
            executed["yes"] = True

        defs = Definitions(
            assets=[an_asset],
            resources={
                "a_resource": ResourceWithString(
                    a_str=EnvVar("ENV_VARIABLE_FOR_TEST"),
                )
            },
        )

        assert defs.get_implicit_global_asset_job_def().execute_in_process().success
        assert executed["yes"]


def test_env_var_data_structure() -> None:
    with environ(
        {
            "FOO": "hello",
            "BAR": "world",
        }
    ):

        class ResourceWithString(ConfigurableResource):
            my_list: List[str]
            my_dict: Mapping[str, str]

        executed = {}

        @asset
        def an_asset(a_resource: ResourceWithString):
            assert len(a_resource.my_list) == 2
            assert a_resource.my_list[0] == "hello"
            assert a_resource.my_list[1] == "world"
            assert len(a_resource.my_dict) == 2
            assert a_resource.my_dict["foo"] == "hello"
            assert a_resource.my_dict["bar"] == "world"
            executed["yes"] = True

        defs = Definitions(
            assets=[an_asset],
            resources={
                "a_resource": ResourceWithString(
                    my_list=[EnvVar("FOO"), EnvVar("BAR")],
                    my_dict={
                        "foo": EnvVar("FOO"),
                        "bar": EnvVar("BAR"),
                    },
                )
            },
        )

        assert defs.get_implicit_global_asset_job_def().execute_in_process().success
        assert executed["yes"]


def test_runtime_config_env_var():
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @asset
    def hello_world_asset(writer: WriterResource):
        writer.output("hello, world!")

    defs = Definitions(
        assets=[hello_world_asset],
        resources={"writer": WriterResource.configure_at_launch()},
    )

    os.environ["MY_PREFIX_FOR_TEST"] = "greeting: "
    try:
        assert (
            defs.get_implicit_global_asset_job_def()
            .execute_in_process(
                {"resources": {"writer": {"config": {"prefix": EnvVar("MY_PREFIX_FOR_TEST")}}}}
            )
            .success
        )
        assert out_txt == ["greeting: hello, world!"]
    finally:
        del os.environ["MY_PREFIX_FOR_TEST"]


def test_env_var_err():
    if "UNSET_ENV_VAR" in os.environ:
        del os.environ["UNSET_ENV_VAR"]

    class ResourceWithString(ConfigurableResource):
        a_str: str

    @asset
    def an_asset(a_resource: ResourceWithString):
        pass

    # No error constructing the resource, only at runtime
    defs = Definitions(
        assets=[an_asset],
        resources={
            "a_resource": ResourceWithString(
                a_str=EnvVar("UNSET_ENV_VAR"),
            )
        },
    )
    with pytest.raises(
        DagsterInvalidConfigError,
        match=(
            'You have attempted to fetch the environment variable "UNSET_ENV_VAR" which is not set.'
        ),
    ):
        defs.get_implicit_global_asset_job_def().execute_in_process()

    # Test using runtime configuration of the resource
    defs = Definitions(
        assets=[an_asset],
        resources={"a_resource": ResourceWithString.configure_at_launch()},
    )
    with pytest.raises(
        DagsterInvalidConfigError,
        match=(
            'You have attempted to fetch the environment variable "UNSET_ENV_VAR_RUNTIME" which is'
            " not set."
        ),
    ):
        defs.get_implicit_global_asset_job_def().execute_in_process(
            {"resources": {"a_resource": {"config": {"a_str": EnvVar("UNSET_ENV_VAR_RUNTIME")}}}}
        )


def test_env_var_nested_resources() -> None:
    class ResourceWithString(ConfigurableResource):
        a_str: str

    class OuterResource(ConfigurableResource):
        inner: ResourceWithString

    executed = {}

    @asset
    def an_asset(a_resource: OuterResource):
        assert a_resource.inner.a_str == "SOME_VALUE"
        executed["yes"] = True

    defs = Definitions(
        assets=[an_asset],
        resources={
            "a_resource": OuterResource(
                inner=ResourceWithString(
                    a_str=EnvVar("ENV_VARIABLE_FOR_TEST"),
                )
            )
        },
    )

    with environ(
        {
            "ENV_VARIABLE_FOR_TEST": "SOME_VALUE",
        }
    ):
        assert defs.get_implicit_global_asset_job_def().execute_in_process().success
        assert executed["yes"]


def test_env_var_nested_config() -> None:
    class NestedWithString(Config):
        a_str: str

    class OuterResource(ConfigurableResource):
        inner: NestedWithString

    executed = {}

    @asset
    def an_asset(a_resource: OuterResource):
        assert a_resource.inner.a_str == "SOME_VALUE"
        executed["yes"] = True

    defs = Definitions(
        assets=[an_asset],
        resources={
            "a_resource": OuterResource(
                inner=NestedWithString(
                    a_str=EnvVar("ENV_VARIABLE_FOR_TEST"),
                )
            )
        },
    )

    with environ(
        {
            "ENV_VARIABLE_FOR_TEST": "SOME_VALUE",
        }
    ):
        assert defs.get_implicit_global_asset_job_def().execute_in_process().success
        assert executed["yes"]


def test_using_enum() -> None:
    executed = {}

    class MyEnum(enum.Enum):
        FOO = "foo"
        BAR = "bar"

    class MyResource(ConfigurableResource):
        an_enum: MyEnum

    @asset
    def an_asset(my_resource: MyResource):
        assert my_resource.an_enum == MyEnum.FOO
        executed["yes"] = True

    defs = Definitions(
        assets=[an_asset],
        resources={
            "my_resource": MyResource(
                an_enum=MyEnum.FOO,
            )
        },
    )

    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
    assert executed["yes"]
    executed.clear()

    defs = Definitions(
        assets=[an_asset],
        resources={
            "my_resource": MyResource.configure_at_launch(),
        },
    )

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process(
            {"resources": {"my_resource": {"config": {"an_enum": MyEnum.FOO.name}}}}
        )
        .success
    )
    assert executed["yes"]


def test_using_enum_complex() -> None:
    executed = {}

    class MyEnum(enum.Enum):
        FOO = "foo"
        BAR = "bar"

    class MyResource(ConfigurableResource):
        list_of_enums: List[MyEnum]
        optional_enum: Optional[MyEnum] = None

    @asset
    def an_asset(my_resource: MyResource):
        assert my_resource.optional_enum is None
        assert my_resource.list_of_enums == [MyEnum.FOO, MyEnum.BAR]
        executed["yes"] = True

    defs = Definitions(
        assets=[an_asset],
        resources={
            "my_resource": MyResource(
                list_of_enums=[MyEnum.FOO, MyEnum.BAR],
            )
        },
    )

    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
    assert executed["yes"]
    executed.clear()


def test_resource_defs_on_asset() -> None:
    executed = {}

    class MyResource(ConfigurableResource):
        a_str: str

    @asset(resource_defs={"my_resource": MyResource(a_str="foo")})
    def an_asset(my_resource: MyResource):
        assert my_resource.a_str == "foo"
        executed["yes"] = True

    defs = Definitions(
        assets=[an_asset],
    )
    defs.get_implicit_global_asset_job_def().execute_in_process()

    assert executed["yes"]

    # Cannot specify both required_resource_keys and resources as args
    with pytest.raises(CheckError):

        @asset(required_resource_keys={"my_other_resource"})
        def an_other_asset(my_resource: MyResource):
            pass


def test_extending_resource() -> None:
    executed = {}

    class BaseResource(ConfigurableResource):
        a_str: str = "bar"
        an_int: int = 1

    class ExtendingResource(BaseResource):
        a_float: float = 1.0

    @op
    def hello_world_op(writer: ExtendingResource):
        assert writer.a_str == "foo"
        assert writer.an_int == 1
        assert writer.a_float == 1.0
        executed["yes"] = True

    @job(resource_defs={"writer": ExtendingResource(a_str="foo")})
    def no_prefix_job() -> None:
        hello_world_op()

    assert no_prefix_job.execute_in_process().success
    assert executed["yes"]


def test_extending_resource_nesting() -> None:
    executed = {}

    class NestedResource(ConfigurableResource):
        a_str: str

    class BaseResource(ConfigurableResource):
        nested: NestedResource
        a_str: str = "bar"
        an_int: int = 1

    class ExtendingResource(BaseResource):
        a_float: float = 1.0

    @asset
    def an_asset(writer: ExtendingResource):
        assert writer.a_str == "foo"
        assert writer.nested.a_str == "baz"
        assert writer.an_int == 1
        assert writer.a_float == 1.0
        executed["yes"] = True

    defs = Definitions(
        assets=[an_asset],
        resources={"writer": ExtendingResource(a_str="foo", nested=NestedResource(a_str="baz"))},
    )
    assert defs.get_implicit_global_asset_job_def().execute_in_process().success

    assert executed["yes"]
    executed.clear()

    nested_defer = NestedResource.configure_at_launch()
    defs = Definitions(
        assets=[an_asset],
        resources={
            "nested_deferred": nested_defer,
            "writer": ExtendingResource(a_str="foo", nested=nested_defer),
        },
    )
    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process(
            run_config={"resources": {"nested_deferred": {"config": {"a_str": "baz"}}}}
        )
        .success
    )

    assert executed["yes"]


def test_bind_resource_to_job_at_defn_time_err() -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @op
    def hello_world_op(writer: WriterResource):
        writer.output("hello, world!")

    @job
    def hello_world_job():
        hello_world_op()

    # Validate that jobs without bound resources error at repository construction time
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'writer' required by op 'hello_world_op' was not provided",
    ):
        build_caching_repository_data_from_dict({"jobs": {"hello_world_job": hello_world_job}})

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'writer' required by op 'hello_world_op' was not provided",
    ):

        @repository
        def my_repo():
            return [hello_world_job]

    # Validate that this also happens with Definitions
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'writer' required by op 'hello_world_op' was not provided",
    ):
        Definitions(
            jobs=[hello_world_job],
        )


def test_bind_resource_to_job_at_defn_time() -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @op
    def hello_world_op(writer: WriterResource):
        writer.output("hello, world!")

    @job
    def hello_world_job():
        hello_world_op()

    # Bind the resource to the job at definition time and validate that it works
    defs = Definitions(
        jobs=[hello_world_job],
        resources={
            "writer": WriterResource(prefix=""),
        },
    )

    assert defs.get_job_def("hello_world_job").execute_in_process().success
    assert out_txt == ["hello, world!"]

    out_txt.clear()

    defs = Definitions(
        jobs=[hello_world_job],
        resources={
            "writer": WriterResource(prefix="msg: "),
        },
    )

    assert defs.get_job_def("hello_world_job").execute_in_process().success
    assert out_txt == ["msg: hello, world!"]


def test_bind_resource_to_job_at_defn_time_bind_resources_to_jobs() -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @op
    def hello_world_op(writer: WriterResource):
        writer.output("hello, world!")

    @job
    def hello_world_job():
        hello_world_op()

    # BindResourcesToJobs is a no-op now
    defs = Definitions(
        jobs=BindResourcesToJobs([hello_world_job]),
        resources={
            "writer": WriterResource(prefix=""),
        },
    )

    assert defs.get_job_def("hello_world_job").execute_in_process().success
    assert out_txt == ["hello, world!"]

    out_txt.clear()

    # BindResourcesToJobs is a no-op now
    defs = Definitions(
        jobs=BindResourcesToJobs([hello_world_job]),
        resources={
            "writer": WriterResource(prefix="msg: "),
        },
    )

    assert defs.get_job_def("hello_world_job").execute_in_process().success
    assert out_txt == ["msg: hello, world!"]


def test_bind_resource_to_job_with_job_config() -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    class OpConfig(Config):
        message: str = "hello, world!"

    @op
    def hello_world_op(writer: WriterResource, config: OpConfig):
        writer.output(config.message)

    @job(config={})
    def hello_world_job() -> None:
        hello_world_op()

    @job(config={"ops": {"hello_world_op": {"config": {"message": "hello, earth!"}}}})
    def hello_earth_job() -> None:
        hello_world_op()

    defs = Definitions(
        jobs=[hello_world_job, hello_earth_job],
        resources={
            "writer": WriterResource(prefix="msg: "),
        },
    )

    assert defs.get_job_def("hello_world_job").execute_in_process().success
    assert out_txt == ["msg: hello, world!"]
    out_txt.clear()

    assert defs.get_job_def("hello_earth_job").execute_in_process().success
    assert out_txt == ["msg: hello, earth!"]

    # Validate that we correctly error
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'writer' required by op 'hello_world_op' was not provided",
    ):
        Definitions(
            jobs=[hello_world_job],
        )


def test_execute_in_process() -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @op
    def hello_world_op(writer: WriterResource):
        writer.output("hello, world!")

    @job
    def hello_world_job() -> None:
        hello_world_op()

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'writer' required by op 'hello_world_op' was not provided",
    ):
        hello_world_job.execute_in_process()

    assert not out_txt

    # Bind resource as part of calling execute_in_process
    assert hello_world_job.execute_in_process(
        resources={"writer": WriterResource(prefix="msg: ")}
    ).success
    assert out_txt == ["msg: hello, world!"]


def test_bind_resource_to_job_at_defn_time_override() -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @op
    def hello_world_op(writer: WriterResource):
        writer.output("hello, world!")

    # Binding the resource to the job at definition time should not override the resource
    @job(
        resource_defs={
            "writer": WriterResource(prefix="job says: "),
        }
    )
    def hello_world_job_with_override():
        hello_world_op()

    @job
    def hello_world_job_no_override():
        hello_world_op()

    defs = Definitions(
        jobs=[hello_world_job_with_override, hello_world_job_no_override],
        resources={
            "writer": WriterResource(prefix="definitions says: "),
        },
    )

    assert defs.get_job_def("hello_world_job_with_override").execute_in_process().success
    assert out_txt == ["job says: hello, world!"]
    out_txt.clear()

    assert defs.get_job_def("hello_world_job_no_override").execute_in_process().success
    assert out_txt == ["definitions says: hello, world!"]


def test_bind_resource_to_instigator() -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @op
    def hello_world_op(writer: WriterResource):
        writer.output("hello, world!")

    @job
    def hello_world_job():
        hello_world_op()

    @sensor(job=hello_world_job)
    def hello_world_sensor():
        ...

    hello_world_schedule = ScheduleDefinition(
        name="hello_world_schedule", cron_schedule="* * * * *", job=hello_world_job
    )

    # Bind the resource to the job at definition time and validate that it works
    defs = Definitions(
        jobs=[hello_world_job],
        schedules=[hello_world_schedule],
        sensors=[hello_world_sensor],
        resources={
            "writer": WriterResource(prefix="msg: "),
        },
    )

    assert (
        cast(JobDefinition, defs.get_sensor_def("hello_world_sensor").job)
        .execute_in_process()
        .success
    )
    assert out_txt == ["msg: hello, world!"]

    out_txt.clear()

    assert (
        cast(JobDefinition, defs.get_schedule_def("hello_world_schedule").job)
        .execute_in_process()
        .success
    )
    assert out_txt == ["msg: hello, world!"]

    out_txt.clear()


def test_bind_resource_to_instigator_by_name() -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @op
    def hello_world_op(writer: WriterResource):
        writer.output("hello, world!")

    @job
    def hello_world_job():
        hello_world_op()

    @sensor(job_name="hello_world_job")
    def hello_world_sensor():
        ...

    hello_world_schedule = ScheduleDefinition(
        name="hello_world_schedule", cron_schedule="* * * * *", job_name="hello_world_job"
    )

    # Bind the resource to the job at definition time and validate that it works
    defs = Definitions(
        jobs=[hello_world_job],
        schedules=[hello_world_schedule],
        sensors=[hello_world_sensor],
        resources={
            "writer": WriterResource(prefix="msg: "),
        },
    )

    assert (
        defs.get_job_def(cast(str, defs.get_sensor_def("hello_world_sensor").job_name))
        .execute_in_process()
        .success
    )
    assert out_txt == ["msg: hello, world!"]

    out_txt.clear()

    assert (
        defs.get_job_def(cast(str, defs.get_schedule_def("hello_world_schedule").job_name))
        .execute_in_process()
        .success
    )
    assert out_txt == ["msg: hello, world!"]

    out_txt.clear()


def test_bind_io_manager_default() -> None:
    outputs = []

    class MyIOManager(ConfigurableIOManager):
        def load_input(self, _) -> None:
            pass

        def handle_output(self, _, obj) -> None:
            outputs.append(obj)

    @op
    def hello_world_op() -> str:
        return "foo"

    @job
    def hello_world_job() -> None:
        hello_world_op()

    # Bind the I/O manager to the job at definition time and validate that it works
    defs = Definitions(
        jobs=[hello_world_job],
        resources={
            "io_manager": MyIOManager(),
        },
    )

    assert defs.get_job_def("hello_world_job").execute_in_process().success
    assert outputs == ["foo"]


def test_bind_io_manager_override() -> None:
    outputs = []

    class MyIOManager(ConfigurableIOManager):
        def load_input(self, _) -> None:
            pass

        def handle_output(self, _, obj) -> None:
            outputs.append(obj)

    class MyOtherIOManager(ConfigurableIOManager):
        def load_input(self, _) -> None:
            pass

        def handle_output(self, _, obj) -> None:
            pass

    @op
    def hello_world_op() -> str:
        return "foo"

    @job(resource_defs={"io_manager": MyIOManager()})
    def hello_world_job() -> None:
        hello_world_op()

    # Bind the I/O manager to the job at definition time and validate that it does
    # not take precedence over the one defined on the job
    defs = Definitions(
        jobs=[hello_world_job],
        resources={
            "io_manager": MyOtherIOManager(),
        },
    )

    assert defs.get_job_def("hello_world_job").execute_in_process().success
    assert outputs == ["foo"]


def test_aliased_field_structured_resource():
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix_: str = PyField(..., alias="prefix")

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix_}{text}")

    @op
    def hello_world_op(writer: WriterResource):
        writer.output("hello, world!")

    @job(resource_defs={"writer": WriterResource(prefix="")})
    def no_prefix_job():
        hello_world_op()

    assert no_prefix_job.execute_in_process().success
    assert out_txt == ["hello, world!"]

    out_txt.clear()

    @job(resource_defs={"writer": WriterResource(prefix="greeting: ")})
    def prefix_job():
        hello_world_op()

    assert prefix_job.execute_in_process().success
    assert out_txt == ["greeting: hello, world!"]

    out_txt.clear()

    @job(resource_defs={"writer": WriterResource.configure_at_launch()})
    def prefix_job_at_runtime():
        hello_world_op()

    assert prefix_job_at_runtime.execute_in_process(
        {"resources": {"writer": {"config": {"prefix": "runtime: "}}}}
    ).success
    assert out_txt == ["runtime: hello, world!"]


def test_direct_op_invocation() -> None:
    class MyResource(ConfigurableResource):
        a_str: str

    @op
    def my_op(context, my_resource: MyResource) -> str:
        assert my_resource.a_str == "foo"
        return my_resource.a_str

    # Just providing context is ok, we'll use the resource from the context
    assert my_op(build_op_context(resources={"my_resource": MyResource(a_str="foo")})) == "foo"

    # Providing both context and resource is not ok, because we don't know which one to use
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Cannot provide resources in both context and kwargs",
    ):
        assert (
            my_op(
                context=build_op_context(resources={"my_resource": MyResource(a_str="foo")}),
                my_resource=MyResource(a_str="foo"),
            )
            == "foo"
        )

    # Providing resource only as kwarg is ok, we'll use that (we still need a context though)
    assert my_op(context=build_op_context(), my_resource=MyResource(a_str="foo")) == "foo"

    # Providing resource only as positional arg is ok, we'll use that (we still need a context though)
    assert my_op(build_op_context(), MyResource(a_str="foo")) == "foo"

    @op
    def my_op_no_context(my_resource: MyResource) -> str:
        assert my_resource.a_str == "foo"
        return my_resource.a_str

    # Providing context is ok, we just discard it and use the resource from the context
    assert (
        my_op_no_context(build_op_context(resources={"my_resource": MyResource(a_str="foo")}))
        == "foo"
    )

    # Providing resource only as kwarg is ok, we'll use that
    assert my_op_no_context(my_resource=MyResource(a_str="foo")) == "foo"


def test_direct_op_invocation_multiple_resources() -> None:
    class MyResource(ConfigurableResource):
        a_str: str

    @op
    def my_op(context, my_resource: MyResource, my_other_resource: MyResource) -> str:
        assert my_resource.a_str == "foo"
        assert my_other_resource.a_str == "bar"
        return my_resource.a_str

    # Just providing context is ok, we'll use both resources from the context
    assert (
        my_op(
            build_op_context(
                resources={
                    "my_resource": MyResource(a_str="foo"),
                    "my_other_resource": MyResource(a_str="bar"),
                }
            )
        )
        == "foo"
    )

    # Providing resource only as kwarg is ok, we'll use that (we still need a context though)
    assert (
        my_op(
            context=build_op_context(),
            my_resource=MyResource(a_str="foo"),
            my_other_resource=MyResource(a_str="bar"),
        )
        == "foo"
    )

    @op
    def my_op_no_context(my_resource: MyResource, my_other_resource: MyResource) -> str:
        assert my_resource.a_str == "foo"
        assert my_other_resource.a_str == "bar"
        return my_resource.a_str

    # Providing context is ok, we just discard it and use the resource from the context
    assert (
        my_op_no_context(
            build_op_context(
                resources={
                    "my_resource": MyResource(a_str="foo"),
                    "my_other_resource": MyResource(a_str="bar"),
                }
            )
        )
        == "foo"
    )

    # Providing resource only as kwarg is ok, we'll use that
    assert (
        my_op_no_context(
            my_resource=MyResource(a_str="foo"), my_other_resource=MyResource(a_str="bar")
        )
        == "foo"
    )


def test_direct_op_invocation_with_inputs() -> None:
    class MyResource(ConfigurableResource):
        z: int

    @op
    def my_wacky_addition_op(context, x: int, y: int, my_resource: MyResource) -> int:
        return x + y + my_resource.z

    # Just providing context is ok, we'll use the resource from the context
    # We are successfully able to input x and y as args
    assert (
        my_wacky_addition_op(build_op_context(resources={"my_resource": MyResource(z=2)}), 4, 5)
        == 11
    )
    # We can also input x and y as kwargs
    assert (
        my_wacky_addition_op(build_op_context(resources={"my_resource": MyResource(z=3)}), y=1, x=2)
        == 6
    )

    # Providing resource only as kwarg is ok, we'll use that (we still need a context though)
    # We can input x and y as args
    assert my_wacky_addition_op(build_op_context(), 10, 20, my_resource=MyResource(z=30)) == 60
    # We can also input x and y as kwargs in this case
    assert my_wacky_addition_op(build_op_context(), y=1, x=2, my_resource=MyResource(z=3)) == 6

    @op
    def my_wacky_addition_op_no_context(x: int, y: int, my_resource: MyResource) -> int:
        return x + y + my_resource.z

    # Providing context is ok, we just discard it and use the resource from the context
    # We can input x and y as args
    assert (
        my_wacky_addition_op_no_context(
            build_op_context(resources={"my_resource": MyResource(z=2)}), 4, 5
        )
        == 11
    )
    # We can also input x and y as kwargs
    assert (
        my_wacky_addition_op_no_context(
            build_op_context(resources={"my_resource": MyResource(z=3)}), y=1, x=2
        )
        == 6
    )

    # Providing resource only as kwarg is ok, we'll use that
    # We can input x and y as args
    assert my_wacky_addition_op_no_context(10, 20, my_resource=MyResource(z=30)) == 60
    # We can also input x and y as kwargs in this case
    assert my_wacky_addition_op_no_context(y=1, x=2, my_resource=MyResource(z=3)) == 6

    # Direct invocation is a little weird if the resource comes before an input,
    # but it still works as long as you use kwargs for the inputs or provide the resource explicitly
    @op
    def my_wacky_addition_op_resource_first(my_resource: MyResource, x: int, y: int) -> int:
        return x + y + my_resource.z

    # Here we have to use kwargs for x and y because we're not providing the resource explicitly
    assert (
        my_wacky_addition_op_resource_first(
            build_op_context(resources={"my_resource": MyResource(z=2)}), x=4, y=5
        )
        == 11
    )

    # Here we can just use args for x and y because we're providing the resource explicitly as an arg
    assert my_wacky_addition_op_resource_first(MyResource(z=2), 45, 53) == 100


def test_direct_asset_invocation() -> None:
    class MyResource(ConfigurableResource):
        a_str: str

    @asset
    def my_asset(context, my_resource: MyResource) -> str:
        assert my_resource.a_str == "foo"
        return my_resource.a_str

    # Just providing context is ok, we'll use the resource from the context
    assert my_asset(build_op_context(resources={"my_resource": MyResource(a_str="foo")})) == "foo"

    # Providing both context and resource is not ok, because we don't know which one to use
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Cannot provide resources in both context and kwargs",
    ):
        assert (
            my_asset(
                context=build_op_context(resources={"my_resource": MyResource(a_str="foo")}),
                my_resource=MyResource(a_str="foo"),
            )
            == "foo"
        )

    # Providing resource only as kwarg is ok, we'll use that (we still need a context though)
    assert my_asset(context=build_op_context(), my_resource=MyResource(a_str="foo")) == "foo"

    # Providing resource  as arg is ok, we'll use that (we still need a context though)
    assert my_asset(build_op_context(), MyResource(a_str="foo")) == "foo"

    @asset
    def my_asset_no_context(my_resource: MyResource) -> str:
        assert my_resource.a_str == "foo"
        return my_resource.a_str

    # Providing context is ok, we just discard it and use the resource from the context
    assert (
        my_asset_no_context(build_op_context(resources={"my_resource": MyResource(a_str="foo")}))
        == "foo"
    )

    # Providing resource only as kwarg is ok, we'll use that
    assert my_asset_no_context(my_resource=MyResource(a_str="foo")) == "foo"


def test_direct_asset_invocation_with_inputs() -> None:
    class MyResource(ConfigurableResource):
        z: int

    @asset
    def my_wacky_addition_asset(context, x: int, y: int, my_resource: MyResource) -> int:
        return x + y + my_resource.z

    # Just providing context is ok, we'll use the resource from the context
    # We are successfully able to input x and y as args
    assert (
        my_wacky_addition_asset(build_op_context(resources={"my_resource": MyResource(z=2)}), 4, 5)
        == 11
    )
    # We can also input x and y as kwargs
    assert (
        my_wacky_addition_asset(
            build_op_context(resources={"my_resource": MyResource(z=3)}), y=1, x=2
        )
        == 6
    )

    # Providing resource only as kwarg is ok, we'll use that (we still need a context though)
    # We can input x and y as args
    assert my_wacky_addition_asset(build_op_context(), 10, 20, my_resource=MyResource(z=30)) == 60
    # We can also input x and y as kwargs in this case
    assert my_wacky_addition_asset(build_op_context(), y=1, x=2, my_resource=MyResource(z=3)) == 6

    @asset
    def my_wacky_addition_asset_no_context(x: int, y: int, my_resource: MyResource) -> int:
        return x + y + my_resource.z

    # Providing context is ok, we just discard it and use the resource from the context
    # We can input x and y as args
    assert (
        my_wacky_addition_asset_no_context(
            build_op_context(resources={"my_resource": MyResource(z=2)}), 4, 5
        )
        == 11
    )
    # We can also input x and y as kwargs
    assert (
        my_wacky_addition_asset_no_context(
            build_op_context(resources={"my_resource": MyResource(z=3)}), y=1, x=2
        )
        == 6
    )

    # Providing resource only as kwarg is ok, we'll use that
    # We can input x and y as args
    assert my_wacky_addition_asset_no_context(10, 20, my_resource=MyResource(z=30)) == 60
    # We can also input x and y as kwargs in this case
    assert my_wacky_addition_asset_no_context(y=1, x=2, my_resource=MyResource(z=3)) == 6


def test_from_resource_context_and_to_config_field() -> None:
    class StringResource(ConfigurableResourceFactory[str]):
        a_string: str

        def create_resource(self, context) -> str:
            return self.a_string + "bar"

    @resource(config_schema=StringResource.to_config_schema())
    def string_resource_function_style(context: InitResourceContext) -> str:
        return StringResource.from_resource_context(context)

    assert (
        string_resource_function_style(build_init_resource_context({"a_string": "foo"})) == "foobar"
    )


def test_from_resource_context_and_to_config_field_complex() -> None:
    class MyComplexConfigResource(ConfigurableResource):
        a_string: str
        a_list_of_ints: List[int]
        a_map_of_lists_of_maps_of_floats: Mapping[str, List[Mapping[str, float]]]

    @resource(config_schema=MyComplexConfigResource.to_config_schema())
    def complex_config_resource_function_style(
        context: InitResourceContext,
    ) -> MyComplexConfigResource:
        return MyComplexConfigResource.from_resource_context(context)

    complex_config_resource = complex_config_resource_function_style(
        build_init_resource_context(
            {
                "a_string": "foo",
                "a_list_of_ints": [1, 2, 3],
                "a_map_of_lists_of_maps_of_floats": {
                    "a": [{"b": 1.0}, {"c": 2.0}],
                    "d": [{"e": 3.0}, {"f": 4.0}],
                },
            }
        )
    )
    assert complex_config_resource.a_string == "foo"
    assert complex_config_resource.a_list_of_ints == [1, 2, 3]
    assert complex_config_resource.a_map_of_lists_of_maps_of_floats == {
        "a": [{"b": 1.0}, {"c": 2.0}],
        "d": [{"e": 3.0}, {"f": 4.0}],
    }


def test_direct_op_invocation_plain_arg_with_resource_definition_no_inputs_no_context() -> None:
    class NumResource(ConfigurableResource):
        num: int

    executed = {}

    @op
    def an_op(my_resource: NumResource) -> None:
        assert my_resource.num == 1
        executed["yes"] = True

    an_op(NumResource(num=1))

    assert executed["yes"]


def test_direct_op_invocation_kwarg_with_resource_definition_no_inputs_no_context() -> None:
    class NumResource(ConfigurableResource):
        num: int

    executed = {}

    @op
    def an_op(my_resource: NumResource) -> None:
        assert my_resource.num == 1
        executed["yes"] = True

    an_op(my_resource=NumResource(num=1))

    assert executed["yes"]


def test_direct_asset_invocation_plain_arg_with_resource_definition_no_inputs_no_context() -> None:
    class NumResource(ConfigurableResource):
        num: int

    executed = {}

    @asset
    def an_asset(my_resource: NumResource) -> None:
        assert my_resource.num == 1
        executed["yes"] = True

    an_asset(NumResource(num=1))

    assert executed["yes"]


def test_direct_asset_invocation_kwarg_with_resource_definition_no_inputs_no_context() -> None:
    class NumResource(ConfigurableResource):
        num: int

    executed = {}

    @asset
    def an_asset(my_resource: NumResource) -> None:
        assert my_resource.num == 1
        executed["yes"] = True

    an_asset(my_resource=NumResource(num=1))

    assert executed["yes"]


def test_direct_asset_invocation_many_resource_args() -> None:
    class NumResource(ConfigurableResource):
        num: int

    executed = {}

    @asset
    def an_asset(my_resource: NumResource, my_other_resource: NumResource) -> None:
        assert my_resource.num == 1
        assert my_other_resource.num == 2
        executed["yes"] = True

    an_asset(NumResource(num=1), NumResource(num=2))
    assert executed["yes"]
    executed.clear()

    an_asset(my_resource=NumResource(num=1), my_other_resource=NumResource(num=2))
    assert executed["yes"]
    executed.clear()

    an_asset(my_other_resource=NumResource(num=2), my_resource=NumResource(num=1))
    assert executed["yes"]
    executed.clear()

    an_asset(NumResource(num=1), my_other_resource=NumResource(num=2))
    assert executed["yes"]


def test_direct_asset_invocation_many_resource_args_context() -> None:
    class NumResource(ConfigurableResource):
        num: int

    executed = {}

    @asset
    def an_asset(context, my_resource: NumResource, my_other_resource: NumResource) -> None:
        assert context.resources.my_resource.num == 1
        assert context.resources.my_other_resource.num == 2
        assert my_resource.num == 1
        assert my_other_resource.num == 2
        executed["yes"] = True

    an_asset(build_op_context(), NumResource(num=1), NumResource(num=2))
    assert executed["yes"]
    executed.clear()

    an_asset(
        build_op_context(), my_resource=NumResource(num=1), my_other_resource=NumResource(num=2)
    )
    assert executed["yes"]
    executed.clear()

    an_asset(
        my_other_resource=NumResource(num=2),
        my_resource=NumResource(num=1),
        context=build_op_context(),
    )
    assert executed["yes"]
    executed.clear()


def test_from_resource_context_and_to_config_empty() -> None:
    class NoConfigResource(ConfigurableResource[str]):
        def get_string(self) -> str:
            return "foo"

    @resource(config_schema=NoConfigResource.to_config_schema())
    def string_resource_function_style(context: InitResourceContext) -> str:
        return NoConfigResource.from_resource_context(context).get_string()

    assert string_resource_function_style(build_init_resource_context()) == "foo"


def test_context_on_resource_basic() -> None:
    executed = {}

    class ContextUsingResource(ConfigurableResource):
        def access_context(self) -> None:
            self.get_resource_context()

    with pytest.raises(
        CheckError, match="Attempted to get context before resource was initialized."
    ):
        ContextUsingResource().access_context()

    # Can access context after binding one
    ContextUsingResource().with_resource_context(build_init_resource_context()).access_context()

    @asset
    def my_test_asset(context_using: ContextUsingResource) -> None:
        context_using.access_context()
        executed["yes"] = True

    defs = Definitions(
        assets=[my_test_asset],
        resources={"context_using": ContextUsingResource()},
    )

    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
    assert executed["yes"]


def test_context_on_resource_use_instance() -> None:
    executed = {}

    class OutputDirResource(ConfigurableResource):
        output_dir: Optional[str] = None

        def get_effective_output_dir(self) -> str:
            if self.output_dir:
                return self.output_dir

            context = self.get_resource_context()
            assert context.instance
            return context.instance.storage_directory()

    with pytest.raises(
        CheckError, match="Attempted to get context before resource was initialized."
    ):
        OutputDirResource(output_dir=None).get_effective_output_dir()

    with mock.patch(
        "dagster._core.instance.DagsterInstance.storage_directory"
    ) as storage_directory:
        storage_directory.return_value = "/tmp"

        with DagsterInstance.ephemeral() as instance:
            assert (
                OutputDirResource(output_dir=None)
                .with_resource_context(build_init_resource_context(instance=instance))
                .get_effective_output_dir()
                == "/tmp"
            )

        @asset
        def my_other_output_asset(output_dir: OutputDirResource) -> None:
            assert output_dir.get_effective_output_dir() == "/tmp"
            executed["yes"] = True

        defs = Definitions(
            assets=[my_other_output_asset],
            resources={"output_dir": OutputDirResource()},
        )

        assert defs.get_implicit_global_asset_job_def().execute_in_process().success
        assert executed["yes"]


def test_context_on_resource_runtime_config() -> None:
    executed = {}

    class OutputDirResource(ConfigurableResource):
        output_dir: Optional[str] = None

        def get_effective_output_dir(self) -> str:
            if self.output_dir:
                return self.output_dir

            context = self.get_resource_context()
            assert context.instance
            return context.instance.storage_directory()

    with mock.patch(
        "dagster._core.instance.DagsterInstance.storage_directory"
    ) as storage_directory:
        storage_directory.return_value = "/tmp"

        @asset
        def my_other_output_asset(output_dir: OutputDirResource) -> None:
            assert output_dir.get_effective_output_dir() == "/tmp"
            executed["yes"] = True

        defs = Definitions(
            assets=[my_other_output_asset],
            resources={"output_dir": OutputDirResource.configure_at_launch()},
        )

        assert (
            defs.get_implicit_global_asset_job_def()
            .execute_in_process(
                run_config={"resources": {"output_dir": {"config": {"output_dir": None}}}}
            )
            .success
        )
        assert executed["yes"]


def test_context_on_resource_nested() -> None:
    executed = {}

    class OutputDirResource(ConfigurableResource):
        output_dir: Optional[str] = None

        def get_effective_output_dir(self) -> str:
            if self.output_dir:
                return self.output_dir

            context = self.get_resource_context()
            assert context.instance
            return context.instance.storage_directory()

    class OutputDirWrapperResource(ConfigurableResource):
        output_dir: OutputDirResource

    with pytest.raises(
        CheckError, match="Attempted to get context before resource was initialized."
    ):
        OutputDirWrapperResource(
            output_dir=OutputDirResource(output_dir=None)
        ).output_dir.get_effective_output_dir()

    with mock.patch(
        "dagster._core.instance.DagsterInstance.storage_directory"
    ) as storage_directory:
        storage_directory.return_value = "/tmp"

        @asset
        def my_other_output_asset(wrapper: OutputDirWrapperResource) -> None:
            assert wrapper.output_dir.get_effective_output_dir() == "/tmp"
            executed["yes"] = True

        defs = Definitions(
            assets=[my_other_output_asset],
            resources={"wrapper": OutputDirWrapperResource(output_dir=OutputDirResource())},
        )

        assert defs.get_implicit_global_asset_job_def().execute_in_process().success
        assert executed["yes"]


def test_bind_top_level_resource_sensor_multi_job() -> None:
    executed = {}

    class FooResource(ConfigurableResource):
        my_str: str

    @op
    def hello_world_op(foo: FooResource):
        assert foo.my_str == "foo"
        executed["yes"] = True

    @job()
    def hello_world_job():
        hello_world_op()

    @job
    def hello_world_job_2():
        hello_world_op()

    @sensor(jobs=[hello_world_job, hello_world_job_2])
    def hello_world_sensor(context):
        return RunRequest(run_key="foo")

    Definitions(
        sensors=[hello_world_sensor],
        jobs=[hello_world_job, hello_world_job_2],
        resources={
            "foo": FooResource(my_str="foo"),
        },
    )


def test_secret_str() -> None:
    class ResourceWithSecret(ConfigurableResource):
        a_secret: SecretStr

    @asset
    def my_asset(my_resource: ResourceWithSecret):
        return my_resource.a_secret.get_secret_value()

    assert my_asset(ResourceWithSecret(a_secret="foo")) == "foo"  # type: ignore
    assert my_asset(my_resource=ResourceWithSecret(a_secret="foo")) == "foo"  # type: ignore

    defs = Definitions(
        assets=[my_asset], resources={"my_resource": ResourceWithSecret(a_secret="foo")}
    )
    result = defs.get_implicit_global_asset_job_def().execute_in_process()

    assert result.success
    assert result.output_for_node("my_asset") == "foo"


def test_secret_str_runtime_config() -> None:
    class ResourceWithSecret(ConfigurableResource):
        a_secret: SecretStr

    @asset
    def my_asset(my_resource: ResourceWithSecret):
        return my_resource.a_secret.get_secret_value()

    defs = Definitions(
        assets=[my_asset], resources={"my_resource": ResourceWithSecret.configure_at_launch()}
    )
    result = defs.get_implicit_global_asset_job_def().execute_in_process(
        run_config={"resources": {"my_resource": {"config": {"a_secret": "bar"}}}}
    )

    assert result.success
    assert result.output_for_node("my_asset") == "bar"


def test_secret_str_from_env() -> None:
    class ResourceWithSecret(ConfigurableResource):
        a_secret: SecretStr

    @asset
    def my_asset(my_resource: ResourceWithSecret):
        return my_resource.a_secret.get_secret_value()

    with environ(
        {
            "ENV_VARIABLE_FOR_TEST": "baz",
        }
    ):
        defs = Definitions(
            assets=[my_asset],
            resources={"my_resource": ResourceWithSecret(a_secret=EnvVar("ENV_VARIABLE_FOR_TEST"))},
        )
        result = defs.get_implicit_global_asset_job_def().execute_in_process()

        assert result.success
        assert result.output_for_node("my_asset") == "baz"


def test_secret_str_nested() -> None:
    class ResourceWithSecret(ConfigurableResource):
        a_secret: SecretStr

    class OuterResourceWithSecret(ConfigurableResource):
        inner: ResourceWithSecret
        another_secret: SecretStr

    @asset
    def my_asset(my_resource: OuterResourceWithSecret):
        return (
            my_resource.another_secret.get_secret_value()
            + my_resource.inner.a_secret.get_secret_value()
        )

    assert my_asset(OuterResourceWithSecret(inner=ResourceWithSecret(a_secret="foo"), another_secret="bar")) == "barfoo"  # type: ignore
    assert my_asset(my_resource=OuterResourceWithSecret(inner=ResourceWithSecret(a_secret="foo"), another_secret="bar")) == "barfoo"  # type: ignore

    defs = Definitions(
        assets=[my_asset],
        resources={
            "my_resource": OuterResourceWithSecret(
                inner=ResourceWithSecret(a_secret="foo"), another_secret="bar"
            )
        },
    )
    result = defs.get_implicit_global_asset_job_def().execute_in_process()

    assert result.success
    assert result.output_for_node("my_asset") == "barfoo"
