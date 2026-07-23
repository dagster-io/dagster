"""Shared utilities for dbt components (both local project and cloud)."""

import itertools
import json
import warnings
from collections.abc import Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, NewType

import dagster as dg
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import OpSpec
from dagster_shared import check

from dagster_dbt.asset_utils import (
    DAGSTER_DBT_EXCLUDE_METADATA_KEY,
    DAGSTER_DBT_SELECT_METADATA_KEY,
    DAGSTER_DBT_SELECTOR_METADATA_KEY,
    get_node,
    get_upstream_unique_ids,
)
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, DagsterDbtTranslatorSettings
from dagster_dbt.dbt_project import DbtProject

# Distinct NewType wrappers so a caller of `_remap_deps_for_overridden_keys` cannot
# silently pass the two translator roles in swapped order: the shim translator routes
# through any user override of `DbtProjectComponent.get_asset_spec`, while the base
# translator is the headless `DagsterDbtTranslator` instance used inside
# `DbtProjectComponent.get_asset_spec` for recursion (the source of the bug we are
# working around).
ShimDbtTranslator = NewType("ShimDbtTranslator", DagsterDbtTranslator)
BaseDbtTranslator = NewType("BaseDbtTranslator", DagsterDbtTranslator)

_resolution_context: ContextVar[ResolutionContext] = ContextVar("resolution_context")


@contextmanager
def _set_resolution_context(context: ResolutionContext):
    """Context manager to set the resolution context for dbt components."""
    token = _resolution_context.set(context)
    try:
        yield
    finally:
        _resolution_context.reset(token)


@dataclass(frozen=True)
class DagsterDbtComponentTranslatorSettings(DagsterDbtTranslatorSettings):
    """Subclass of DagsterDbtTranslatorSettings that enables code references by default."""

    enable_code_references: bool = True


def build_op_spec(
    op: OpSpec | None,
    select: str,
    exclude: str,
    selector: str,
    op_name: str,
) -> OpSpec:
    """Build an OpSpec with dbt selection tags injected."""
    default = op or OpSpec(name=op_name)
    return default.model_copy(
        update=dict(
            tags={
                **(default.tags or {}),
                **({DAGSTER_DBT_SELECT_METADATA_KEY: select} if select else {}),
                **({DAGSTER_DBT_EXCLUDE_METADATA_KEY: exclude} if exclude else {}),
                **({DAGSTER_DBT_SELECTOR_METADATA_KEY: selector} if selector else {}),
            }
        )
    )


def resolve_cli_args(
    cli_args: list[str | dict[str, Any]],
    context: dg.AssetExecutionContext,
) -> list[str]:
    """Resolve and normalize CLI args using the current resolution context and partition scope."""
    partition_key = context.partition_key if context.has_partition_key else None
    partition_key_range = context.partition_key_range if context.has_partition_key_range else None
    try:
        partition_time_window = context.partition_time_window
    except Exception:
        partition_time_window = None

    resolved_args = (
        _resolution_context.get()
        .with_scope(
            partition_key=partition_key,
            partition_key_range=partition_key_range,
            partition_time_window=partition_time_window,
        )
        .resolve_value(cli_args, as_type=list[str])
    )

    def _normalize_arg(arg: str | dict[str, Any]) -> list[str]:
        if isinstance(arg, str):
            return [arg]

        check.invariant(len(arg.keys()) == 1, "Invalid cli args dict, must have exactly one key")
        key = next(iter(arg.keys()))
        value = arg[key]
        if isinstance(value, dict):
            normalized_value = json.dumps(value)
        else:
            normalized_value = str(value)

        return [key, normalized_value]

    normalized_args = list(itertools.chain(*[list(_normalize_arg(arg)) for arg in resolved_args]))
    return normalized_args


