from collections.abc import Mapping, Sequence
from typing import Any

from dagster import AssetDep, AssetKey, AssetSpec
from dagster._core.definitions.assets.definition.asset_spec import (
    SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET,
)
from dagster._utils.tags import is_valid_tag_key

from dagster_dbt.asset_utils import (
    DAGSTER_DBT_UNIQUE_ID_METADATA_KEY,
    DBT_DEFAULT_EXCLUDE,
    DBT_DEFAULT_SELECT,
    DBT_DEFAULT_SELECTOR,
    build_dbt_specs,
    get_node,
)
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, validate_translator
from dagster_dbt.dbt_manifest import DbtManifestParam, validate_manifest
from dagster_dbt.dbt_project import DbtProject

DAGSTER_DBT_EXPOSURE_TYPE_METADATA_KEY = "dagster_dbt/exposure_type"
DAGSTER_DBT_EXPOSURE_URL_METADATA_KEY = "dagster_dbt/exposure_url"
DAGSTER_DBT_EXPOSURE_MATURITY_METADATA_KEY = "dagster_dbt/exposure_maturity"

DAGSTER_DBT_SEMANTIC_MODEL_MEASURES_METADATA_KEY = "dagster_dbt/measures"
DAGSTER_DBT_SEMANTIC_MODEL_DIMENSIONS_METADATA_KEY = "dagster_dbt/dimensions"
DAGSTER_DBT_SEMANTIC_MODEL_ENTITIES_METADATA_KEY = "dagster_dbt/entities"
DAGSTER_DBT_METRIC_TYPE_METADATA_KEY = "dagster_dbt/metric_type"
DAGSTER_DBT_METRIC_LABEL_METADATA_KEY = "dagster_dbt/metric_label"

DAGSTER_DBT_EXTERNAL_PACKAGE_METADATA_KEY = "dagster_dbt/external_package"


# dbt exposure types (https://docs.getdbt.com/reference/exposure-properties#type):
# dashboard, notebook, analysis, ml, application. We map each to a kind that
# Dagster's UI can render with a distinct icon.
_DBT_EXPOSURE_TYPE_TO_KIND: Mapping[str, str] = {
    "dashboard": "dashboard",
    "notebook": "notebook",
    "analysis": "analysis",
    "ml": "ml",
    "application": "application",
}


def build_dbt_asset_specs(
    *,
    manifest: DbtManifestParam,
    dagster_dbt_translator: DagsterDbtTranslator | None = None,
    select: str = DBT_DEFAULT_SELECT,
    exclude: str | None = DBT_DEFAULT_EXCLUDE,
    selector: str | None = DBT_DEFAULT_SELECTOR,
    project: DbtProject | None = None,
) -> Sequence[AssetSpec]:
    """Build a list of asset specs from a set of dbt resources selected from a dbt manifest.

    Args:
        manifest (Union[Mapping[str, Any], str, Path]): The contents of a manifest.json file
            or the path to a manifest.json file. A manifest.json contains a representation of a
            dbt project (models, tests, macros, etc). We use this representation to create
            corresponding Dagster asset specs.
        dagster_dbt_translator (Optional[DagsterDbtTranslator]): Allows customizing how to map
            dbt models, seeds, etc. to asset keys and asset metadata.
        select (str): A dbt selection string for the models in a project that you want
            to include. Defaults to ``fqn:*``.
        exclude (Optional[str]): A dbt selection string for the models in a project that you want
            to exclude. Defaults to "".
        selector (Optional[str]): A dbt selector for the models in a project that you want
            to include. Defaults to None.
        project (Optional[DbtProject]): A DbtProject instance which provides a pointer to the dbt
            project location and manifest. Not required, but needed to attach code references from
            model code to Dagster assets.

    Returns:
        Sequence[AssetSpec]: A list of asset specs.
    """
    manifest = validate_manifest(manifest)
    dagster_dbt_translator = validate_translator(dagster_dbt_translator or DagsterDbtTranslator())

    specs, _ = build_dbt_specs(
        manifest=manifest,
        translator=dagster_dbt_translator,
        select=select,
        exclude=exclude or DBT_DEFAULT_EXCLUDE,
        selector=selector or DBT_DEFAULT_SELECTOR,
        io_manager_key=None,
        project=project,
    )

    return specs


