import json
import os
import re
import subprocess
import sys
import tempfile
from abc import ABC, abstractmethod
from typing import Any, Callable, List, Mapping

import pytest
from dagster import IOManager, ResourceByKey, asset, job, op, resource
from dagster._check import CheckError
from dagster._config.field import Field
from dagster._config.field_utils import EnvVar
from dagster._config.structured_config import (
    Config,
    ConfigurableIOManagerFactory,
    ConfigurableLegacyIOManagerAdapter,
    ConfigurableLegacyResourceAdapter,
    ConfigurableResource,
    ResourceDependency,
)
from dagster._core.definitions.assets_job import build_assets_job
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.resource_annotation import Resource
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.run_config import RunConfig
from dagster._core.errors import DagsterInvalidConfigError
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.execution.context.init import InitResourceContext
from dagster._core.storage.io_manager import IOManagerDefinition, io_manager
from dagster._core.test_utils import environ
from dagster._utils.cached_method import cached_method


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


def test_invalid_config():
    class MyResource(ConfigurableResource):
        foo: int

    with pytest.raises(
        DagsterInvalidConfigError,
    ):
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
        Writer()  # pylint: disable=abstract-class-instantiated

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

    class ResourceWithCleanup(ConfigurableResource):
        idx: int

        def create_resource(self, context):
            called.append(f"creation_{self.idx}")
            yield True
            called.append(f"cleanup_{self.idx}")

    @op
    def check_resource_created(
        resource_with_cleanup_1: Resource[bool], resource_with_cleanup_2: Resource[bool]
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


def test_wrapping_function_resource():
    out_txt = []

    @resource(config_schema={"prefix": str})
    def writer_resource(context):
        prefix = context.resource_config["prefix"]

        def output(text: str) -> None:
            out_txt.append(f"{prefix}{text}")

        return output

    class WriterResource(ConfigurableLegacyResourceAdapter):
        prefix: str

        @property
        def wrapped_resource(self) -> ResourceDefinition:
            return writer_resource

    @op
    def hello_world_op(writer: Resource[Callable[[str], None]]):
        writer("hello, world!")

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
            """Implement as one would implement a @io_manager decorator function"""
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
    class StringResource(ConfigurableResource[str]):
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

    class PostfixWriterResource(ConfigurableResource[Callable[[str], None]]):
        writer: ResourceDependency[Callable[[str], None]]
        postfix: str

        def create_resource(self, context) -> Callable[[str], None]:
            def output(text: str):
                self.writer(f"{text}{self.postfix}")

            return output

    @asset
    def my_asset(writer: PostfixWriterResource):
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

    class PostfixWriterResource(ConfigurableResource[Callable[[str], None]]):
        writer: ResourceDependency[Callable[[str], None]]
        postfix: str

        def create_resource(self, context) -> Callable[[str], None]:
            def output(text: str):
                self.writer(f"{text}{self.postfix}")

            return output

    @asset
    def my_asset(writer: PostfixWriterResource):
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

    class PostfixWriterResource(ConfigurableResource[Callable[[str], None]]):
        writer: ResourceDependency[Callable[[str], None]]
        postfix: str

        def create_resource(self, context) -> Callable[[str], None]:
            def output(text: str):
                self.writer(f"{text}{self.postfix}")

            return output

    @asset
    def my_asset(writer: PostfixWriterResource):
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
from dagster._config.structured_config import ConfigurableResource

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
        assert pyright_out[0] == "(self: InnerResource, a_string: str) -> None"
        assert (
            pyright_out[1]
            == "(self: OuterResource, inner: InnerResource | PartialResource[InnerResource],"
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
from dagster._config.structured_config import ConfigurableResource

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
from dagster._config.structured_config import ConfigurableResource, ResourceDependency

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
            == "(self: StringDependentResource, a_string: ConfigurableResource[str] |"
            " PartialResource[str] | ResourceDefinition | str) -> None"
        )

        # Ensure that the retrieved type is str
        assert pyright_out[1] == "str"
        assert mypy_out[1] == "builtins.str"


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


def test_resource_by_key() -> None:
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
    json_writer_resource = JsonWriterResource(indent=2, base_writer=ResourceByKey("base_writer"))

    assert (
        Definitions(
            assets=[hello_world_asset],
            resources={
                "writer": json_writer_resource,
                "base_writer": writer_resource,
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
        indent=2, base_writer=ResourceByKey("base_writer")
    )

    assert (
        Definitions(
            assets=[hello_world_asset],
            resources={
                "writer": prefixed_json_writer_resource,
                "base_writer": prefixed_writer_resource,
            },
        )
        .get_implicit_global_asset_job_def()
        .execute_in_process()
        .success
    )

    assert out_txt == ['greeting: {\n  "hello": "world"\n}']


def test_resource_by_key_function_resource() -> None:
    out_txt = []

    @resource
    def writer_resource(context):
        def output(text: str) -> None:
            out_txt.append(text)

        return output

    class PostfixWriterResource(ConfigurableResource[Callable[[str], None]]):
        writer: ResourceDependency[Callable[[str], None]]
        postfix: str

        def create_resource(self, context) -> Callable[[str], None]:
            def output(text: str):
                self.writer(f"{text}{self.postfix}")

            return output

    @asset
    def my_asset(writer: PostfixWriterResource):
        writer("foo")
        writer("bar")

    defs = Definitions(
        assets=[my_asset],
        resources={
            "writer": PostfixWriterResource(writer=ResourceByKey("base_writer"), postfix="!"),
            "base_writer": writer_resource,
        },
    )

    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
    assert out_txt == ["foo!", "bar!"]
