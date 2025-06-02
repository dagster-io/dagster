from pathlib import Path
from typing import Optional

from dagster_shared.serdes.objects import PluginObjectKey

from dagster.components.component_scaffolding import scaffold_object
from dagster.components.core.package_entry import load_package_object


def scaffold_object_command_impl(
    typename: str,
    path: Path,
    json_params: Optional[str],
    scaffold_format: str,
    project_root: Optional[Path],
) -> None:
    key = PluginObjectKey.from_typename(typename)
    obj = load_package_object(key)

    scaffold_object(
        path,
        obj,
        typename,
        json_params,
        scaffold_format,
        project_root,
    )
