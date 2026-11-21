"""Unit tests for :func:`_remap_deps_for_overridden_keys`.

These tests exercise the helper directly with a synthetic dbt manifest so we can
cover edge cases (custom partition mappings, source-key collapse, cycle introduction)
that the existing jaffle_shop fixture does not produce naturally.
"""

from collections.abc import Mapping
from typing import Any
from unittest.mock import MagicMock

import dagster as dg
import pytest
from dagster_dbt.components.dbt_component_utils import (
    BaseDbtTranslator,
    ShimDbtTranslator,
    _remap_deps_for_overridden_keys,
)
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator


def _build_manifest() -> Mapping[str, Any]:
    """A minimal manifest with two models: `child` depends on `parent`."""
    return {
        "nodes": {
            "model.proj.child": {
                "unique_id": "model.proj.child",
                "name": "child",
                "fqn": ["proj", "child"],
                "resource_type": "model",
                "depends_on": {"nodes": ["model.proj.parent"]},
                "meta": {},
                "config": {},
                "tags": [],
            },
            "model.proj.parent": {
                "unique_id": "model.proj.parent",
                "name": "parent",
                "fqn": ["proj", "parent"],
                "resource_type": "model",
                "depends_on": {"nodes": []},
                "meta": {},
                "config": {},
                "tags": [],
            },
        },
        "sources": {},
        "metadata": {"project_name": "proj"},
        "parent_map": {"model.proj.child": ["model.proj.parent"]},
        "child_map": {"model.proj.parent": ["model.proj.child"]},
    }


def _prefix_shim(base_translator: DagsterDbtTranslator) -> MagicMock:
    """A shim translator that prefixes every asset key with 'new'."""
    shim = MagicMock(spec=DagsterDbtTranslator)
    shim.get_asset_spec.side_effect = lambda m, uid, p: base_translator.get_asset_spec(
        m, uid, p
    ).replace_attributes(key=base_translator.get_asset_spec(m, uid, p).key.with_prefix("new"))
    return shim


def test_remap_preserves_custom_partition_mapping() -> None:
    """A user override that remaps keys must preserve a non-default partition_mapping
    on the rewritten dep. Regression test for the case Owen Kephart flagged: the
    jaffle_shop fixture has only None partition_mappings, so this exercises the path
    directly with a TimeWindowPartitionMapping.
    """
    manifest = _build_manifest()
    base_translator = DagsterDbtTranslator()
    shim = _prefix_shim(base_translator)

    base_spec = base_translator.get_asset_spec(manifest, "model.proj.child", None)
    custom_mapping = dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
    base_spec_with_custom = base_spec.replace_attributes(
        deps=[
            dg.AssetDep(
                asset=dep.asset_key,
                partition_mapping=custom_mapping,
                metadata={"source_name": dg.MetadataValue.text("custom")},
            )
            for dep in base_spec.deps
        ],
        key=base_spec.key.with_prefix("new"),
    )

    remapped = _remap_deps_for_overridden_keys(
        base_spec_with_custom,
        shim_translator=ShimDbtTranslator(shim),
        base_translator=BaseDbtTranslator(base_translator),
        manifest=manifest,
        unique_id="model.proj.child",
        project=None,
    )

    remapped_deps = list(remapped.deps)
    assert len(remapped_deps) == 1
    new_dep = remapped_deps[0]
    assert new_dep.asset_key == dg.AssetKey(["new", "parent"])
    assert new_dep.partition_mapping == custom_mapping
    assert new_dep.metadata == {"source_name": dg.MetadataValue.text("custom")}


