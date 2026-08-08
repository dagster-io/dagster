import copy
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from unittest import mock

import pytest
from dagster._core.definitions.assets.graph.asset_graph import AssetGraph
from dagster._core.definitions.events import AssetKey
from dagster._record import replace
from dagster_dbt import DagsterDbtTranslator, DbtProject, build_dbt_asset_selection
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.asset_utils import DBT_DEFAULT_EXCLUDE, DBT_DEFAULT_SELECT
from dagster_dbt.compat import DBT_PYTHON_VERSION
from dagster_dbt.dbt_manifest_asset_selection import DbtManifestAssetSelection
from dagster_shared.check.functions import ParameterCheckError

from dagster_dbt_tests.dbt_projects import test_jaffle_shop_path

if TYPE_CHECKING:
    from dagster._core.definitions.asset_selection import AndAssetSelection


@pytest.mark.parametrize(
    ["select", "exclude", "expected_dbt_resource_names"],
    [
        (
            None,
            None,
            {
                "raw_customers",
                "raw_orders",
                "raw_payments",
                "stg_customers",
                "stg_orders",
                "stg_payments",
                "customers",
                "orders",
            },
        ),
        (
            "raw_customers stg_customers",
            None,
            {
                "raw_customers",
                "stg_customers",
            },
        ),
        (
            "raw_customers+",
            None,
            {
                "raw_customers",
                "stg_customers",
                "customers",
            },
        ),
        (
            "resource_type:model",
            None,
            {
                "stg_customers",
                "stg_orders",
                "stg_payments",
                "customers",
                "orders",
            },
        ),
        (
            "raw_customers+,resource_type:model",
            None,
            {
                "stg_customers",
                "customers",
            },
        ),
        (
            None,
            "orders",
            {
                "raw_customers",
                "raw_orders",
                "raw_payments",
                "stg_customers",
                "stg_orders",
                "stg_payments",
                "customers",
            },
        ),
        (
            None,
            "raw_customers+",
            {
                "raw_orders",
                "raw_payments",
                "stg_orders",
                "stg_payments",
                "orders",
            },
        ),
        (
            None,
            "raw_customers stg_customers",
            {
                "raw_orders",
                "raw_payments",
                "stg_orders",
                "stg_payments",
                "customers",
                "orders",
            },
        ),
        (
            None,
            "resource_type:model",
            {
                "raw_customers",
                "raw_orders",
                "raw_payments",
            },
        ),
        (
            None,
            "tag:does-not-exist",
            {
                "raw_customers",
                "raw_orders",
                "raw_payments",
                "stg_customers",
                "stg_orders",
                "stg_payments",
                "customers",
                "orders",
            },
        ),
    ],
    ids=[
        "--select fqn:*",
        "--select raw_customers stg_customers",
        "--select raw_customers+",
        "--select resource_type:model",
        "--select raw_customers+,resource_type:model",
        "--exclude orders",
        "--exclude raw_customers+",
        "--exclude raw_customers stg_customers",
        "--exclude resource_type:model",
        "--exclude tag:does-not-exist",
    ],
)
def test_dbt_asset_selection(
    test_jaffle_shop_manifest: dict[str, Any],
    select: str | None,
    exclude: str | None,
    expected_dbt_resource_names: set[str],
) -> None:
    expected_asset_keys = {AssetKey(key) for key in expected_dbt_resource_names}

    @dbt_assets(manifest=test_jaffle_shop_manifest)
    def my_dbt_assets(): ...

    asset_graph = AssetGraph.from_assets([my_dbt_assets])
    asset_selection = build_dbt_asset_selection(
        [my_dbt_assets],
        dbt_select=select or DBT_DEFAULT_SELECT,
        dbt_exclude=exclude or DBT_DEFAULT_EXCLUDE,
    )
    selected_asset_keys = asset_selection.resolve(all_assets=asset_graph)

    assert selected_asset_keys == expected_asset_keys


