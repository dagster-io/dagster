import os
import shutil
import sys
import tempfile
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import patch

import dagster as dg
import pytest
from click.testing import CliRunner
from dagster import AssetKey, AssetSpec, BackfillPolicy
from dagster._core.definitions.assets.definition.asset_spec import (
    SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET,
)
from dagster._core.definitions.backfill_policy import BackfillPolicyType
from dagster._core.definitions.metadata.source_code import (
    CodeReferencesMetadataValue,
    LocalFileCodeReference,
)
from dagster._core.instance_for_test import instance_for_test
from dagster._core.test_utils import ensure_dagster_tests_import, new_cwd
from dagster._utils.env import environ
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.core.component_tree import ComponentTree
from dagster.components.core.load_defs import build_component_defs
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import AssetAttributesModel, OpSpec
from dagster.components.testing.test_cases import TestOpCustomization, TestTranslation
from dagster.components.testing.utils import create_defs_folder_sandbox
from dagster_dbt import DbtCliResource, DbtProject, DbtProjectComponent
from dagster_dbt.cli.app import project_app_typer_click_object
from dagster_dbt.components.dbt_project.component import (
    _set_resolution_context,
    get_projects_from_dbt_component,
)
from dagster_dbt_tests.dbt_projects import test_metadata_path
from dagster_dg_cli.cli import cli as dg_cli
from dagster_shared import check

ensure_dagster_tests_import()
from dagster_tests.components_tests.integration_tests.component_loader import (
    load_test_component_defs,
)
from dagster_tests.components_tests.utils import (
    build_component_defs_for_test,
    create_project_from_components,
    load_component_for_test,
)

STUB_LOCATION_PATH = Path(__file__).parent / "code_locations" / "dbt_project_location"
COMPONENT_RELPATH = "defs/jaffle_shop_dbt"

JAFFLE_SHOP_KEYS = {
    AssetKey("customers"),
    AssetKey("orders"),
    AssetKey("raw_customers"),
    AssetKey("raw_orders"),
    AssetKey("raw_payments"),
    AssetKey("stg_customers"),
    AssetKey("stg_orders"),
    AssetKey("stg_payments"),
}


@pytest.fixture(autouse=True)
def _setup() -> Iterator:
    with (
        instance_for_test() as instance,
        scoped_definitions_load_context(),
        # this file doesn't use `create_defs_folder_sandbox` so we need to mock out the local_state_dir
        tempfile.TemporaryDirectory() as temp_dir,
        patch(
            "dagster.components.utils.project_paths.get_local_defs_state_dir",
            return_value=Path(temp_dir),
        ),
    ):
        yield instance


@pytest.fixture(scope="module")
def dbt_path() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copytree(STUB_LOCATION_PATH, temp_dir, dirs_exist_ok=True)
        # make sure a manifest.json file is created
        dbt_path = Path(temp_dir) / "defs/jaffle_shop_dbt/jaffle_shop"
        project = DbtProject(dbt_path)
        project.preparer.prepare(project)
        yield dbt_path


@pytest.fixture(scope="function")
def tmp_dbt_path() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copytree(STUB_LOCATION_PATH, temp_dir, dirs_exist_ok=True)
        dbt_path = Path(temp_dir) / "defs/jaffle_shop_dbt/jaffle_shop"
        yield dbt_path


class TestDbtOpCustomization(TestOpCustomization):
    def test_translation(
        self, attributes: Mapping[str, Any], assertion: Callable[[OpSpec], bool], dbt_path
    ) -> None:
        component = load_component_for_test(
            DbtProjectComponent,
            {
                "project": str(dbt_path),
                "op": attributes,
            },
        )
        op = component.op
        assert op
        assert assertion(op)


