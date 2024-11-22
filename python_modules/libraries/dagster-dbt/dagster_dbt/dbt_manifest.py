from collections.abc import Mapping
from functools import cache
from pathlib import Path
from typing import Any, Union, cast

import dagster._check as check
import orjson

from dagster_dbt.errors import DagsterDbtManifestNotFoundError

DbtManifestParam = Union[Mapping[str, Any], str, Path]


@cache
def read_manifest_path(manifest_path: Path) -> Mapping[str, Any]:
    """Reads a dbt manifest path and returns the parsed JSON as a dict.

    This function is cached to ensure that we don't read the same path multiple times, which
    creates multiple copies of the parsed manifest in memory.

    If we fix the fact that the manifest is held in memory instead of garbage collected, we
    can delete this cache.
    """
    if not manifest_path.exists():
        raise DagsterDbtManifestNotFoundError(f"{manifest_path} does not exist.")

    return cast(Mapping[str, Any], orjson.loads(manifest_path.read_bytes()))


def validate_manifest(manifest: DbtManifestParam) -> Mapping[str, Any]:
    check.inst_param(manifest, "manifest", (Path, str, dict))

    if isinstance(manifest, str):
        manifest = Path(manifest)

    if isinstance(manifest, Path):
        # Resolve the path to ensure a consistent key for the cache
        manifest = read_manifest_path(manifest.resolve())

    return manifest