@pytest.mark.parametrize(
    ["select", "exclude", "expected_dbt_resource_names"],
    [
        (
            None,
            None,
            {
                "raw_customers",
                "stg_customers",
            },
        ),
        (
            "raw_customers",
            None,
            {
                "raw_customers",
            },
        ),
        (
            "customers",
            None,
            {},
        ),
        (
            None,
            "raw_customers",
            {"stg_customers"},
        ),
    ],
)
def test_dbt_asset_selection_on_asset_definition_with_existing_selection(
    test_jaffle_shop_manifest: dict[str, Any],
    select: str | None,
    exclude: str | None,
    expected_dbt_resource_names: set[str],
):
    expected_asset_keys = {AssetKey(key) for key in expected_dbt_resource_names}

    @dbt_assets(manifest=test_jaffle_shop_manifest, select="+stg_customers")
    def my_dbt_assets(): ...

    asset_graph = AssetGraph.from_assets([my_dbt_assets])
    asset_selection = build_dbt_asset_selection(
        [my_dbt_assets],
        dbt_select=select or DBT_DEFAULT_SELECT,
        dbt_exclude=exclude or DBT_DEFAULT_EXCLUDE,
    )
    selected_asset_keys = asset_selection.resolve(all_assets=asset_graph)

    assert selected_asset_keys == expected_asset_keys


def test_dbt_asset_selection_manifest_argument(
    test_jaffle_shop_manifest_path: Path, test_jaffle_shop_manifest: dict[str, Any]
) -> None:
    expected_asset_keys = {
        AssetKey(key)
        for key in {
            "raw_customers",
            "raw_orders",
            "raw_payments",
            "stg_customers",
            "stg_orders",
            "stg_payments",
            "customers",
            "orders",
        }
    }

    for manifest_param in [
        test_jaffle_shop_manifest,
        test_jaffle_shop_manifest_path,
        os.fspath(test_jaffle_shop_manifest_path),
    ]:

        @dbt_assets(manifest=manifest_param)
        def my_dbt_assets(): ...

        asset_graph = AssetGraph.from_assets([my_dbt_assets])
        asset_selection = build_dbt_asset_selection([my_dbt_assets], dbt_select="fqn:*")
        selected_asset_keys = asset_selection.resolve(all_assets=asset_graph)

        assert selected_asset_keys == expected_asset_keys


def test_dbt_asset_selection_equality(
    test_jaffle_shop_manifest_path: Path, test_jaffle_shop_manifest: dict[str, Any]
) -> None:
    for manifest_param in [
        test_jaffle_shop_manifest,
        test_jaffle_shop_manifest_path,
        os.fspath(test_jaffle_shop_manifest_path),
    ]:

        @dbt_assets(manifest=manifest_param)
        def my_dbt_assets(): ...

        asset_selection = build_dbt_asset_selection([my_dbt_assets], dbt_select="fqn:*")

        assert asset_selection == asset_selection

        assert asset_selection != build_dbt_asset_selection(
            [my_dbt_assets], dbt_select="new_select"
        )

        dbt_manifest_asset_selection = cast("AndAssetSelection", asset_selection).operands[0]

        assert isinstance(dbt_manifest_asset_selection, DbtManifestAssetSelection)

        altered_manifest = copy.deepcopy(dbt_manifest_asset_selection.manifest)
        altered_manifest["metadata"]["project_id"] = 12345

        assert dbt_manifest_asset_selection != replace(
            dbt_manifest_asset_selection,
            manifest=altered_manifest,
        )

        assert dbt_manifest_asset_selection != replace(
            dbt_manifest_asset_selection,
            select="other_select",
        )

        assert dbt_manifest_asset_selection != replace(
            dbt_manifest_asset_selection,
            dagster_dbt_translator=mock.MagicMock(spec=DagsterDbtTranslator),
        )

        assert dbt_manifest_asset_selection != replace(
            dbt_manifest_asset_selection,
            exclude="other_exclude",
        )

        # changing non-metadata fields does not affect equality
        altered_nodes_manifest = dict(copy.deepcopy(dbt_manifest_asset_selection.manifest))
        altered_nodes_manifest["nodes"] = []
        assert dbt_manifest_asset_selection == replace(
            dbt_manifest_asset_selection,
            manifest=altered_nodes_manifest,
        )


