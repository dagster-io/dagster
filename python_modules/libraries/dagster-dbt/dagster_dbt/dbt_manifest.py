from pathlib import Path
from typing import Any, Mapping, Union, cast

import dagster._check as check
import orjson

from .asset_utils import is_asset_check_from_dbt_resource_props

DbtManifestParam = Union[Mapping[str, Any], str, Path]


def validate_manifest(manifest: DbtManifestParam) -> Mapping[str, Any]:
    check.inst_param(manifest, "manifest", (Path, str, dict))

    if isinstance(manifest, str):
        manifest = Path(manifest)

    if isinstance(manifest, Path):
        manifest = cast(Mapping[str, Any], orjson.loads(manifest.read_bytes()))

    is_asset_check_by_unique_id = {
        unique_id: is_asset_check_from_dbt_resource_props(dbt_resource_props)
        for unique_id, dbt_resource_props in manifest.get("nodes", {}).items()
        if unique_id.startswith("test")
    }
    is_asset_check_metadata_valid = len(set(is_asset_check_by_unique_id.values())) <= 1
    check.invariant(
        is_asset_check_metadata_valid,
        "When enabling asset checks for dbt tests, all tests must be enabled as asset checks",
    )

    return manifest