@pytest.mark.parametrize(
    "backfill_policy", [None, "single_run", "multi_run", "multi_run_with_max_partitions"]
)
def test_python_params(dbt_path: Path, backfill_policy: str | None) -> None:
    backfill_policy_arg = {}
    if backfill_policy == "single_run":
        backfill_policy_arg["backfill_policy"] = {"type": "single_run"}
    elif backfill_policy == "multi_run":
        backfill_policy_arg["backfill_policy"] = {"type": "multi_run"}
    elif backfill_policy == "multi_run_with_max_partitions":
        backfill_policy_arg["backfill_policy"] = {"type": "multi_run", "max_partitions_per_run": 3}

    defs = build_component_defs_for_test(
        DbtProjectComponent,
        {
            "project": str(dbt_path),
            "op": {
                "name": "some_op",
                "tags": {"tag1": "value"},
                **backfill_policy_arg,
            },
        },
    )
    assert defs.resolve_asset_graph().get_all_asset_keys() == JAFFLE_SHOP_KEYS
    assets_def = defs.resolve_assets_def("stg_customers")
    assert assets_def.op.name == "some_op"
    assert assets_def.op.tags["tag1"] == "value"

    # Ensure dbt code references are automatically added to the asset
    refs = check.inst(
        assets_def.metadata_by_key[AssetKey("stg_customers")]["dagster/code_references"],
        CodeReferencesMetadataValue,
    )
    assert len(refs.code_references) == 1
    assert isinstance(refs.code_references[0], LocalFileCodeReference)
    assert refs.code_references[0].file_path.endswith("models/staging/stg_customers.sql")

    if backfill_policy is None:
        assert assets_def.backfill_policy is None
    elif backfill_policy == "single_run":
        assert isinstance(assets_def.backfill_policy, BackfillPolicy)
        assert assets_def.backfill_policy.policy_type == BackfillPolicyType.SINGLE_RUN
    elif backfill_policy == "multi_run":
        assert isinstance(assets_def.backfill_policy, BackfillPolicy)
        assert assets_def.backfill_policy.policy_type == BackfillPolicyType.MULTI_RUN
        assert assets_def.backfill_policy.max_partitions_per_run == 1
    elif backfill_policy == "multi_run_with_max_partitions":
        assert isinstance(assets_def.backfill_policy, BackfillPolicy)
        assert assets_def.backfill_policy.policy_type == BackfillPolicyType.MULTI_RUN
        assert assets_def.backfill_policy.max_partitions_per_run == 3


def test_load_from_path(dbt_path: Path) -> None:
    with load_test_component_defs(dbt_path.parent.parent.parent) as defs:
        assert defs.resolve_asset_graph().get_all_asset_keys() == JAFFLE_SHOP_KEYS

        for asset_node in defs.resolve_asset_graph().asset_nodes:
            assert asset_node.tags["foo"] == "bar"

            assert asset_node.metadata["something"] == 1


def test_project_prepare_cli(dbt_path: Path) -> None:
    src_path = dbt_path.parent.parent.parent
    with create_project_from_components(str(src_path)) as res:
        p, _ = res
        result = CliRunner().invoke(
            project_app_typer_click_object,
            [
                "prepare-and-package",
                "--components",
                str(p),
            ],
        )
        assert result.exit_code == 0

        projects = get_projects_from_dbt_component(p)

        assert projects

        for p in projects:
            assert p.manifest_path.exists()


def test_dbt_subclass_additional_scope_fn(dbt_path: Path) -> None:
    @dataclass
    class DebugDbtProjectComponent(DbtProjectComponent):
        @classmethod
        def get_additional_scope(cls) -> Mapping[str, Any]:
            return {
                "get_tags_for_node": lambda node: {
                    "model_id": str(node.get("name", "")).replace("_", "-")
                }
            }

    defs = build_component_defs_for_test(
        DebugDbtProjectComponent,
        {
            "project": str(dbt_path),
            "translation": {"tags": "{{ get_tags_for_node(node) }}"},
        },
    )
    assets_def = defs.resolve_assets_def(AssetKey("stg_customers"))
    assert assets_def.get_asset_spec(AssetKey("stg_customers")).tags["model_id"] == "stg-customers"


