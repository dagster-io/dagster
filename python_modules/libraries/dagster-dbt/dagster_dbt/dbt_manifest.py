from pathlib import Path
from typing import Any, Mapping, Union, cast

import dagster._check as check
import orjson

DbtManifestParam = Union[Mapping[str, Any], str, Path]


def validate_manifest(manifest: DbtManifestParam) -> Mapping[str, Any]:
    check.inst_param(manifest, "manifest", (Path, str, dict))

    if isinstance(manifest, str):
        manifest = Path(manifest)

    if isinstance(manifest, Path):
        manifest = cast(Mapping[str, Any], orjson.loads(manifest.read_bytes()))

    return manifest
