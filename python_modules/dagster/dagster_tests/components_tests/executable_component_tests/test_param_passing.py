from typing import Annotated, Callable

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.result import MaterializeResult
from dagster._core.storage.mem_io_manager import InMemoryIOManager
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.executable_component.component import (
    ExecutableComponent,
    Upstream,
    get_upstream_args,
    materialize_result_with_value,
    value_for_asset,
)


def test_upstream_args_with_annotated_type_matching_names() -> None:
    def return_hello_execute_fn(context) -> MaterializeResult:
        return materialize_result_with_value(value="hello")

    return_hello_component = ExecutableComponent(
        execute_fn=return_hello_execute_fn, assets=[AssetSpec(key="return_hello")]
    )

    def hello_world_execute_fn(
        context, return_hello: Annotated[str, Upstream(asset_key="return_hello")]
    ) -> MaterializeResult:
        return materialize_result_with_value(value=return_hello + " world")

    hello_world_component = ExecutableComponent(
        execute_fn=hello_world_execute_fn,
        assets=[AssetSpec(key="hello_world_asset", deps=["return_hello"])],
    )

    defs = Definitions.merge(
        hello_world_component.build_defs(ComponentLoadContext.for_test()),
        return_hello_component.build_defs(ComponentLoadContext.for_test()),
    )

    io_manager = InMemoryIOManager()
    result = materialize(
        [defs.get_assets_def("hello_world_asset"), defs.get_assets_def("return_hello")],
        resources={"io_manager": io_manager},
    )
    assert result.success


def test_upstream_args_with_annotated_type_different_names() -> None:
    def return_hello_execute_fn(context) -> MaterializeResult:
        return materialize_result_with_value(value="hello")

    return_hello_component = ExecutableComponent(
        execute_fn=return_hello_execute_fn, assets=[AssetSpec(key="return_hello")]
    )

    def hello_world_execute_fn(
        context, foo_bar: Annotated[str, Upstream(asset_key="return_hello")]
    ) -> MaterializeResult:
        return materialize_result_with_value(value=foo_bar + " world")

    hello_world_component = ExecutableComponent(
        execute_fn=hello_world_execute_fn,
        assets=[AssetSpec(key="hello_world_asset", deps=["return_hello"])],
    )

    defs = Definitions.merge(
        hello_world_component.build_defs(ComponentLoadContext.for_test()),
        return_hello_component.build_defs(ComponentLoadContext.for_test()),
    )

    io_manager = InMemoryIOManager()
    result = materialize(
        [defs.get_assets_def("hello_world_asset"), defs.get_assets_def("return_hello")],
        resources={"io_manager": io_manager},
    )
    assert result.success
    assert result.output_for_node("return_hello_execute_fn", output_name="return_hello") == "hello"
    assert (
        result.output_for_node("hello_world_execute_fn", output_name="hello_world_asset")
        == "hello world"
    )


# I want this to be a udf with execute_fn in scope
def get_deps(execute_fn: Callable) -> list[AssetKey]:
    return [
        upstream_param_info.asset_key
        if upstream_param_info.asset_key
        else AssetKey(upstream_param_info.param_name)
        for upstream_param_info in get_upstream_args(execute_fn).values()
    ]


def test_udf_for_dep() -> None:
    def return_hello_execute_fn(context) -> MaterializeResult:
        return materialize_result_with_value(value="hello")

    return_hello_component = ExecutableComponent(
        execute_fn=return_hello_execute_fn, assets=[AssetSpec(key="return_hello")]
    )

    def hello_world_execute_fn(
        context, foo_bar: Annotated[str, Upstream(asset_key="return_hello")]
    ) -> MaterializeResult:
        return materialize_result_with_value(value=foo_bar + " world")

    hello_world_component = ExecutableComponent(
        execute_fn=hello_world_execute_fn,
        assets=[AssetSpec(key="hello_world_asset", deps=get_deps(hello_world_execute_fn))],
    )

    defs = Definitions.merge(
        hello_world_component.build_defs(ComponentLoadContext.for_test()),
        return_hello_component.build_defs(ComponentLoadContext.for_test()),
    )

    io_manager = InMemoryIOManager()
    result = materialize(
        [defs.get_assets_def("hello_world_asset"), defs.get_assets_def("return_hello")],
        resources={"io_manager": io_manager},
    )
    assert result.success
    assert value_for_asset(result, "return_hello") == "hello"
    assert value_for_asset(result, "hello_world_asset") == "hello world"