def test_target_path_from_component_string(dbt_path: Path) -> None:
    component = load_component_for_test(
        DbtProjectComponent,
        {
            "project": {
                "project_dir": str(dbt_path),
                "target_path": "tmp_dbt_target",
            }
        },
    )
    assert isinstance(component.dbt_project.target_path, Path)
    assert component.dbt_project.target_path == Path("tmp_dbt_target")


class TestDbtTranslation(TestTranslation):
    def test_translation(
        self,
        dbt_path: Path,
        attributes: Mapping[str, Any],
        assertion: Callable[[AssetSpec], bool],
        key_modifier: Callable[[AssetKey], AssetKey] | None,
    ) -> None:
        defs = build_component_defs_for_test(
            DbtProjectComponent,
            {
                "project": str(dbt_path),
                "translation": attributes,
            },
        )
        key = AssetKey("stg_customers")

        if key_modifier:
            key = key_modifier(key)

        assets_def = defs.resolve_assets_def(key)
        assert assertion(assets_def.get_asset_spec(key))


def test_subselection(dbt_path: Path) -> None:
    defs = build_component_defs_for_test(
        DbtProjectComponent,
        {"project": str(dbt_path), "select": "raw_customers"},
    )
    assert defs.resolve_asset_graph().get_all_asset_keys() == {AssetKey("raw_customers")}


def test_exclude(dbt_path: Path) -> None:
    defs = build_component_defs_for_test(
        DbtProjectComponent,
        {"project": str(dbt_path), "exclude": "customers"},
    )
    assert defs.resolve_asset_graph().get_all_asset_keys() == JAFFLE_SHOP_KEYS - {
        AssetKey("customers")
    }


DEPENDENCY_ON_DBT_PROJECT_LOCATION_PATH = (
    Path(__file__).parent / "code_locations" / "dependency_on_dbt_project_location"
)


def test_dependency_on_dbt_project():
    # Ensure DEPENDENCY_ON_DBT_PROJECT_LOCATION_PATH is an importable python module
    sys.path.append(str(DEPENDENCY_ON_DBT_PROJECT_LOCATION_PATH.parent))

    # there's an order of operations issue here, wherein the dependency on the dbt project only
    # loads the component (and doesn't build definitions), but the dbt project only ensures that
    # the manifest exists during the build process. we should figure out a more systemtic way to
    # fix this issue.
    project = DbtProject(
        Path(DEPENDENCY_ON_DBT_PROJECT_LOCATION_PATH) / "defs/jaffle_shop_dbt/jaffle_shop"
    )
    project.preparer.prepare(project)

    defs = build_component_defs(DEPENDENCY_ON_DBT_PROJECT_LOCATION_PATH / "defs")

    assert AssetKey("downstream_of_customers") in defs.resolve_asset_graph().get_all_asset_keys()
    downstream_of_customers_def = defs.resolve_assets_def("downstream_of_customers")
    assert set(downstream_of_customers_def.asset_deps[AssetKey("downstream_of_customers")]) == {
        AssetKey("customers")
    }

    assert (
        AssetKey("downstream_of_customers_two") in defs.resolve_asset_graph().get_all_asset_keys()
    )
    downstream_of_customers_two_def = defs.resolve_assets_def("downstream_of_customers_two")
    assert set(
        downstream_of_customers_two_def.asset_deps[AssetKey("downstream_of_customers_two")]
    ) == {AssetKey("customers")}

    assert defs.resolve_job_def("run_customers")
    assert defs.resolve_schedule_def("run_customers_schedule")


def test_spec_is_available_in_scope(dbt_path: Path) -> None:
    defs = build_component_defs_for_test(
        DbtProjectComponent,
        {
            "project": str(dbt_path),
            "translation": {"metadata": {"asset_key": "{{ spec.key.path }}"}},
        },
    )
    assets_def = defs.resolve_assets_def(AssetKey("stg_customers"))
    assert assets_def.get_asset_spec(AssetKey("stg_customers")).metadata["asset_key"] == [
        "stg_customers"
    ]


def map_spec(spec: AssetSpec) -> AssetSpec:
    return spec.replace_attributes(tags={"is_custom_spec": "yes"})


