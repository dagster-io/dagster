from collections.abc import Sequence
from typing import Optional

from dagster import AssetSpec

from dagster_dbt.asset_utils import build_dbt_specs
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, validate_translator
from dagster_dbt.dbt_manifest import DbtManifestParam, validate_manifest
from dagster_dbt.dbt_project import DbtProject


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

    specs, _ = build_dbt_specs(
        manifest=manifest,
        translator=dagster_dbt_translator,
        select=select,
        exclude=exclude or "",
        io_manager_key=None,
        project=project,
    )

    return [
        # Allow specs to be represented as external assets by adhering to external asset invariants.
        spec.replace_attributes(skippable=False, code_version=None)
        for spec in specs
    ]
