import shutil
import sys
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

import pytest
from dagster import AssetKey, AssetSpec, BackfillPolicy
from dagster._core.definitions.backfill_policy import BackfillPolicyType
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster.components.core.load_defs import build_component_defs
from dagster.components.resolved.core_models import AssetAttributesModel
from dagster_dbt import DbtProject, DbtProjectComponent

ensure_dagster_tests_import()

from dagster_tests.components_tests.integration_tests.component_loader import (
    load_test_component_defs,
)
from dagster_tests.components_tests.utils import build_component_defs_for_test

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


@contextmanager
@pytest.fixture(scope="module")
def dbt_path() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copytree(STUB_LOCATION_PATH, temp_dir, dirs_exist_ok=True)
        # make sure a manifest.json file is created
        dbt_path = Path(temp_dir) / "defs/jaffle_shop_dbt/jaffle_shop"
        project = DbtProject(dbt_path)
        project.preparer.prepare(project)
        yield dbt_path


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
            "dbt": {"project_dir": dbt_path},
            "op": {"name": "some_op", "tags": {"tag1": "value"}, **backfill_policy_arg},
        },
    )
    assert defs.get_asset_graph().get_all_asset_keys() == JAFFLE_SHOP_KEYS
    assets_def = defs.get_assets_def("stg_customers")
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
    with load_test_component_defs(dbt_path.parent.parent.parent) as defs:
        assert defs.get_asset_graph().get_all_asset_keys() == JAFFLE_SHOP_KEYS

        for asset_node in defs.get_asset_graph().asset_nodes:
            assert asset_node.tags["foo"] == "bar"
            assert asset_node.tags["another"] == "one"
            assert asset_node.metadata["something"] == 1


def test_dbt_subclass_additional_scope_fn(dbt_path: Path) -> None:
    @dataclass
    class DebugDbtProjectComponent(DbtProjectComponent):
        @classmethod
        def get_additional_scope(cls) -> Mapping[str, Any]:
            return {"get_tags_for_node": lambda node: {"model_id": node["name"].replace("_", "-")}}

    defs = build_component_defs_for_test(
        DebugDbtProjectComponent,
        {
            "dbt": {"project_dir": dbt_path},
            "asset_attributes": {"tags": "{{ get_tags_for_node(node) }}"},
        },
    )
    assets_def = defs.get_assets_def(AssetKey("stg_customers"))
    assert assets_def.get_asset_spec(AssetKey("stg_customers")).tags["model_id"] == "stg-customers"