def test_remap_source_key_collapse_with_matching_dep_collapses_silently() -> None:
    """When two upstreams collapse onto the same new key but their partition_mapping
    and metadata match, dedup silently — no error.
    """
    manifest = _build_manifest()
    # Add a second parent so child has two upstream IDs that both collapse to 'parent'.
    manifest["nodes"]["model.proj.parent2"] = {
        "unique_id": "model.proj.parent2",
        "name": "parent2",
        "fqn": ["proj", "parent2"],
        "resource_type": "model",
        "depends_on": {"nodes": []},
        "meta": {},
        "config": {},
        "tags": [],
    }
    manifest["nodes"]["model.proj.child"]["depends_on"]["nodes"] = [
        "model.proj.parent",
        "model.proj.parent2",
    ]
    manifest["parent_map"]["model.proj.child"] = ["model.proj.parent", "model.proj.parent2"]
    base_translator = DagsterDbtTranslator()

    # Shim collapses both parents onto the same new key.
    shim = MagicMock(spec=DagsterDbtTranslator)
    shim.get_asset_spec.side_effect = lambda m, uid, p: base_translator.get_asset_spec(
        m, uid, p
    ).replace_attributes(key=dg.AssetKey(["merged", "parent"]))

    base_spec = base_translator.get_asset_spec(manifest, "model.proj.child", None)
    base_spec = base_spec.replace_attributes(key=dg.AssetKey(["merged", "child"]))

    remapped = _remap_deps_for_overridden_keys(
        base_spec,
        shim_translator=ShimDbtTranslator(shim),
        base_translator=BaseDbtTranslator(base_translator),
        manifest=manifest,
        unique_id="model.proj.child",
        project=None,
    )
    remapped_deps = list(remapped.deps)
    assert len(remapped_deps) == 1
    assert remapped_deps[0].asset_key == dg.AssetKey(["merged", "parent"])


def test_remap_source_key_collapse_with_divergent_metadata_raises() -> None:
    """When two upstreams collapse onto the same new key but their partition_mapping
    or metadata diverge, raise rather than silently drop information.

    Regression test for Owen Kephart's review comment on the silent-drop behavior.
    """
    manifest = _build_manifest()
    manifest["nodes"]["model.proj.parent2"] = {
        "unique_id": "model.proj.parent2",
        "name": "parent2",
        "fqn": ["proj", "parent2"],
        "resource_type": "model",
        "depends_on": {"nodes": []},
        "meta": {},
        "config": {},
        "tags": [],
    }
    manifest["nodes"]["model.proj.child"]["depends_on"]["nodes"] = [
        "model.proj.parent",
        "model.proj.parent2",
    ]
    manifest["parent_map"]["model.proj.child"] = ["model.proj.parent", "model.proj.parent2"]
    base_translator = DagsterDbtTranslator()
    shim = MagicMock(spec=DagsterDbtTranslator)
    shim.get_asset_spec.side_effect = lambda m, uid, p: base_translator.get_asset_spec(
        m, uid, p
    ).replace_attributes(key=dg.AssetKey(["merged", "parent"]))

    base_spec = base_translator.get_asset_spec(manifest, "model.proj.child", None)
    # Make the two deps disagree on metadata so collapse would lose info.
    base_spec = base_spec.replace_attributes(
        key=dg.AssetKey(["merged", "child"]),
        deps=[
            dg.AssetDep(
                asset=dg.AssetKey(["parent"]),
                metadata={"source": dg.MetadataValue.text("a")},
            ),
            dg.AssetDep(
                asset=dg.AssetKey(["parent2"]),
                metadata={"source": dg.MetadataValue.text("b")},
            ),
        ],
    )
    with pytest.raises(
        dg.DagsterInvalidDefinitionError, match="diverging partition_mapping or metadata"
    ):
        _remap_deps_for_overridden_keys(
            base_spec,
            shim_translator=ShimDbtTranslator(shim),
            base_translator=BaseDbtTranslator(base_translator),
            manifest=manifest,
            unique_id="model.proj.child",
            project=None,
        )


def test_remap_swap_of_shim_and_base_raises() -> None:
    """Passing the same translator instance as both shim and base must fail loudly.

    The NewType wrappers make this a static type error at well-behaved call sites;
    this test deliberately bypasses the type system (the # type: ignore below) to
    exercise the runtime invariant as defense in depth.
    """
    manifest = _build_manifest()
    base_translator = DagsterDbtTranslator()
    base_spec = base_translator.get_asset_spec(manifest, "model.proj.child", None)
    with pytest.raises(Exception, match="distinct instances"):
        _remap_deps_for_overridden_keys(
            base_spec,
            shim_translator=base_translator,  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]
            base_translator=base_translator,  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]
            manifest=manifest,
            unique_id="model.proj.child",
            project=None,
        )