def test_dbt_asset_selection_selector(
    test_jaffle_shop_manifest: dict[str, Any],
) -> None:
    expected_asset_keys = {AssetKey(key) for key in {"stg_customers", "customers"}}

    # selector defined on the asset selection
    @dbt_assets(manifest=test_jaffle_shop_manifest)
    def all_dbt_assets(): ...

    asset_selection = build_dbt_asset_selection(
        [all_dbt_assets], dbt_selector="raw_customer_child_models"
    )
    selected_asset_keys = asset_selection.resolve([all_dbt_assets])
    assert selected_asset_keys == expected_asset_keys

    # selector defined on the assets definition
    @dbt_assets(manifest=test_jaffle_shop_manifest, selector="raw_customer_child_models")
    def selected_dbt_assets(): ...

    assert selected_dbt_assets.keys == expected_asset_keys

    asset_selection = build_dbt_asset_selection([selected_dbt_assets])
    selected_asset_keys = asset_selection.resolve([selected_dbt_assets])
    assert selected_asset_keys == expected_asset_keys


def test_dbt_asset_selection_path_selector_without_project_reproduces_issue(
    test_jaffle_shop_manifest: dict[str, Any],
) -> None:
    expected_asset_keys = {
        AssetKey(key)
        for key in {
            "raw_customers",
            "raw_orders",
            "raw_payments",
            "stg_customers",
            "stg_orders",
            "stg_payments",
            "customers",
            "orders",
        }
    }

    @dbt_assets(manifest=test_jaffle_shop_manifest)
    def my_dbt_assets(): ...

    fqn_asset_selection = build_dbt_asset_selection([my_dbt_assets], dbt_selector="select_with_fqn")
    fqn_selected_asset_keys = fqn_asset_selection.resolve([my_dbt_assets])
    assert fqn_selected_asset_keys == expected_asset_keys

    path_asset_selection = build_dbt_asset_selection(
        [my_dbt_assets], dbt_selector="select_with_path"
    )
    path_selected_asset_keys = path_asset_selection.resolve([my_dbt_assets])
    assert path_selected_asset_keys == set()


def test_dbt_asset_selection_path_selector_with_project(
    test_jaffle_shop_manifest: dict[str, Any],
) -> None:
    if (
        DBT_PYTHON_VERSION is not None
        and DBT_PYTHON_VERSION.major == 1
        and DBT_PYTHON_VERSION.minor == 7
    ):
        pytest.skip("dbt-core 1.7 does not expose dbt_common project-root contextvars")

    expected_asset_keys = {
        AssetKey(key)
        for key in {
            "raw_customers",
            "raw_orders",
            "raw_payments",
            "stg_customers",
            "stg_orders",
            "stg_payments",
            "customers",
            "orders",
        }
    }

    @dbt_assets(
        manifest=test_jaffle_shop_manifest,
        project=DbtProject(project_dir=test_jaffle_shop_path),
    )
    def my_dbt_assets(): ...

    path_asset_selection = build_dbt_asset_selection(
        [my_dbt_assets], dbt_selector="select_with_path"
    )
    path_selected_asset_keys = path_asset_selection.resolve([my_dbt_assets])
    assert path_selected_asset_keys == expected_asset_keys


def test_dbt_asset_selection_selector_invalid(
    test_jaffle_shop_manifest: dict[str, Any],
) -> None:
    with pytest.raises(ParameterCheckError):

        @dbt_assets(
            manifest=test_jaffle_shop_manifest,
            select="stg_customers",
            selector="raw_customer_child_models",
        )
        def selected_dbt_assets(): ...

    with pytest.raises(ParameterCheckError):

        @dbt_assets(
            manifest=test_jaffle_shop_manifest,
            exclude="stg_customers",
            selector="raw_customer_child_models",
        )
        def selected_dbt_assets(): ...

    with pytest.raises(ValueError):

        @dbt_assets(
            manifest=test_jaffle_shop_manifest,
            selector="fake_selector_does_not_exist",
        )
        def selected_dbt_assets(): ...


