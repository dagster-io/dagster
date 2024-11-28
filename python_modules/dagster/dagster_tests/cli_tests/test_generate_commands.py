import importlib
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional, Type

from click.testing import CliRunner
from dagster import AssetExecutionContext, AssetKey, Definitions, PipesSubprocessClient, asset
from dagster._components import (
    CodeLocationProjectContext,
    Component,
    ComponentInitContext,
    ComponentLoadContext,
    ComponentRegistry,
)
from dagster._components.cli.generate import (
    generate_code_location_command,
    generate_component_command,
    generate_component_type_command,
    generate_deployment_command,
)
from dagster._utils import pushd
from pydantic import BaseModel, TypeAdapter
from typing_extensions import Self


def _ensure_cwd_on_sys_path():
    if sys.path[0] != "":
        sys.path.insert(0, "")


def _assert_module_imports(module_name: str):
    _ensure_cwd_on_sys_path()
    assert importlib.import_module(module_name)


# ########################
# ##### EXAMPLE COMPONENT TYPE
# ########################


class BazParams(BaseModel):
    asset_key: str
    resource_key: str


_SAMPLE_PIPES_SCRIPT = """
from dagster_pipes import open_dagster_pipes

context = open_dagster_pipes()
context.report_asset_materialization({"metakey": "metaval"})
"""


class Baz(Component):
    params_schema = Optional[BazParams]

    @classmethod
    def generate_files(cls, params: Any):
        with open("sample.py", "w") as f:
            f.write(_SAMPLE_PIPES_SCRIPT)

    @classmethod
    def from_component_params(
        cls, init_context: ComponentInitContext, component_params: object
    ) -> Self:
        loaded_params = TypeAdapter(cls.params_schema).validate_python(component_params)
        return cls(
            key=AssetKey.from_user_string(loaded_params.asset_key),  # type: ignore
            resource_key=loaded_params.resource_key,  # type: ignore
        )

    def __init__(self, key: AssetKey, resource_key: str):
        self.key = key
        self.resource_key = resource_key

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @asset(key=self.key, required_resource_keys={self.resource_key})
        def dummy(context: AssetExecutionContext):
            context.resources[self.resource_key].run(
                context=context, command=["python", "sample.py"]
            )

        return Definitions(assets=[dummy], resources={self.resource_key: PipesSubprocessClient()})


########################


@contextmanager
def isolated_example_deployment_foo(runner: CliRunner) -> Iterator[None]:
    with runner.isolated_filesystem():
        runner.invoke(generate_deployment_command, ["foo"])
        with pushd("foo"):
            yield


@contextmanager
def isolated_example_code_location_bar(runner: CliRunner) -> Iterator[None]:
    with isolated_example_deployment_foo(runner), clean_module_cache("bar"):
        runner.invoke(generate_code_location_command, ["bar"])
        with pushd("code_locations/bar"):
            yield


@contextmanager
def global_component_types(*components: Type[Component]) -> Iterator[None]:
    try:
        global_registry = ComponentRegistry.get_global()
        for component in components:
            global_registry.register(component.registered_name(), component)
        yield
    finally:
        for component in components:
            if global_registry.has(component.registered_name()):
                global_registry.unregister(component.registered_name())


@contextmanager
def clean_module_cache(module_name: str):
    prefix = f"{module_name}."
    keys_to_del = {
        key for key in sys.modules.keys() if key == module_name or key.startswith(prefix)
    }
    for key in keys_to_del:
        del sys.modules[key]
    yield


def test_generate_deployment_command_success():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(generate_deployment_command, ["foo"])
        assert result.exit_code == 0
        assert Path("foo").exists()
        assert Path("foo/.github").exists()
        assert Path("foo/.github/workflows").exists()
        assert Path("foo/.github/workflows/dagster-cloud-deploy.yaml").exists()
        assert Path("foo/dagster_cloud.yaml").exists()
        assert Path("foo/code_locations").exists()


def test_generate_deployment_command_already_exists_fails():
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("foo")
        result = runner.invoke(generate_deployment_command, ["foo"])
        assert result.exit_code != 0
        assert "already exists" in result.output


