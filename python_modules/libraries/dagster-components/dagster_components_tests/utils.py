import textwrap
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import AbstractSet, Optional  # noqa: UP035

from dagster import AssetKey, DagsterInstance
from dagster._utils import pushd
from dagster_components.core.component import (
    Component,
    ComponentDeclNode,
    ComponentLoadContext,
    ComponentTypeRegistry,
)


def registry() -> ComponentTypeRegistry:
    return ComponentTypeRegistry.from_entry_point_discovery()


def script_load_context(decl_node: Optional[ComponentDeclNode] = None) -> ComponentLoadContext:
    return ComponentLoadContext.for_test(registry=registry(), decl_node=decl_node)


def get_asset_keys(component: Component) -> AbstractSet[AssetKey]:
    return {
        key
        for key in component.build_defs(ComponentLoadContext.for_test())
        .get_asset_graph()
        .get_all_asset_keys()
    }


def assert_assets(component: Component, expected_assets: int) -> None:
    defs = component.build_defs(ComponentLoadContext.for_test())
    assert len(defs.get_asset_graph().get_all_asset_keys()) == expected_assets
    result = defs.get_implicit_global_asset_job_def().execute_in_process(
        instance=DagsterInstance.ephemeral()
    )
    assert result.success


def generate_component_lib_pyproject_toml(name: str, is_code_location: bool = False) -> str:
    pkg_name = name.replace("-", "_")
    base = textwrap.dedent(f"""
        [build-system]
        requires = ["setuptools", "wheel"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "{name}"
        version = "0.1.0"
        dependencies = [
            "dagster-components",
        ]

        [project.entry-points]
        "dagster.components" = {{ {pkg_name} = "{pkg_name}.lib"}}
    """)
    if is_code_location:
        return base + textwrap.dedent("""
        [tool.dagster]
        module_name = "{ pkg_name }.definitions"
        project_name = "{ pkg_name }"
        """)
    else:
        return base


@contextmanager
def temp_code_location_bar() -> Iterator[None]:
    with TemporaryDirectory() as tmpdir, pushd(tmpdir):
        Path("bar/bar/lib").mkdir(parents=True)
        Path("bar/bar/components").mkdir(parents=True)
        with open("bar/pyproject.toml", "w") as f:
            f.write(generate_component_lib_pyproject_toml("bar", is_code_location=True))
        Path("bar/bar/__init__.py").touch()
        Path("bar/bar/definitions.py").touch()
        Path("bar/bar/lib/__init__.py").touch()

        with pushd("bar"):
            yield