def _model_node(unique_id: str, name: str) -> dict[str, Any]:
    return {
        "unique_id": unique_id,
        "resource_type": "model",
        "name": name,
        "package_name": "test",
        "fqn": ["test", name],
        "path": f"{name}.sql",
        "original_file_path": f"models/{name}.sql",
        "tags": [],
        "config": {"enabled": True, "tags": [], "materialized": "table"},
        "depends_on": {"nodes": [], "macros": []},
    }


def _source_node(unique_id: str, source_name: str, name: str) -> dict[str, Any]:
    return {
        "unique_id": unique_id,
        "resource_type": "source",
        "source_name": source_name,
        "name": name,
        "package_name": "test",
        "fqn": ["test", source_name, name],
        "path": "sources.yml",
        "original_file_path": "models/sources.yml",
        "tags": [],
        "config": {"enabled": True, "tags": []},
    }


@pytest.mark.parametrize(
    "select, expected_unique_ids",
    [
        pytest.param("isolated", {"model.test.isolated"}, id="isolated-model-alone"),
        pytest.param(
            "fqn:*",
            {
                "model.test.parent",
                "model.test.child",
                "model.test.isolated",
            },
            id="broader-selector",
        ),
    ],
)
def test_select_unique_ids_includes_isolated_fusion_models(
    select: str, expected_unique_ids: set[str]
) -> None:
    """A dbt model with no ``source()``/``ref()`` calls (and nothing referencing it)
    is omitted from ``child_map`` by dbt-fusion manifests, unlike dbt-core which keys
    ``child_map`` by every node. Selection must still surface such isolated nodes
    rather than silently dropping them.

    Regression test for https://github.com/dagster-io/dagster/issues/33801.
    """
    from dagster_dbt.utils import _select_unique_ids_from_manifest

    manifest_json: dict[str, Any] = {
        "nodes": {
            "model.test.parent": _model_node("model.test.parent", "parent"),
            "model.test.child": _model_node("model.test.child", "child"),
            "model.test.isolated": _model_node("model.test.isolated", "isolated"),
        },
        "sources": {},
        "metrics": {},
        "exposures": {},
        # dbt-fusion-style child_map: the isolated model appears neither as a key
        # nor as a value, because it has no parents and no children.
        "child_map": {
            "model.test.parent": ["model.test.child"],
            "model.test.child": [],
        },
        "parent_map": {
            "model.test.parent": [],
            "model.test.child": ["model.test.parent"],
        },
    }

    selected = _select_unique_ids_from_manifest(
        select=select, exclude="", selector="", manifest_json=manifest_json
    )

    assert selected == expected_unique_ids


def test_select_unique_ids_includes_isolated_fusion_models_with_ref_source_graph() -> None:
    from dagster_dbt.utils import _select_unique_ids_from_manifest

    manifest_json: dict[str, Any] = {
        "nodes": {
            "model.test.uses_source": {
                **_model_node("model.test.uses_source", "uses_source"),
                "depends_on": {"nodes": ["source.test.raw.customers"], "macros": []},
            },
            "model.test.isolated": _model_node("model.test.isolated", "isolated"),
        },
        "sources": {
            "source.test.raw.customers": _source_node(
                "source.test.raw.customers", "raw", "customers"
            ),
        },
        "metrics": {},
        "exposures": {},
        # Mixed dbt-fusion-style graph: one model is connected to a source, while the
        # isolated model is absent from child_map because it has no parents or children.
        "child_map": {
            "source.test.raw.customers": ["model.test.uses_source"],
            "model.test.uses_source": [],
        },
        "parent_map": {
            "source.test.raw.customers": [],
            "model.test.uses_source": ["source.test.raw.customers"],
        },
    }

    selected = _select_unique_ids_from_manifest(
        select="fqn:*", exclude="", selector="", manifest_json=manifest_json
    )

    assert selected == {
        "model.test.uses_source",
        "model.test.isolated",
    }