def build_dbt_source_asset_specs(
    *,
    manifest: DbtManifestParam,
    dagster_dbt_translator: DagsterDbtTranslator | None = None,
    project: DbtProject | None = None,
) -> Sequence[AssetSpec]:
    """Build external (observable, non-materializable) ``AssetSpec`` objects for every dbt
    source declared in the manifest.

    Sources are emitted as bare ``AssetSpec`` instances so that passing them to
    :py:class:`dagster.Definitions` yields observable external assets rather than
    materializable ones. When another Dagster integration (Fivetran, Sling, a manual
    ``AssetSpec``, etc.) declares an asset with the same :py:class:`dagster.AssetKey`,
    Dagster merges the two — dbt's contribution (freshness policy, table schema, tags)
    layers on top without conflicting with the upstream materializer.

    Automatic derivations that flow through the translator (freshness policies from
    ``sources.freshness``, table metadata, kinds, code references, etc.) apply to the
    returned specs.

    Multiple dbt sources that collapse to the same ``AssetKey`` (see the
    ``enable_duplicate_source_asset_keys`` translator setting) are de-duplicated first-wins.

    Args:
        manifest: The contents of a ``manifest.json`` file or the path to one.
        dagster_dbt_translator: Optional translator; defaults to :py:class:`DagsterDbtTranslator`.
        project: Optional :py:class:`DbtProject` — needed for code references.

    Returns:
        Sequence[AssetSpec]: One ``AssetSpec`` per unique source ``AssetKey`` in the manifest.
    """
    manifest = validate_manifest(manifest)
    translator = validate_translator(dagster_dbt_translator or DagsterDbtTranslator())

    seen: set[AssetKey] = set()
    specs: list[AssetSpec] = []
    for source_unique_id in manifest.get("sources", {}):
        spec = translator.get_asset_spec(manifest, source_unique_id, project)
        if spec.key in seen:
            continue
        seen.add(spec.key)
        # Tag as an auto-created stub so that any explicit user declaration at the same
        # AssetKey (Fivetran, Sling, a manual observable_source_asset) takes precedence
        # per Dagster's asset-node precedence order (materializable > observable > non-stub).
        # dbt-derived metadata (freshness policy, table schema, kinds) still travels with the
        # spec and merges into the winning declaration.
        specs.append(
            spec.merge_attributes(metadata={SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET: True})
        )

    return specs


def _dep_asset_key_for_exposure_upstream(
    manifest: Mapping[str, Any],
    translator: DagsterDbtTranslator,
    upstream_unique_id: str,
) -> AssetKey | None:
    """Resolve the Dagster ``AssetKey`` for one entry in an exposure's ``depends_on.nodes``.

    Exposures depend on models, sources, seeds, snapshots, and (rarely) metrics. Anything
    the ``get_node`` lookup can find + that the translator produces a key for becomes a
    dep. Missing / non-existent references are silently skipped rather than raising, since
    dbt manifests occasionally carry stale references.
    """
    try:
        upstream_props = get_node(manifest, upstream_unique_id)
    except Exception:
        return None
    return translator.get_asset_key(upstream_props)