def map_spec_to_attributes(spec: AssetSpec):
    return AssetAttributesModel(tags={"is_custom_spec": "yes"})


def map_spec_to_attributes_dict(spec: AssetSpec) -> dict[str, Any]:
    return {"tags": {"is_custom_spec": "yes"}}


@pytest.mark.parametrize("map_fn", [map_spec, map_spec_to_attributes, map_spec_to_attributes_dict])
def test_udf_map_spec(dbt_path: Path, map_fn: Callable[[AssetSpec], Any]) -> None:
    @dataclass
    class DebugDbtProjectComponent(DbtProjectComponent):
        @classmethod
        def get_additional_scope(cls) -> Mapping[str, Any]:
            return {"map_spec": map_fn}

    defs = build_component_defs_for_test(
        DebugDbtProjectComponent,
        {
            "project": str(dbt_path),
            "translation": "{{ map_spec(spec) }}",
        },
    )
    assets_def = defs.resolve_assets_def(AssetKey("stg_customers"))
    assert assets_def.get_asset_spec(AssetKey("stg_customers")).tags["is_custom_spec"] == "yes"


def test_state_path(
    dbt_path: Path,
) -> None:
    comp = load_component_for_test(
        DbtProjectComponent,
        {
            "project": {
                "project_dir": str(dbt_path),
                "state_path": "state",
                "profile": "profile",
                "target": "target",
            },
        },
    )
    state_path = comp.dbt_project.state_path
    assert state_path
    assert Path(state_path).relative_to(dbt_path.resolve())
    assert comp.dbt_project.state_path
    assert comp.dbt_project.state_path.resolve() == Path(state_path)
    assert comp.dbt_project.target == "target"
    assert comp.dbt_project.profile == "profile"


@pytest.mark.parametrize(
    ["cli_args", "expected_args"],
    [
        (
            None,
            [
                "build",
            ],
        ),
        (
            ["build", "--foo"],
            ["build", "--foo"],
        ),
        (
            [
                "run",
                {
                    "--vars": {
                        "start_date": "{{ partition_key_range.start }}",
                        "end_date": "{{ foo }}",
                    }
                },
                {"--threads": 2},
            ],
            [
                "run",
                "--vars",
                '{"start_date": "2021-01-01", "end_date": "2021-01-01"}',
                "--threads",
                "2",
            ],
        ),
    ],
)
def test_cli_args(dbt_path: Path, cli_args: list[str] | None, expected_args: list[str]) -> None:
    args = {"cli_args": cli_args} if cli_args else {}

    comp = load_component_for_test(
        DbtProjectComponent,
        {"project": str(dbt_path), **args},
    )
    context = dg.build_asset_context(
        partition_key_range=dg.PartitionKeyRange(start="2021-01-01", end="2021-01-01"),
    )
    with _set_resolution_context(ResolutionContext.default().with_scope(foo="2021-01-01")):
        assert comp.get_cli_args(context) == expected_args


def test_python_interface(dbt_path: Path):
    context = ComponentTree.for_test().load_context
    assert DbtProjectComponent(
        project=DbtProject(dbt_path),
    ).build_defs(context)

    defs = DbtProjectComponent(
        project=DbtProject(dbt_path),
        translation=lambda spec, _: spec.replace_attributes(tags={"python": "rules"}),
    ).build_defs(context)
    assets_def = defs.resolve_assets_def(AssetKey("stg_customers"))
    assert assets_def.get_asset_spec(AssetKey("stg_customers")).tags["python"] == "rules"


def test_settings(dbt_path: Path):
    c = DbtProjectComponent.resolve_from_yaml(f"""
project: {dbt_path!s}
translation_settings:
    enable_source_tests_as_checks: True
    """)
    assert c.translator.settings.enable_source_tests_as_checks

    c = DbtProjectComponent.resolve_from_yaml(f"""
project: {dbt_path!s}
translation:
    group_name: bark
translation_settings:
    enable_source_tests_as_checks: True
    """)
    assert c.translator.settings.enable_source_tests_as_checks


