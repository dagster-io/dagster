from typing import Optional, Sequence

import dagster._check as check
from dagster import AssetDep, AssetKey, AssetSpec
from dagster._annotations import experimental

from .asset_utils import build_dbt_multi_asset_args
from .dagster_dbt_translator import DagsterDbtTranslator, validate_translator
from .dbt_manifest import DbtManifestParam, validate_manifest
from .dbt_project import DbtProject


@experimental
def build_dbt_asset_specs(
    *,
    manifest: DbtManifestParam,
    dagster_dbt_translator: Optional[DagsterDbtTranslator] = None,
    select: str = "fqn:*",
    exclude: Optional[str] = None,
    project: Optional[DbtProject] = None,
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
        project (Optional[DbtProject]): A DbtProject instance which provides a pointer to the dbt
            project location and manifest. Not required, but needed to attach code references from
            model code to Dagster assets.

    Returns:
        Sequence[AssetSpec]: A list of asset specs.
    """
    manifest = validate_manifest(manifest)
    dagster_dbt_translator = validate_translator(dagster_dbt_translator or DagsterDbtTranslator())

    (
        _,
        outs,
        internal_asset_deps,
        _,
    ) = build_dbt_multi_asset_args(
        manifest=manifest,
        dagster_dbt_translator=dagster_dbt_translator,
        select=select,
        exclude=exclude or "",
        io_manager_key=None,
        project=project,
    )

    specs = [
        asset_out.to_spec(
            key=check.inst(asset_out.key, AssetKey),
            deps=[AssetDep(asset=dep) for dep in internal_asset_deps.get(output_name, set())],
        )
        # Allow specs to be represented as external assets by adhering to external asset invariants.
        ._replace(
            skippable=False,
            code_version=None,
        )
        for output_name, asset_out in outs.items()
    ]

    return specs
