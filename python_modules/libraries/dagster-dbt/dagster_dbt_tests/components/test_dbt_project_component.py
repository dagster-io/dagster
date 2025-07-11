import shutil
import sys
import tempfile
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

import pytest
from click.testing import CliRunner
from dagster import AssetKey, AssetSpec, BackfillPolicy
from dagster._core.definitions.backfill_policy import BackfillPolicyType
from dagster._core.definitions.metadata.source_code import (
    CodeReferencesMetadataValue,
    LocalFileCodeReference,
)
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster._utils.env import environ
from dagster.components.core.load_defs import build_component_defs
from dagster.components.core.tree import ComponentTree
from dagster.components.resolved.core_models import AssetAttributesModel, OpSpec
from dagster.components.resolved.errors import ResolutionException
from dagster.components.testing import TestOpCustomization, TestTranslation
from dagster_dbt import DbtProject, DbtProjectComponent
from dagster_dbt.cli.app import project_app_typer_click_object
from dagster_dbt.components.dbt_project.component import get_projects_from_dbt_component
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


@pytest.fixture(scope="module")
def dbt_path() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copytree(STUB_LOCATION_PATH, temp_dir, dirs_exist_ok=True)
        # make sure a manifest.json file is created
        dbt_path = Path(temp_dir) / "defs/jaffle_shop_dbt/jaffle_shop"
        project = DbtProject(dbt_path)
        project.preparer.prepare(project)
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
def test_python_params(dbt_path: Path, backfill_policy: Optional[str]) -> None:
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


class TestDbtTranslation(TestTranslation):
    def test_translation(
        self,
        dbt_path: Path,
        attributes: Mapping[str, Any],
        assertion: Callable[[AssetSpec], bool],
        key_modifier: Optional[Callable[[AssetKey], AssetKey]],
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
    state_path = comp.cli_resource.state_path
    assert state_path
    assert Path(state_path).relative_to(dbt_path.resolve())
    assert comp.project.state_path
    assert comp.project.state_path.resolve() == Path(state_path)
    assert comp.project.target == "target"
    assert comp.project.profile == "profile"


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
    assert c.project.target == "prod"


def test_project_root(dbt_path: Path):
    # match to ensure {{ project_root }} is evaluated
    with pytest.raises(ResolutionException, match="project_dir /dbt does not exist"):
        DbtProjectComponent.resolve_from_yaml("""
project: "{{ project_root }}/dbt"
        """)

    # match to ensure {{ project_root }} is evaluated
    with pytest.raises(ResolutionException, match="project_dir /dbt does not exist"):
        DbtProjectComponent.resolve_from_yaml("""
project:
  project_dir: "{{ project_root }}/dbt"
        """)


def test_disable_prep_if_dev(dbt_path: Path):
    c = DbtProjectComponent.resolve_from_yaml(f"""
project: {dbt_path!s}
prepare_if_dev: False
    """)
    assert not c.prepare_if_dev