def test_resolution(dbt_path: Path):
    with environ({"DBT_TARGET": "prod"}):
        target = """target: "{{ env.DBT_TARGET }}" """
        c = DbtProjectComponent.resolve_from_yaml(f"""
project:
  project_dir: {dbt_path!s}
  {target}
        """)
    assert c.dbt_project.target == "prod"


def test_disable_prep_if_dev(dbt_path: Path):
    c = DbtProjectComponent.resolve_from_yaml(f"""
project: {dbt_path!s}
prepare_if_dev: False
    """)
    assert not c.prepare_if_dev


def test_subclass_override_get_asset_spec(dbt_path: Path) -> None:
    """Test that we can subclass DbtProjectComponent and override get_asset_spec method."""

    @dataclass
    class CustomDbtProjectComponent(DbtProjectComponent):
        def get_asset_spec(
            self, manifest: Mapping[str, Any], unique_id: str, project: DbtProject | None
        ) -> dg.AssetSpec:
            # Get the base asset spec from the parent implementation
            base_spec = super().get_asset_spec(manifest, unique_id, project)

            # Add custom tags to demonstrate the override works
            custom_tags = {
                "custom_override": "true",
                "model_name": manifest["nodes"][unique_id]["name"],
            }

            # Return the spec with our custom modifications
            return base_spec.replace_attributes(tags={**base_spec.tags, **custom_tags})

    defs = build_component_defs_for_test(CustomDbtProjectComponent, {"project": str(dbt_path)})

    # Test that our custom get_asset_spec method is being used
    assets_def = defs.resolve_assets_def(AssetKey("stg_customers"))
    asset_spec = assets_def.get_asset_spec(AssetKey("stg_customers"))

    # Verify that our custom tags were added
    assert asset_spec.tags["custom_override"] == "true"
    assert asset_spec.tags["model_name"] == "stg_customers"
    # Verify code references are still added automatically
    refs = check.inst(
        assets_def.metadata_by_key[AssetKey("stg_customers")]["dagster/code_references"],
        CodeReferencesMetadataValue,
    )
    assert len(refs.code_references) == 1
    assert isinstance(refs.code_references[0], LocalFileCodeReference)
    assert refs.code_references[0].file_path.endswith("models/staging/stg_customers.sql")

    # Verify that the base functionality still works (e.g., original metadata is preserved)
    assert "dagster-dbt/materialization_type" in asset_spec.metadata
    assert "dagster/table_name" in asset_spec.metadata

    # Test with another asset to ensure it works across different models
    assets_def_orders = defs.resolve_assets_def(AssetKey("stg_orders"))
    asset_spec_orders = assets_def_orders.get_asset_spec(AssetKey("stg_orders"))

    assert asset_spec_orders.tags["custom_override"] == "true"
    assert asset_spec_orders.tags["model_name"] == "stg_orders"


