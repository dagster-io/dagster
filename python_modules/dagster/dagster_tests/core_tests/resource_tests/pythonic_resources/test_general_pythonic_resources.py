import enum
import sys
from abc import ABC, abstractmethod
from typing import List, Mapping, Optional

import mock
import pytest
from dagster import (
    AssetExecutionContext,
    Config,
    ConfigurableIOManagerFactory,
    ConfigurableLegacyIOManagerAdapter,
    ConfigurableResource,
    DagsterInstance,
    Definitions,
    IAttachDifferentObjectToOpContext,
    InitResourceContext,
    IOManager,
    IOManagerDefinition,
    ResourceDependency,
    ResourceParam,
    RunConfig,
    asset,
    build_init_resource_context,
    io_manager,
    job,
    materialize,
    op,
    resource,
)
from dagster._check import CheckError
from dagster._config.pythonic_config import ConfigurableResourceFactory
from dagster._core.definitions.assets_job import build_assets_job
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
)
from dagster._utils.cached_method import cached_method
from pydantic import (
    Field as PyField,
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
    def an_asset(context: AssetExecutionContext):
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
    def another_asset(context: AssetExecutionContext):
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


def test_basic_enum_override_with_resource_instance() -> None:
    class BasicEnum(enum.Enum):
        A = "a_value"
        B = "b_value"

    setup_executed = {}

    class MyResource(ConfigurableResource):
        my_enum: BasicEnum

        def setup_for_execution(self, context: InitResourceContext) -> None:
            setup_executed["yes"] = True
            assert context.resource_config["my_enum"] in [BasicEnum.A.value, BasicEnum.B.value]

    @asset
    def asset_with_resource(context, my_resource: MyResource):
        return my_resource.my_enum.value

    result_one = materialize(
        [asset_with_resource],
        resources={"my_resource": MyResource(my_enum=BasicEnum.A)},
    )
    assert result_one.success
    assert result_one.output_for_node("asset_with_resource") == "a_value"
    assert setup_executed["yes"]

    setup_executed.clear()

    result_two = materialize(
        [asset_with_resource],
        resources={"my_resource": MyResource(my_enum=BasicEnum.A)},
        run_config={"resources": {"my_resource": {"config": {"my_enum": "B"}}}},
    )

    assert result_two.success
    assert result_two.output_for_node("asset_with_resource") == "b_value"
    assert setup_executed["yes"]


def test_basic_enum_override_with_resource_configured_at_launch() -> None:
    class AnotherEnum(enum.Enum):
        A = "a_value"
        B = "b_value"

    class MyResource(ConfigurableResource):
        my_enum: AnotherEnum

    @asset
    def asset_with_resource(context, my_resource: MyResource):
        return my_resource.my_enum.value

    result_one = materialize(
        [asset_with_resource],
        resources={"my_resource": MyResource.configure_at_launch()},
        run_config={"resources": {"my_resource": {"config": {"my_enum": "B"}}}},
    )

    assert result_one.success
    assert result_one.output_for_node("asset_with_resource") == "b_value"

    result_two = materialize(
        [asset_with_resource],
        resources={"my_resource": MyResource.configure_at_launch(my_enum=AnotherEnum.A)},
        run_config={"resources": {"my_resource": {"config": {"my_enum": "B"}}}},
    )

    assert result_two.success
    assert result_two.output_for_node("asset_with_resource") == "b_value"


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
    ContextUsingResource().with_replaced_resource_context(
        build_init_resource_context()
    ).access_context()

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
                .with_replaced_resource_context(build_init_resource_context(instance=instance))
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


def test_telemetry_custom_resource():
    class MyResource(ConfigurableResource):
        my_value: str

        @classmethod
        def _is_dagster_maintained(cls) -> bool:
            return False

    assert not MyResource(my_value="foo")._is_dagster_maintained()  # noqa: SLF001


def test_telemetry_dagster_resource():
    class MyResource(ConfigurableResource):
        my_value: str

        @classmethod
        def _is_dagster_maintained(cls) -> bool:
            return True

    assert MyResource(my_value="foo")._is_dagster_maintained()  # noqa: SLF001


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