def build_dbt_exposure_asset_specs(
    *,
    manifest: DbtManifestParam,
    dagster_dbt_translator: DagsterDbtTranslator | None = None,
    project: DbtProject | None = None,
) -> Sequence[AssetSpec]:
    """Build observable external ``AssetSpec`` objects for every dbt exposure declared in
    ``exposures.yml``.

    Each exposure becomes a downstream node in the Dagster graph, with deps on the
    referenced upstream models (from ``depends_on.nodes``). Exposures are NOT materialized
    by Dagster — they are external artifacts (BI dashboards, notebooks, ML models,
    applications) declared in dbt so users can trace "if this model breaks, which
    dashboards are affected?" in the graph.

    Kind is derived from ``exposure.type`` (dashboard / notebook / analysis / application
    / ml) so the Dagster UI renders a distinct icon per exposure type.

    Metadata surfaced (under the ``dagster_dbt/`` namespace):

    - ``exposure_type`` (str): the raw ``exposure.type`` value from dbt.
    - ``exposure_url`` (str): the ``exposure.url`` — link to the actual dashboard /
      notebook so users can navigate from Dagster.
    - ``exposure_maturity`` (str): ``low`` / ``medium`` / ``high`` per dbt's exposure
      maturity taxonomy.
    - ``unique_id`` (str): the dbt ``unique_id`` (e.g. ``exposure.my_project.dash``).

    Owners are pulled from ``exposure.owner.email`` when present. Tags are copied from
    ``exposure.tags``.

    The ``AssetKey`` is derived via ``translator.get_asset_key`` (which honors
    ``meta.dagster.asset_key`` on the exposure); by default this collapses to the raw
    exposure name.

    Args:
        manifest: The contents of a ``manifest.json`` file or the path to one.
        dagster_dbt_translator: Optional translator; defaults to :py:class:`DagsterDbtTranslator`.
        project: Reserved for future use (code references); currently unused.

    Returns:
        Sequence[AssetSpec]: One ``AssetSpec`` per exposure in the manifest.
    """
    del project  # currently unused; kept in signature to match the source-spec helper
    manifest = validate_manifest(manifest)
    translator = validate_translator(dagster_dbt_translator or DagsterDbtTranslator())

    specs: list[AssetSpec] = []
    for exposure_unique_id, exposure_props in manifest.get("exposures", {}).items():
        exposure_type = str(exposure_props.get("type") or "").lower()
        kind = _DBT_EXPOSURE_TYPE_TO_KIND.get(exposure_type)
        kinds = {kind} if kind else None

        deps: list[AssetDep] = []
        seen_dep_keys: set[AssetKey] = set()
        for upstream_unique_id in exposure_props.get("depends_on", {}).get("nodes", []) or []:
            upstream_key = _dep_asset_key_for_exposure_upstream(
                manifest, translator, upstream_unique_id
            )
            if upstream_key is None or upstream_key in seen_dep_keys:
                continue
            seen_dep_keys.add(upstream_key)
            deps.append(AssetDep(asset=upstream_key))

        owner_config = exposure_props.get("owner") or {}
        owner_email = owner_config.get("email")
        owners = [owner_email] if isinstance(owner_email, str) and owner_email else None

        tags = {
            tag: ""
            for tag in exposure_props.get("tags") or []
            if isinstance(tag, str) and is_valid_tag_key(tag)
        }

        metadata: dict[str, Any] = {
            DAGSTER_DBT_UNIQUE_ID_METADATA_KEY: exposure_unique_id,
            DAGSTER_DBT_EXPOSURE_TYPE_METADATA_KEY: exposure_type or "",
        }
        url = exposure_props.get("url")
        if isinstance(url, str) and url:
            metadata[DAGSTER_DBT_EXPOSURE_URL_METADATA_KEY] = url
        maturity = exposure_props.get("maturity")
        if isinstance(maturity, str) and maturity:
            metadata[DAGSTER_DBT_EXPOSURE_MATURITY_METADATA_KEY] = maturity

        specs.append(
            AssetSpec(
                key=translator.get_asset_key(exposure_props),
                deps=deps,
                description=exposure_props.get("description"),
                metadata=metadata,
                owners=owners,
                tags=tags,
                kinds=kinds,
            )
        )

    return specs


