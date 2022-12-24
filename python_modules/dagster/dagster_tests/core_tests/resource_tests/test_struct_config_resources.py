import sys
from abc import ABC, abstractmethod
from typing import Any, Callable

import pytest
from pydantic import ValidationError

from dagster import asset, job, op, resource
from dagster._config.structured_config import (
    Resource,
    StructuredConfigIOManagerAdapter,
    StructuredResourceAdapter,
)
from dagster._core.definitions.assets_job import build_assets_job
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.resource_output import ResourceOutput
from dagster._core.execution.context.input import InputContext
from dagster._core.execution.context.output import OutputContext
from dagster._core.storage.io_manager import IOManager, IOManagerDefinition, io_manager
from dagster._utils.cached_method import cached_method


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

    class WriterResource(Resource, ABC):
        @abstractmethod
        def output(self, text: str) -> None:
            pass

    class PrefixedWriterResource(WriterResource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    class RepetitiveWriterResource(WriterResource):
        repetitions: int

        def output(self, text: str) -> None:
            out_txt.append(f"{text} " * self.repetitions)

    @op
    def hello_world_op(writer: WriterResource):
        writer.output("hello, world!")

    # Can't instantiate abstract class
    with pytest.raises(TypeError):
        WriterResource()  # pylint: disable=abstract-class-instantiated

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
        resource_with_cleanup_1: ResourceOutput[bool], resource_with_cleanup_2: ResourceOutput[bool]
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

    counts = {"num_calls_to_factory": 0}

    @resource(config_schema={"prefix": str})
    def writer_resource(context):
        counts["num_calls_to_factory"] += 1
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
    def hello_world_op(writer: ResourceOutput[Callable[[str], None]]):
        writer("hello, world!")

    @job(resource_defs={"writer": WriterResource(prefix="")})
    def no_prefix_job():
        hello_world_op()

    assert counts["num_calls_to_factory"] == 0

    assert no_prefix_job.execute_in_process().success
    assert out_txt == ["hello, world!"]
    assert counts["num_calls_to_factory"] == 1

    out_txt.clear()

    @job(resource_defs={"writer": WriterResource(prefix="greeting: ")})
    def prefix_job():
        hello_world_op()

    assert prefix_job.execute_in_process().success
    assert out_txt == ["greeting: hello, world!"]


def test_wrapping_io_manager_with_context():
    class APreexistingIOManager(IOManager):
        def __init__(self, a_str: str):
            self.a_str = a_str

        def load_input(self, context: "InputContext") -> Any:
            pass

        def handle_output(self, context: "OutputContext", obj: Any) -> None:
            pass

    counts = {"num_calls_to_factory": 0}

    @io_manager(config_schema={"a_str": str})
    def a_preexisting_io_manager(context):
        counts["num_calls_to_factory"] += 1
        return APreexistingIOManager(context.resource_config["a_str"])

    class TypedPreexistingIOManager(StructuredConfigIOManagerAdapter):
        a_str: str

        @property
        def wrapped_io_manager_def(self) -> IOManagerDefinition:
            return a_preexisting_io_manager

    executed = {}

    @asset
    def an_asset(context):
        assert context.resources.io_manager.a_str == "foo"
        executed["yes"] = True

    defs = Definitions(
        assets=[an_asset], resources={"io_manager": TypedPreexistingIOManager(a_str="foo")}
    )

    assert counts["num_calls_to_factory"] == 0

    assert defs.get_implicit_global_asset_job_def().execute_in_process().success

    assert counts["num_calls_to_factory"] == 1

    assert executed["yes"]


def test_wrapping_io_manager_no_context():
    class APreexistingIOManager(IOManager):
        def load_input(self, context: "InputContext") -> Any:
            pass

        def handle_output(self, context: "OutputContext", obj: Any) -> None:
            pass

    counts = {"num_calls_to_factory": 0}

    @io_manager
    def a_preexisting_io_manager_no_context():
        counts["num_calls_to_factory"] += 1
        return APreexistingIOManager()

    class WrapAPreexistingIOManager(StructuredConfigIOManagerAdapter):
        @property
        def wrapped_io_manager_def(self) -> IOManagerDefinition:
            return a_preexisting_io_manager_no_context

    executed = {}

    @asset
    def an_asset(_):
        executed["yes"] = True

    defs = Definitions(assets=[an_asset], resources={"io_manager": WrapAPreexistingIOManager()})

    assert counts["num_calls_to_factory"] == 0

    assert defs.get_implicit_global_asset_job_def().execute_in_process().success

    assert counts["num_calls_to_factory"] == 1

    assert executed["yes"]