def test_basic_component_dev_mode(tmp_dbt_path: Path) -> None:
    with (
        instance_for_test(),
        create_defs_folder_sandbox() as sandbox,
        environ({"DAGSTER_IS_DEV_CLI": "1"}),
    ):
        defs_path = sandbox.scaffold_component(
            component_cls=DbtProjectComponent,
            defs_yaml_contents={
                "type": "dagster_dbt.DbtProjectComponent",
                "attributes": {
                    "project": {"project_dir": str(tmp_dbt_path)},
                },
            },
            defs_path="dbt",
        )

        with (
            scoped_definitions_load_context() as load_context,
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            assert isinstance(component, DbtProjectComponent)

            # make sure assets are still loaded even though original project dir is gone
            specs = defs.get_all_asset_specs()
            assert len(specs) > 0

            # Verify we have the expected assets from jaffle_shop
            asset_keys = {spec.key for spec in specs}
            assert dg.AssetKey("customers") in asset_keys
            assert dg.AssetKey("orders") in asset_keys

            # Verify the state key was accessed
            assert load_context.accessed_defs_state_info is not None

            expected_key = "DbtProjectComponent[jaffle_shop]"
            assert expected_key in load_context.accessed_defs_state_info.info_mapping


def test_basic_component_non_dev_mode(tmp_dbt_path: Path) -> None:
    with (
        instance_for_test(),
        create_defs_folder_sandbox() as sandbox,
    ):
        defs_path = sandbox.scaffold_component(
            component_cls=DbtProjectComponent,
            defs_yaml_contents={
                "type": "dagster_dbt.DbtProjectComponent",
                "attributes": {
                    "project": {"project_dir": str(tmp_dbt_path)},
                },
            },
            defs_path="dbt",
        )

        # simulate running refresh-defs-state in CI
        original_env = os.environ.copy()
        with new_cwd(str(sandbox.project_root)), sandbox.activate_venv_for_project():
            result = CliRunner().invoke(dg_cli, ["utils", "refresh-defs-state"])
            assert result.exit_code == 0
        # a side effect of running refresh-defs-state in process is that DAGSTER_IS_DEV_CLI is set to 1,
        # so avoid that by restoring the original environment
        os.environ = original_env

        # delete the original dbt project directory entirely to simulate a PEX deploy
        shutil.rmtree(tmp_dbt_path)

        with (
            scoped_definitions_load_context() as load_context,
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs),
        ):
            assert isinstance(component, DbtProjectComponent)

            # make sure assets are still loaded even though original project dir is gone
            specs = defs.get_all_asset_specs()
            assert len(specs) > 0

            # Verify we have the expected assets from jaffle_shop
            asset_keys = {spec.key for spec in specs}
            assert dg.AssetKey("customers") in asset_keys
            assert dg.AssetKey("orders") in asset_keys

            # Verify the state key was accessed
            assert load_context.accessed_defs_state_info is not None

            expected_key = "DbtProjectComponent[jaffle_shop]"
            assert expected_key in load_context.accessed_defs_state_info.info_mapping


def test_subclass_with_op_config_schema(dbt_path: Path) -> None:
    """Test that we can subclass DbtProjectComponent and set a custom op_config_schema."""

    @dataclass
    class CustomConfigDbtProjectComponent(DbtProjectComponent):
        @property
        def op_config_schema(self) -> type[dg.Config]:
            class CustomConfig(dg.Config):
                full_refresh: bool = False
                custom_param: str = "default"

            return CustomConfig

        def execute(self, context: dg.AssetExecutionContext, dbt: "DbtCliResource") -> Iterator:
            # Access the config from the context
            config = context.op_config
            context.log.info(f"full_refresh: {config['full_refresh']}")
            context.log.info(f"custom_param: {config['custom_param']}")

            # Use the config to modify execution behavior
            if config["full_refresh"]:
                # In a real implementation, you might modify the dbt CLI args here
                context.log.info("Running with full refresh")

            # Call the parent execute method
            yield from super().execute(context, dbt)

    defs = build_component_defs_for_test(
        CustomConfigDbtProjectComponent,
        {"project": str(dbt_path), "select": "raw_customers"},
    )

    # Verify the component was created with the correct config schema
    assets_def = defs.resolve_assets_def(AssetKey("raw_customers"))

    # Check that the config schema is set on the underlying assets_def
    assert assets_def.op.config_schema is not None

    # Test that we can materialize with custom config
    with instance_for_test() as instance:
        result = defs.get_implicit_global_asset_job_def().execute_in_process(
            instance=instance,
            asset_selection=[AssetKey("raw_customers")],
            run_config={
                "ops": {
                    assets_def.op.name: {
                        "config": {
                            "full_refresh": True,
                            "custom_param": "test_value",
                        }
                    }
                }
            },
        )
        assert result.success