@pytest.mark.parametrize(
    "attributes, assertion, should_error",
    [
        ({"group_name": "group"}, lambda asset_spec: asset_spec.group_name == "group", False),
        (
            {"owners": ["team:analytics"]},
            lambda asset_spec: asset_spec.owners == ["team:analytics"],
            False,
        ),
        ({"tags": {"foo": "bar"}}, lambda asset_spec: asset_spec.tags.get("foo") == "bar", False),
        (
            {"kinds": ["snowflake"]},
            lambda asset_spec: "snowflake" in asset_spec.kinds
            and "dbt" in asset_spec.kinds,  # Ensure dbt-specific kind is not overwritten
            False,
        ),
        (
            {"tags": {"foo": "bar"}, "kinds": ["snowflake"]},
            lambda asset_spec: "snowflake" in asset_spec.kinds
            and "dbt" in asset_spec.kinds  # Ensure dbt-specific kind is not overwritten
            and asset_spec.tags.get("foo") == "bar",
            False,
        ),
        ({"code_version": "1"}, lambda asset_spec: asset_spec.code_version == "1", False),
        (
            {"description": "some description"},
            lambda asset_spec: asset_spec.description == "some description",
            False,
        ),
        (
            {"metadata": {"foo": "bar"}},
            lambda asset_spec: asset_spec.metadata.get("foo") == "bar"
            and "dagster-dbt/materialization_type"
            in asset_spec.metadata,  # Ensure dagster-dbt populated metadata is not overwritten
            False,
        ),
        ({"deps": ["customers"]}, None, True),
        (
            {"automation_condition": "{{ automation_condition.eager() }}"},
            lambda asset_spec: asset_spec.automation_condition is not None,
            False,
        ),
        (
            {"key": "{{ node.name }}"},
            lambda asset_spec: asset_spec.key == AssetKey("stg_customers"),
            False,
        ),
    ],
    ids=[
        "group_name",
        "owners",
        "tags",
        "kinds",
        "tags-and-kinds",
        "code-version",
        "description",
        "metadata",
        "deps",
        "automation_condition",
        "key",
    ],
)
def test_asset_attributes(
    dbt_path: Path,
    attributes: Mapping[str, Any],
    assertion: Optional[Callable[[AssetSpec], bool]],
    should_error: bool,
) -> None:
    wrapper = pytest.raises(Exception) if should_error else nullcontext()
    with wrapper:
        defs = build_component_defs_for_test(
            DbtProjectComponent,
            {
                "dbt": {"project_dir": dbt_path},
                "asset_attributes": attributes,
            },
        )
        assert defs.get_asset_graph().get_all_asset_keys() == JAFFLE_SHOP_KEYS
        assets_def = defs.get_assets_def("stg_customers")
    if assertion:
        assert assertion(assets_def.get_asset_spec(AssetKey("stg_customers")))


IGNORED_KEYS = {"skippable"}


def test_asset_attributes_is_comprehensive():
    all_asset_attribute_keys = []
    for test_arg in test_asset_attributes.pytestmark[0].args[1]:  # pyright: ignore[reportFunctionMemberAccess]
        all_asset_attribute_keys.extend(test_arg[0].keys())
    from dagster.components.resolved.core_models import AssetAttributesModel

    assert (
        set(AssetAttributesModel.model_fields.keys()) - IGNORED_KEYS
        == set(all_asset_attribute_keys)
    ), f"The test_asset_attributes test does not cover all fields, missing: {set(AssetAttributesModel.model_fields.keys()) - IGNORED_KEYS - set(all_asset_attribute_keys)}"


def test_subselection(dbt_path: Path) -> None:
    defs = build_component_defs_for_test(
        DbtProjectComponent,
        {"dbt": {"project_dir": dbt_path}, "select": "raw_customers"},
    )
    assert defs.get_asset_graph().get_all_asset_keys() == {AssetKey("raw_customers")}


def test_exclude(dbt_path: Path) -> None:
    defs = build_component_defs_for_test(
        DbtProjectComponent,
        {"dbt": {"project_dir": dbt_path}, "exclude": "customers"},
    )
    assert defs.get_asset_graph().get_all_asset_keys() == JAFFLE_SHOP_KEYS - {AssetKey("customers")}


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
    assert AssetKey("downstream_of_customers") in defs.get_asset_graph().get_all_asset_keys()
    downstream_of_customers_def = defs.get_assets_def("downstream_of_customers")
    assert set(downstream_of_customers_def.asset_deps[AssetKey("downstream_of_customers")]) == {
        AssetKey("customers")
    }


def test_spec_is_available_in_scope(dbt_path: Path) -> None:
    defs = build_component_defs_for_test(
        DbtProjectComponent,
        {
            "dbt": {"project_dir": dbt_path},
            "asset_attributes": {"metadata": {"asset_key": "{{ spec.key.path }}"}},
        },
    )
    assets_def = defs.get_assets_def(AssetKey("stg_customers"))
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
            "dbt": {"project_dir": dbt_path},
            "asset_attributes": "{{ map_spec(spec) }}",
        },
    )
    assets_def = defs.get_assets_def(AssetKey("stg_customers"))
    assert assets_def.get_asset_spec(AssetKey("stg_customers")).tags["is_custom_spec"] == "yes"
