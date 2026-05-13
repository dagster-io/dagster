import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import dagster as dg
import pytest
from dagster import AssetKey
from dagster._core.instance_for_test import instance_for_test
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster._utils.env import environ
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster_dbt import DbtProject, DbtProjectComponent

ensure_dagster_tests_import()

from dagster_tests.components_tests.integration_tests.component_loader import (
    load_test_component_defs,
)
from dagster_tests.components_tests.utils import build_component_defs_for_test

STUB_LOCATION_PATH = (
    Path(__file__).parent / "code_locations" / "templated_custom_keys_dbt_project_location"
)
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

JAFFLE_SHOP_KEYS_WITH_PREFIX = {
    AssetKey(["some_prefix", "customers"]),
    AssetKey(["some_prefix", "orders"]),
    AssetKey(["some_prefix", "raw_customers"]),
    AssetKey(["some_prefix", "raw_orders"]),
    AssetKey(["some_prefix", "raw_payments"]),
    AssetKey(["some_prefix", "stg_customers"]),
    AssetKey(["some_prefix", "stg_orders"]),
    AssetKey(["some_prefix", "stg_payments"]),
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


def test_python_attributes_node_rename(dbt_path: Path) -> None:
    defs = build_component_defs_for_test(
        DbtProjectComponent,
        {
            "project": str(dbt_path),
            "translation": {"key": "some_prefix/{{ node.name }}"},
        },
    )
    assert defs.resolve_asset_graph().get_all_asset_keys() == JAFFLE_SHOP_KEYS_WITH_PREFIX


def test_python_attributes_group(dbt_path: Path) -> None:
    defs = build_component_defs_for_test(
        DbtProjectComponent,
        {
            "project": str(dbt_path),
            "translation": {"group_name": "some_group"},
        },
    )
    assert defs.resolve_asset_graph().get_all_asset_keys() == JAFFLE_SHOP_KEYS
    for key in JAFFLE_SHOP_KEYS:
        assert defs.resolve_assets_def(key).get_asset_spec(key).group_name == "some_group"


def test_load_from_path(dbt_path: Path) -> None:
    with instance_for_test(), load_test_component_defs(dbt_path.parent.parent.parent) as defs:
        assert defs.resolve_asset_graph().get_all_asset_keys() == JAFFLE_SHOP_KEYS_WITH_PREFIX


def test_render_vars_root(dbt_path: Path) -> None:
    with environ({"GROUP_AS_ENV": "group_in_env"}):
        defs = build_component_defs_for_test(
            DbtProjectComponent,
            {
                "project": str(dbt_path),
                "translation": {"group_name": "{{ env.GROUP_AS_ENV }}"},
            },
        )
        assert defs.resolve_asset_graph().get_all_asset_keys() == JAFFLE_SHOP_KEYS
        for key in JAFFLE_SHOP_KEYS:
            assert defs.resolve_assets_def(key).get_asset_spec(key).group_name == "group_in_env"


def test_render_vars_asset_key(dbt_path: Path) -> None:
    with environ({"ASSET_KEY_PREFIX": "some_prefix"}):
        defs = build_component_defs_for_test(
            DbtProjectComponent,
            {
                "project": str(dbt_path),
                "translation": {
                    "key": "{{ env.ASSET_KEY_PREFIX }}/{{ node.name }}",
                },
            },
        )
        assert defs.resolve_asset_graph().get_all_asset_keys() == JAFFLE_SHOP_KEYS_WITH_PREFIX


def test_subclass_get_asset_spec_remaps_model_deps(dbt_path: Path) -> None:
    """Subclass override prefixing keys must remap deps to other models.

    Regression test for https://github.com/dagster-io/dagster/issues/33823.
    """

    class PrefixedDbtComponent(DbtProjectComponent):
        def get_asset_spec(self, manifest, unique_id, project):
            base = super().get_asset_spec(manifest, unique_id, project)
            return base.replace_attributes(key=base.key.with_prefix("some_prefix"))

    defs = build_component_defs_for_test(PrefixedDbtComponent, {"project": str(dbt_path)})
    graph = defs.resolve_asset_graph()

    assert graph.get_all_asset_keys() == JAFFLE_SHOP_KEYS_WITH_PREFIX

    customers = AssetKey(["some_prefix", "customers"])
    assert graph.get(customers).parent_keys == {
        AssetKey(["some_prefix", "stg_customers"]),
        AssetKey(["some_prefix", "stg_orders"]),
        AssetKey(["some_prefix", "stg_payments"]),
    }


def test_subclass_get_asset_spec_remaps_source_deps(dbt_path: Path) -> None:
    """Source upstreams (raw_*) are remapped too, not just model upstreams."""

    class PrefixedDbtComponent(DbtProjectComponent):
        def get_asset_spec(self, manifest, unique_id, project):
            base = super().get_asset_spec(manifest, unique_id, project)
            return base.replace_attributes(key=base.key.with_prefix("some_prefix"))

    defs = build_component_defs_for_test(PrefixedDbtComponent, {"project": str(dbt_path)})
    graph = defs.resolve_asset_graph()

    assert graph.get(AssetKey(["some_prefix", "stg_customers"])).parent_keys == {
        AssetKey(["some_prefix", "raw_customers"]),
    }


def test_subclass_get_asset_spec_no_key_change_is_full_noop(dbt_path: Path) -> None:
    """A subclass that overrides get_asset_spec without changing keys must not perturb
    keys, deps (including partition_mapping and metadata), group_name, kinds, or
    metadata keys on any spec.
    """
    baseline_defs = build_component_defs_for_test(DbtProjectComponent, {"project": str(dbt_path)})
    baseline_graph = baseline_defs.resolve_asset_graph()

    class TaggedDbtComponent(DbtProjectComponent):
        def get_asset_spec(self, manifest, unique_id, project):
            base = super().get_asset_spec(manifest, unique_id, project)
            return base.merge_attributes(tags={"custom": "yes"})

    overridden_defs = build_component_defs_for_test(TaggedDbtComponent, {"project": str(dbt_path)})
    overridden_graph = overridden_defs.resolve_asset_graph()

    assert overridden_graph.get_all_asset_keys() == baseline_graph.get_all_asset_keys()
    for key in baseline_graph.get_all_asset_keys():
        baseline_spec = baseline_defs.resolve_assets_def(key).get_asset_spec(key)
        overridden_spec = overridden_defs.resolve_assets_def(key).get_asset_spec(key)
        # The added tag is the one allowed difference.
        assert {
            k: v for k, v in overridden_spec.tags.items() if k != "custom"
        } == baseline_spec.tags
        # Deps must match exactly, including partition_mapping and metadata.
        baseline_deps = {d.asset_key: d for d in baseline_spec.deps}
        overridden_deps = {d.asset_key: d for d in overridden_spec.deps}
        assert baseline_deps.keys() == overridden_deps.keys()
        for asset_key, baseline_dep in baseline_deps.items():
            assert overridden_deps[asset_key].partition_mapping == baseline_dep.partition_mapping
            assert overridden_deps[asset_key].metadata == baseline_dep.metadata
        assert overridden_spec.group_name == baseline_spec.group_name
        assert overridden_spec.kinds == baseline_spec.kinds
        assert overridden_spec.partitions_def == baseline_spec.partitions_def
        assert overridden_spec.metadata == baseline_spec.metadata


def test_subclass_manual_dep_rewrite_still_works(dbt_path: Path) -> None:
    """The issue reporter's manual workaround must continue to produce a correct graph
    after the auto-remap is added (i.e. no double-apply).
    """

    class ManualPrefixedDbtComponent(DbtProjectComponent):
        def get_asset_spec(self, manifest, unique_id, project):
            base = super().get_asset_spec(manifest, unique_id, project)
            new_key = base.key.with_prefix("some_prefix")
            new_deps = [
                dg.AssetDep(
                    asset=d.asset_key.with_prefix("some_prefix"),
                    partition_mapping=d.partition_mapping,
                    metadata=d.metadata,
                )
                for d in base.deps
            ]
            return base.replace_attributes(key=new_key, deps=new_deps)

    defs = build_component_defs_for_test(ManualPrefixedDbtComponent, {"project": str(dbt_path)})
    graph = defs.resolve_asset_graph()
    assert graph.get_all_asset_keys() == JAFFLE_SHOP_KEYS_WITH_PREFIX
    customers = AssetKey(["some_prefix", "customers"])
    assert graph.get(customers).parent_keys == {
        AssetKey(["some_prefix", "stg_customers"]),
        AssetKey(["some_prefix", "stg_orders"]),
        AssetKey(["some_prefix", "stg_payments"]),
    }


def test_yaml_translation_key_rewrite_remaps_deps(dbt_path: Path) -> None:
    """Regression lock: the YAML translation path already remapped deps correctly;
    assert it explicitly so future refactors don't silently break it.
    """
    defs = build_component_defs_for_test(
        DbtProjectComponent,
        {"project": str(dbt_path), "translation": {"key": "some_prefix/{{ node.name }}"}},
    )
    graph = defs.resolve_asset_graph()
    customers = AssetKey(["some_prefix", "customers"])
    assert graph.get(customers).parent_keys == {
        AssetKey(["some_prefix", "stg_customers"]),
        AssetKey(["some_prefix", "stg_orders"]),
        AssetKey(["some_prefix", "stg_payments"]),
    }