def test_subclass_with_op_config_schema_and_custom_get_asset_spec(dbt_path: Path) -> None:
    """Test subclassing with both op_config_schema and get_asset_spec overrides."""

    @dataclass
    class AdvancedCustomDbtProjectComponent(DbtProjectComponent):
        @property
        def op_config_schema(self) -> type[dg.Config]:
            class AdvancedConfig(dg.Config):
                add_metadata_url: bool = True
                base_url: str = "https://example.com"

            return AdvancedConfig

        def get_asset_spec(
            self, manifest: Mapping[str, Any], unique_id: str, project: DbtProject | None
        ) -> dg.AssetSpec:
            base_spec = super().get_asset_spec(manifest, unique_id, project)
            dbt_props = self.get_resource_props(manifest, unique_id)

            # Add custom metadata to the asset spec
            return base_spec.merge_attributes(
                metadata={
                    "custom_metadata": "added_via_subclass",
                    "model_name": dbt_props["name"],
                }
            )

        def execute(self, context: dg.AssetExecutionContext, dbt: "DbtCliResource") -> Iterator:
            config = context.op_config
            if config["add_metadata_url"]:
                context.log.info(f"Would add URL metadata: {config['base_url']}")

            yield from super().execute(context, dbt)

    defs = build_component_defs_for_test(
        AdvancedCustomDbtProjectComponent,
        {"project": str(dbt_path), "select": "stg_customers"},
    )

    assets_def = defs.resolve_assets_def(AssetKey("stg_customers"))
    asset_spec = assets_def.get_asset_spec(AssetKey("stg_customers"))

    # Verify custom metadata from get_asset_spec override
    assert asset_spec.metadata["custom_metadata"] == "added_via_subclass"
    assert asset_spec.metadata["model_name"] == "stg_customers"

    # Verify config schema is set
    assert assets_def.op.config_schema is not None

    # Test execution with custom config
    with instance_for_test() as instance:
        result = defs.get_implicit_global_asset_job_def().execute_in_process(
            instance=instance,
            asset_selection=[AssetKey("stg_customers")],
            run_config={
                "ops": {
                    assets_def.op.name: {
                        "config": {
                            "add_metadata_url": True,
                            "base_url": "https://custom.example.com",
                        }
                    }
                }
            },
        )
        assert result.success


def test_upstream_source_metadata_flows_to_stub_asset() -> None:
    """Test that source metadata is included on stub assets when enable_source_metadata is True."""
    # Prepare the manifest for test_metadata_path
    project = DbtProject(test_metadata_path)
    project.preparer.prepare(project)

    defs = build_component_defs_for_test(
        DbtProjectComponent,
        {
            "project": str(test_metadata_path),
            "select": "stg_customers",  # This model depends on source 'jaffle_shop.raw_customers'
            "translation_settings": {
                "enable_source_metadata": True,
            },
        },
    )

    # Get all asset specs from the definitions
    all_specs = list(defs.get_all_asset_specs())
    specs_by_key = {spec.key: spec for spec in all_specs}

    # The source has a custom asset key configured via meta.dagster.asset_key: ["raw_source_customers"]
    source_key = AssetKey("raw_source_customers")
    assert source_key in specs_by_key, f"Source key {source_key} not found in {specs_by_key.keys()}"

    source_spec = specs_by_key[source_key]

    # Should be marked as auto-created stub asset
    assert source_spec.metadata.get(SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET) is True

    # Should have the table_name metadata from the source definition that enables remapping
    table_name = "master_jaffle_shop.main.raw_customers"
    assert source_spec.metadata["dagster/table_name"] == table_name

    # Now build defs with something matching that table name and verify key is remapped
    upstream_spec = dg.AssetSpec(
        key=AssetKey("foo_upstream_defined"), metadata={"dagster/table_name": table_name}
    )
    defs_combined = dg.Definitions.merge(defs, dg.Definitions(assets=[upstream_spec]))

    all_specs_combined = list(defs_combined.get_all_asset_specs())
    specs_by_key_combined = {spec.key: spec for spec in all_specs_combined}

    # should have been remapped, so shouldn't show up here
    assert AssetKey("raw_source_customers") not in specs_by_key_combined
    stg_customers_spec = specs_by_key_combined[AssetKey("stg_customers")]

    # dependency of stg_customers should have been remapped
    deps = list(stg_customers_spec.deps)
    assert len(deps) == 1
    assert deps[0].asset_key == AssetKey("foo_upstream_defined")
    assert deps[0].metadata["dagster/table_name"] == table_name