def _semantic_layer_deps(
    manifest: Mapping[str, Any],
    translator: DagsterDbtTranslator,
    props: Mapping[str, Any],
) -> list[AssetDep]:
    """Build AssetDep list from a semantic_model or metric's ``depends_on.nodes``."""
    deps: list[AssetDep] = []
    seen: set[AssetKey] = set()
    for upstream_id in props.get("depends_on", {}).get("nodes", []) or []:
        try:
            upstream_props = get_node(manifest, upstream_id)
        except Exception:
            continue
        upstream_key = translator.get_asset_key(upstream_props)
        if upstream_key in seen:
            continue
        seen.add(upstream_key)
        deps.append(AssetDep(asset=upstream_key))
    return deps


def build_dbt_semantic_layer_asset_specs(
    *,
    manifest: DbtManifestParam,
    dagster_dbt_translator: DagsterDbtTranslator | None = None,
    project: DbtProject | None = None,
) -> Sequence[AssetSpec]:
    """Build observable external ``AssetSpec`` objects for every dbt ``semantic_model`` and
    ``metric`` declared in the manifest.

    dbt's semantic layer represents entities, dimensions, measures, and metrics that sit
    on top of models. Surfacing them as Dagster ``AssetSpec`` objects lets users:

    - See semantic_models and metrics in the graph with their upstream lineage back to
      the models they're built from.
    - Query on them via ``kind:semantic_model`` / ``kind:metric`` asset selections.
    - Layer freshness / owners / tags on top via ``post_processing:``.

    Emitted specs are NOT materialized by Dagster — the semantic layer is queried
    (typically via dbt Cloud's semantic layer API) rather than materialized. ``AssetSpec``
    without an ``op`` behaves as an observable external asset.

    Semantic models are keyed via ``translator.get_asset_key`` (which honors
    ``meta.dagster.asset_key`` overrides). Metrics likewise.

    Metadata surfaced (under the ``dagster_dbt/`` namespace):

    - semantic_model specs: ``measures`` (list of measure names), ``dimensions`` (list of
      dimension names), ``entities`` (list of entity names).
    - metric specs: ``metric_type`` (``simple`` / ``ratio`` / ``cumulative`` / ``derived``),
      ``metric_label`` (human-readable label from dbt).

    Args:
        manifest: The contents of a ``manifest.json`` file or the path to one.
        dagster_dbt_translator: Optional translator; defaults to :py:class:`DagsterDbtTranslator`.
        project: Reserved for future use; currently unused.

    Returns:
        Sequence[AssetSpec]: One ``AssetSpec`` per semantic_model and metric.
    """
    del project  # currently unused; kept in signature for parity with source/exposure helpers
    manifest = validate_manifest(manifest)
    translator = validate_translator(dagster_dbt_translator or DagsterDbtTranslator())

    specs: list[AssetSpec] = []

    for semantic_model_unique_id, props in (manifest.get("semantic_models") or {}).items():
        deps = _semantic_layer_deps(manifest, translator, props)
        measures = [m.get("name") for m in (props.get("measures") or []) if m.get("name")]
        dimensions = [d.get("name") for d in (props.get("dimensions") or []) if d.get("name")]
        entities = [e.get("name") for e in (props.get("entities") or []) if e.get("name")]

        metadata: dict[str, Any] = {
            DAGSTER_DBT_UNIQUE_ID_METADATA_KEY: semantic_model_unique_id,
            DAGSTER_DBT_SEMANTIC_MODEL_MEASURES_METADATA_KEY: measures,
            DAGSTER_DBT_SEMANTIC_MODEL_DIMENSIONS_METADATA_KEY: dimensions,
            DAGSTER_DBT_SEMANTIC_MODEL_ENTITIES_METADATA_KEY: entities,
        }

        specs.append(
            AssetSpec(
                key=translator.get_asset_key(props),
                deps=deps,
                description=props.get("description"),
                metadata=metadata,
                kinds={"semantic_model"},
            )
        )

    for metric_unique_id, props in (manifest.get("metrics") or {}).items():
        deps = _semantic_layer_deps(manifest, translator, props)
        metric_type = str(props.get("type") or "").lower()
        metadata = {
            DAGSTER_DBT_UNIQUE_ID_METADATA_KEY: metric_unique_id,
            DAGSTER_DBT_METRIC_TYPE_METADATA_KEY: metric_type,
        }
        label = props.get("label")
        if isinstance(label, str) and label:
            metadata[DAGSTER_DBT_METRIC_LABEL_METADATA_KEY] = label

        specs.append(
            AssetSpec(
                key=translator.get_asset_key(props),
                deps=deps,
                description=props.get("description"),
                metadata=metadata,
                kinds={"metric"},
            )
        )

    return specs


