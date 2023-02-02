import json
import os
import re
import subprocess
import sys
import tempfile
from abc import ABC, abstractmethod
from typing import Any, Callable, List

import pytest
from dagster import IOManager, asset, job, op, resource
from dagster._check import CheckError
from dagster._config.field import Field
from dagster._config.structured_config import (
    Resource,
    ResourceDependency,
    StructuredConfigIOManagerBase,
    StructuredIOManagerAdapter,
    StructuredResourceAdapter,
)
from dagster._core.definitions.assets_job import build_assets_job
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.resource_output import Injected
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.execution.context.init import InitResourceContext
from dagster._core.storage.io_manager import IOManagerDefinition, io_manager
from dagster._utils.cached_method import cached_method
from pydantic import ValidationError


def test_basic_structured_resource():
    out_txt = []

    class WriterResource(Resource):
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
    class MyResource(Resource):
        foo: int

    with pytest.raises(
        ValidationError,
    ):
        MyResource(foo="why")


@pytest.mark.skipif(sys.version_info < (3, 8), reason="requires python3.8")
def test_caching_within_resource():
    called = {"greeting": 0, "get_introduction": 0}

    from functools import cached_property

    class GreetingResource(Resource):
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

    class Writer(Resource, ABC):
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

    class ResourceWithCleanup(Resource):
        idx: int

        def create_object_to_pass_to_user_code(self, context):
            called.append(f"creation_{self.idx}")
            yield True
            called.append(f"cleanup_{self.idx}")

    @op
    def check_resource_created(
        resource_with_cleanup_1: Injected[bool], resource_with_cleanup_2: Injected[bool]
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

    class WriterResource(StructuredResourceAdapter):
        prefix: str

        @property
        def wrapped_resource(self) -> ResourceDefinition:
            return writer_resource

    @op
    def hello_world_op(writer: Injected[Callable[[str], None]]):
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

    class AdapterForIOManager(StructuredIOManagerAdapter):
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
    class AnIOManagerFactory(StructuredConfigIOManagerBase):
        a_config_value: str

        def create_io_manager_to_pass_to_user_code(self, _) -> IOManager:
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

    class WriterResource(Resource):
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


def test_nested_resources():
    out_txt = []

    class Writer(Resource, ABC):
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
    class AWSCredentialsResource(Resource):
        username: str
        password: str

    class S3Resource(Resource):
        aws_credentials: AWSCredentialsResource
        bucket_name: str

    class EC2Resource(Resource):
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
    class AWSCredentialsResource(Resource):
        username: str
        password: str

    class S3Resource(Resource):
        aws_credentials: AWSCredentialsResource
        bucket_name: str

    class EC2Resource(Resource):
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
    class CredentialsResource(Resource):
        username: str
        password: str

    class DBConfigResource(Resource):
        creds: CredentialsResource
        host: str
        database: str

    class DBResource(Resource):
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
    class StringResource(Resource[str]):
        a_string: str

        def create_object_to_pass_to_user_code(self, context) -> str:
            return self.a_string

    class MyResource(Resource):
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

    class PostfixWriterResource(Resource[Callable[[str], None]]):
        writer: ResourceDependency[Callable[[str], None]]
        postfix: str

        def create_object_to_pass_to_user_code(self, context) -> Callable[[str], None]:
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

    class PostfixWriterResource(Resource[Callable[[str], None]]):
        writer: ResourceDependency[Callable[[str], None]]
        postfix: str

        def create_object_to_pass_to_user_code(self, context) -> Callable[[str], None]:
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

    class PostfixWriterResource(Resource[Callable[[str], None]]):
        writer: ResourceDependency[Callable[[str], None]]
        postfix: str

        def create_object_to_pass_to_user_code(self, context) -> Callable[[str], None]:
            def output(text: str):
                self.writer(f"{text}{self.postfix}")

            return output

    @asset
    def my_asset(writer: PostfixWriterResource):
        writer("foo")
        writer("bar")

    with pytest.raises(
        CheckError,
        match="Any partially configured, nested resources must be specified to Definitions",
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


def test_type_signatures_constructor_nested_resource():
    with tempfile.TemporaryDirectory() as tempdir:
        filename = os.path.join(tempdir, "test.py")

        with open(filename, "w") as f:
            f.write(
                """
from dagster._config.structured_config import Resource

class InnerResource(Resource):
    a_string: str

class OuterResource(Resource):
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


def test_type_signatures_config_at_launch():
    with tempfile.TemporaryDirectory() as tempdir:
        filename = os.path.join(tempdir, "test.py")

        with open(filename, "w") as f:
            f.write(
                """
from dagster._config.structured_config import Resource

class MyResource(Resource):
    a_string: str

reveal_type(MyResource.configure_at_launch())
"""
            )

        pyright_out = get_pyright_reveal_type_output(filename)
        mypy_out = get_mypy_type_output(filename)

        # Ensure partial resource is correctly parameterized
        assert pyright_out[0] == "PartialResource[MyResource]"
        assert mypy_out[0].endswith("PartialResource[test.MyResource]")


def test_type_signatures_constructor_resource_dependency():
    with tempfile.TemporaryDirectory() as tempdir:
        filename = os.path.join(tempdir, "test.py")

        with open(filename, "w") as f:
            f.write(
                """
from dagster._config.structured_config import Resource, ResourceDependency

class StringDependentResource(Resource):
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
            == "(self: StringDependentResource, a_string: Resource[str] | PartialResource[str] |"
            " ResourceDefinition | str) -> None"
        )

        # Ensure that the retrieved type is str
        assert pyright_out[1] == "str"
        assert mypy_out[1] == "builtins.str"
