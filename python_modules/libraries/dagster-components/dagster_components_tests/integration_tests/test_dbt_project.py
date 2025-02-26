import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import pytest
from dagster import AssetKey
from dagster._core.definitions.backfill_policy import BackfillPolicy, BackfillPolicyType
from dagster_components.core.component_decl_builder import ComponentFileModel
from dagster_components.core.component_defs_builder import (
    YamlComponentDecl,
    build_components_from_component_folder,
    defs_from_components,
)
from dagster_components.lib.dbt_project.component import DbtProjectComponent
from dagster_dbt import DbtProject

from dagster_components_tests.utils import assert_assets, get_asset_keys, script_load_context

if TYPE_CHECKING:
    from dagster import AssetsDefinition

STUB_LOCATION_PATH = Path(__file__).parent.parent / "code_locations" / "dbt_project_location"
COMPONENT_RELPATH = "components/jaffle_shop_dbt"

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


@contextmanager
@pytest.fixture(scope="module")
def dbt_path() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copytree(STUB_LOCATION_PATH, temp_dir, dirs_exist_ok=True)
        # make sure a manifest.json file is created
        project = DbtProject(Path(temp_dir) / "components/jaffle_shop_dbt/jaffle_shop")
        project.preparer.prepare(project)
        yield Path(temp_dir)


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

    decl_node = YamlComponentDecl(
        path=dbt_path / COMPONENT_RELPATH,
        component_file_model=ComponentFileModel(
            type="dbt_project",
            attributes={
                "dbt": {"project_dir": "jaffle_shop"},
                "op": {"name": "some_op", "tags": {"tag1": "value"}, **backfill_policy_arg},
            },
        ),
    )
    context = script_load_context(decl_node)
    component = DbtProjectComponent.load(
        attributes=decl_node.get_attributes(DbtProjectComponent.get_schema()), context=context
    )
    assert get_asset_keys(component) == JAFFLE_SHOP_KEYS
    defs = component.build_defs(script_load_context())
    assets_def: AssetsDefinition = defs.get_assets_def("stg_customers")
    assert assets_def.op.name == "some_op"
    assert assets_def.op.tags["tag1"] == "value"

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
    components = build_components_from_component_folder(
        script_load_context(), dbt_path / "components"
    )
    assert len(components) == 1
    assert get_asset_keys(components[0]) == JAFFLE_SHOP_KEYS

    assert_assets(components[0], len(JAFFLE_SHOP_KEYS))

    defs = defs_from_components(
        context=script_load_context(),
        components=components,
        resources={},
    )

    assert defs.get_asset_graph().get_all_asset_keys() == JAFFLE_SHOP_KEYS

    for asset_node in defs.get_asset_graph().asset_nodes:
        assert asset_node.tags["foo"] == "bar"
        assert asset_node.tags["another"] == "one"
        assert asset_node.metadata["something"] == 1


def test_subselection(dbt_path: Path) -> None:
    decl_node = YamlComponentDecl(
        path=dbt_path / COMPONENT_RELPATH,
        component_file_model=ComponentFileModel(
            type="dbt_project",
            attributes={
                "dbt": {"project_dir": "jaffle_shop"},
                "select": "raw_customers",
            },
        ),
    )
    context = script_load_context(decl_node)
    component = DbtProjectComponent.load(
        attributes=decl_node.get_attributes(DbtProjectComponent.get_schema()), context=context
    )
    assert get_asset_keys(component) == {AssetKey("raw_customers")}


def test_exclude(dbt_path: Path) -> None:
    decl_node = YamlComponentDecl(
        path=dbt_path / COMPONENT_RELPATH,
        component_file_model=ComponentFileModel(
            type="dbt_project",
            attributes={
                "dbt": {"project_dir": "jaffle_shop"},
                "exclude": "customers",
            },
        ),
    )
    context = script_load_context(decl_node)
    component = DbtProjectComponent.load(
        attributes=decl_node.get_attributes(DbtProjectComponent.get_schema()), context=context
    )
    assert get_asset_keys(component) == set(JAFFLE_SHOP_KEYS) - {AssetKey("customers")}