def build_dbt_external_package_asset_specs(
    *,
    manifest: DbtManifestParam,
    external_packages: Sequence[str],
    dagster_dbt_translator: DagsterDbtTranslator | None = None,
    project: DbtProject | None = None,
) -> Sequence[AssetSpec]:
    """Emit observable external stub ``AssetSpec`` objects for every dbt model whose
    ``package_name`` matches one of ``external_packages`` (dbt mesh case).

    Purpose: when a dbt project imports another dbt project as a package (dbt mesh), the
    imported package's models appear in the manifest but the CURRENT project doesn't own
    them — they're managed by a separate Dagster code location for the upstream project.
    Emitting them as observable stub specs lets downstream models in this project's graph
    show their upstream lineage, and lets the upstream project's Dagster code location
    merge with these stubs (auto-stub marker ensures the upstream's non-stub declaration
    wins per Dagster's asset-node precedence order).

    Callers should typically ALSO exclude external-package models from their materializable
    graph (via ``exclude: "package:X"`` on the component). The two work together:

    - ``exclude`` prevents the model from becoming part of the ``@dbt_assets`` op (so
      running the current project's dbt command doesn't try to rebuild the upstream).
    - ``build_dbt_external_package_asset_specs`` emits the stub spec so downstream lineage
      is still visible.

    Metadata surfaced:

    - ``dagster_dbt/unique_id``: the dbt unique_id of the model.
    - ``dagster_dbt/external_package``: the package name that owns this model.
    - ``dagster_dbt/table_name`` and column schema (via the shared translator metadata).

    Args:
        manifest: The contents of a ``manifest.json`` file or the path to one.
        external_packages: List of dbt package names to emit external stub specs for.
        dagster_dbt_translator: Optional translator; defaults to :py:class:`DagsterDbtTranslator`.
        project: Optional :py:class:`DbtProject` (used for code references).

    Returns:
        Sequence[AssetSpec]: One ``AssetSpec`` per model whose ``package_name`` is in
        ``external_packages``, deduplicated by ``AssetKey`` first-wins.
    """
    if not external_packages:
        return []
    manifest = validate_manifest(manifest)
    translator = validate_translator(dagster_dbt_translator or DagsterDbtTranslator())
    external_package_set = set(external_packages)

    seen: set[AssetKey] = set()
    specs: list[AssetSpec] = []
    for unique_id, props in (manifest.get("nodes") or {}).items():
        if props.get("resource_type") != "model":
            continue
        if props.get("package_name") not in external_package_set:
            continue
        # Use the translator for asset-key resolution so meta.dagster.asset_key on the
        # upstream project's model still applies (essential for keys to match the upstream
        # Dagster code location's declarations).
        spec = translator.get_asset_spec(manifest, unique_id, project)
        if spec.key in seen:
            continue
        seen.add(spec.key)
        # Marker so the upstream Dagster location's non-stub declaration wins precedence.
        specs.append(
            spec.merge_attributes(
                metadata={
                    SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET: True,
                    DAGSTER_DBT_EXTERNAL_PACKAGE_METADATA_KEY: props.get("package_name"),
                }
            )
        )
    return specs
