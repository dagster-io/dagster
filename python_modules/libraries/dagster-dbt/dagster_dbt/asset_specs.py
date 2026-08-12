from collections.abc import Sequence

from dagster import AssetKey, AssetSpec
from dagster._core.definitions.assets.definition.asset_spec import (
    SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET,
)

from dagster_dbt.asset_utils import (
    DBT_DEFAULT_EXCLUDE,
    DBT_DEFAULT_SELECT,
    DBT_DEFAULT_SELECTOR,
    build_dbt_specs,
)
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, validate_translator
from dagster_dbt.dbt_manifest import DbtManifestParam, validate_manifest
from dagster_dbt.dbt_project import DbtProject


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