def _remap_deps_for_overridden_keys(
    base_spec: dg.AssetSpec,
    *,
    shim_translator: ShimDbtTranslator,
    base_translator: BaseDbtTranslator,
    manifest: Mapping[str, Any],
    unique_id: str,
    project: DbtProject | None,
) -> dg.AssetSpec:
    """Rewrite ``base_spec.deps`` so an override of ``DbtProjectComponent.get_asset_spec``
    propagates to dependency asset keys.

    ``base_spec`` was produced by ``shim_translator``'s super-call: its key reflects
    the user override, but its deps were resolved against ``base_translator`` (a
    separate instance with no awareness of the override). For each upstream in the
    manifest, compare the base-translator key (what's currently in ``base_spec.deps``)
    with the shim-translator key (what should be there) and rewrite when they differ.
    Self-deps are remapped via ``base_translator.get_asset_key(resource_props) -> base_spec.key``.

    The two translator roles are wrapped in distinct ``NewType``s so a caller cannot
    pass them in swapped positions without a static type error; a runtime identity
    invariant is asserted as a defense in depth.

    Emits a warning when two upstreams collide onto the same new key (split-mapping is
    not supported; only the first mapping is applied), raises
    ``DagsterInvalidDefinitionError`` when a remap would introduce a spurious
    self-edge, and raises ``DagsterInvalidDefinitionError`` when source-key collapse
    discards a dep whose ``partition_mapping`` or ``metadata`` differs from the kept
    one (information loss).

    This is a surgical workaround for the headless ``_base_translator`` design in
    ``DbtProjectComponent`` / ``DbtCloudComponent``. The structural fix is to route
    component-level ``get_asset_spec`` recursion through the shim translator so this
    function becomes unnecessary; tracked as a follow-up in the PR description for
    issue dagster-io/dagster#33823.
    """
    check.invariant(
        shim_translator is not base_translator,
        "shim_translator and base_translator must be distinct instances; "
        "the helper assumes one routes through the user override and the other does not",
    )
    if not base_spec.deps:
        return base_spec

    resource_props = get_node(manifest, unique_id)
    upstream_ids = get_upstream_unique_ids(manifest, resource_props)

    correction: dict[dg.AssetKey, dg.AssetKey] = {}
    for upstream_id in upstream_ids:
        base_key = base_translator.get_asset_spec(manifest, upstream_id, project).key
        new_key = shim_translator.get_asset_spec(manifest, upstream_id, project).key
        if base_key == new_key:
            continue
        existing = correction.get(base_key)
        if existing is not None and existing != new_key:
            warnings.warn(
                f"DbtProjectComponent.get_asset_spec override produced multiple asset "
                f"keys for upstream base key {base_key.to_user_string()!r} on node "
                f"{unique_id!r}: {existing.to_user_string()!r} and "
                f"{new_key.to_user_string()!r}. Only the first mapping is applied to "
                f"deps; split-mappings are not supported. See "
                f"https://github.com/dagster-io/dagster/issues/33823.",
                stacklevel=4,
            )
            continue
        correction[base_key] = new_key

    base_self_key = base_translator.get_asset_key(resource_props)
    base_self_was_dep = base_self_key in {dep.asset_key for dep in base_spec.deps}
    if base_self_key != base_spec.key and base_self_key not in correction:
        correction[base_self_key] = base_spec.key

    if not correction:
        return base_spec

    new_deps: list[dg.AssetDep] = []
    kept_by_key: dict[dg.AssetKey, dg.AssetDep] = {}
    for dep in base_spec.deps:
        new_key = correction.get(dep.asset_key, dep.asset_key)
        if new_key == base_spec.key and not base_self_was_dep:
            raise dg.DagsterInvalidDefinitionError(
                f"DbtProjectComponent.get_asset_spec override remapped upstream "
                f"{dep.asset_key.to_user_string()!r} of {unique_id!r} to the same "
                f"key as the node itself ({new_key.to_user_string()!r}), which "
                f"would introduce a spurious self-dependency. Choose distinct keys."
            )
        new_dep = dg.AssetDep(
            asset=new_key,
            partition_mapping=dep.partition_mapping,
            metadata=dep.metadata,
        )
        existing_dep = kept_by_key.get(new_key)
        if existing_dep is not None:
            # Two distinct upstreams collapsed onto the same new key. Silently
            # discarding the second dep would lose information if partition_mapping
            # or metadata differ.
            if (
                existing_dep.partition_mapping != new_dep.partition_mapping
                or existing_dep.metadata != new_dep.metadata
            ):
                raise dg.DagsterInvalidDefinitionError(
                    f"DbtProjectComponent.get_asset_spec override on node "
                    f"{unique_id!r} collapsed two upstream deps onto the same asset "
                    f"key {new_key.to_user_string()!r} with diverging "
                    f"partition_mapping or metadata. Keeping one would silently "
                    f"drop information from the other. Resolve by either mapping "
                    f"these upstreams to distinct keys or by manually constructing "
                    f"the dep with the desired partition_mapping/metadata."
                )
            continue
        kept_by_key[new_key] = new_dep
        new_deps.append(new_dep)
    return base_spec.replace_attributes(deps=new_deps)