def test_generate_code_location_success():
    runner = CliRunner()
    with isolated_example_deployment_foo(runner):
        result = runner.invoke(generate_code_location_command, ["bar"])
        assert result.exit_code == 0
        assert Path("code_locations/bar").exists()
        assert Path("code_locations/bar/bar").exists()
        assert Path("code_locations/bar/bar/lib").exists()
        assert Path("code_locations/bar/bar/components").exists()
        assert Path("code_locations/bar/bar_tests").exists()
        assert Path("code_locations/bar/pyproject.toml").exists()


def test_generate_code_location_outside_deployment_fails():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(generate_code_location_command, ["bar"])
        assert result.exit_code != 0
        assert "must be run inside a Dagster deployment project" in result.output


def test_generate_code_location_already_exists_fails():
    runner = CliRunner()
    with isolated_example_deployment_foo(runner):
        result = runner.invoke(generate_code_location_command, ["bar"])
        assert result.exit_code == 0
        result = runner.invoke(generate_code_location_command, ["bar"])
        assert result.exit_code != 0
        assert "already exists" in result.output


def test_generate_component_type_success():
    runner = CliRunner()
    with isolated_example_code_location_bar(runner):
        result = runner.invoke(generate_component_type_command, ["baz"])
        assert result.exit_code == 0
        assert Path("bar/lib/baz.py").exists()
        _assert_module_imports("bar.lib.baz")
        context = CodeLocationProjectContext.from_path(os.getcwd())
        assert context.has_component_type("baz")


def test_generate_component_type_outside_code_location_fails():
    runner = CliRunner()
    with isolated_example_deployment_foo(runner):
        result = runner.invoke(generate_component_type_command, ["baz"])
        assert result.exit_code != 0
        assert "must be run inside a Dagster code location project" in result.output


def test_generate_component_type_already_exists_fails():
    runner = CliRunner()
    with isolated_example_code_location_bar(runner):
        result = runner.invoke(generate_component_type_command, ["baz"])
        assert result.exit_code == 0
        result = runner.invoke(generate_component_type_command, ["baz"])
        assert result.exit_code != 0
        assert "already exists" in result.output


def test_generate_component_success():
    runner = CliRunner()
    _ensure_cwd_on_sys_path()
    with isolated_example_code_location_bar(runner), global_component_types(Baz):
        params = json.dumps({"asset_key": "alpha", "resource_key": "alpha_client"})
        result = runner.invoke(generate_component_command, ["baz", "alpha", "--params", params])
        assert result.exit_code == 0
        assert Path("bar/components/alpha").exists()
        assert Path("bar/components/alpha/defs.yaml").exists()
        with open("bar/components/alpha/defs.yaml") as f:
            content = f.read()
            assert "component_type: baz" in content
            assert "asset_key: alpha" in content
        assert Path("bar/components/alpha/sample.py").exists()


def test_generate_component_outside_code_location_fails():
    runner = CliRunner()
    with isolated_example_deployment_foo(runner):
        result = runner.invoke(generate_component_command, ["baz", "alpha"])
        assert result.exit_code != 0
        assert "must be run inside a Dagster code location project" in result.output


def test_generate_component_already_exists_fails():
    runner = CliRunner()
    _ensure_cwd_on_sys_path()
    with isolated_example_code_location_bar(runner), global_component_types(Baz):
        result = runner.invoke(generate_component_command, ["baz", "alpha"])
        assert result.exit_code == 0
        result = runner.invoke(generate_component_command, ["baz", "alpha"])
        assert result.exit_code != 0
        assert "already exists" in result.output


def test_generated_components_load():
    runner = CliRunner()
    _ensure_cwd_on_sys_path()
    with isolated_example_code_location_bar(runner), global_component_types(Baz):
        params_1 = json.dumps({"asset_key": "alpha", "resource_key": "alpha_client"})
        runner.invoke(generate_component_command, ["baz", "alpha", "--params", params_1])
        params_2 = json.dumps({"asset_key": "beta", "resource_key": "beta_client"})
        runner.invoke(generate_component_command, ["baz", "beta", "--params", params_2])

        _ensure_cwd_on_sys_path()
        defs = importlib.import_module("bar.definitions").defs
        asset_keys = {asset.key for asset in defs.assets}
        assert asset_keys == {AssetKey(["alpha"]), AssetKey(["beta"])}
