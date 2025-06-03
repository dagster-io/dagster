import inspect
from textwrap import dedent
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
from dagster.components.testing import scaffold_defs_sandbox


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


def test_simulated_udf_for_dep() -> None:
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


def test_more_real_udf_for_dep() -> None:
    def code_for_execute_py():
        from typing import Annotated

        from dagster import MaterializeResult
        from dagster.components.component.template_vars import template_var
        from dagster.components.lib.executable_component.component import (
            Upstream,
            materialize_result_with_value,
        )

        def return_hello_execute_fn(context) -> MaterializeResult:
            return materialize_result_with_value(value="hello")

        def hello_world_execute_fn(
            context, foo_bar: Annotated[str, Upstream(asset_key="return_hello")]
        ):
            return materialize_result_with_value(value=foo_bar + " world")

        @template_var
        def deps_from_execute_fn():
            def _deps_for_key(asset_key: str):
                if asset_key == "return_hello":
                    return []
                elif asset_key == "hello_world_asset":
                    return ["return_hello"]
                else:
                    raise ValueError(f"Unknown asset key: {asset_key}")

            return _deps_for_key

    with scaffold_defs_sandbox(component_cls=ExecutableComponent) as sandbox:
        execute_fn_content = dedent(
            inspect.getsource(code_for_execute_py).split("def code_for_execute_py():\n", 1)[1]
        )
        execute_path = sandbox.defs_folder_path / "execute.py"
        file_content = dedent(execute_fn_content)
        execute_path.write_text(file_content)
        with sandbox.load_all(
            component_bodies=[
                {
                    "type": "dagster.components.lib.executable_component.component.ExecutableComponent",
                    "attributes": {
                        "execute_fn": ".execute.return_hello_execute_fn",
                        "assets": [{"key": "return_hello"}],
                    },
                    "template_vars_module": ".execute",
                },
                {
                    "type": "dagster.components.lib.executable_component.component.ExecutableComponent",
                    "attributes": {
                        "execute_fn": ".execute.hello_world_execute_fn",
                        "assets": [
                            {
                                "key": "hello_world_asset",
                                "deps": "{{ deps_from_execute_fn('hello_world_asset') }}",
                            }
                        ],
                    },
                    "template_vars_module": ".execute",
                },
            ]
        ) as component_def_tuples:
            return_hello_component, defs_one = component_def_tuples[0]
            assert isinstance(return_hello_component, ExecutableComponent)
            assert return_hello_component.execute_fn.__name__ == "return_hello_execute_fn"

            hello_world_component, defs_two = component_def_tuples[1]
            assert isinstance(hello_world_component, ExecutableComponent)
            assert hello_world_component.execute_fn.__name__ == "hello_world_execute_fn"

            defs = Definitions.merge(defs_one, defs_two)

            io_manager = InMemoryIOManager()
            result = materialize(
                [defs.get_assets_def("hello_world_asset"), defs.get_assets_def("return_hello")],
                resources={"io_manager": io_manager},
            )
            assert result.success
            assert value_for_asset(result, "return_hello") == "hello"
            assert value_for_asset(result, "hello_world_asset") == "hello world"
