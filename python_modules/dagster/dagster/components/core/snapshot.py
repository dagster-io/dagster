import textwrap
from typing import Optional

from dagster_shared.serdes.objects import (
    ComponentTypeSnap,
    LibraryObjectKey,
    LibraryObjectSnap,
    ScaffolderSnap,
)

from dagster.components.component.component import Component
from dagster.components.scaffold.scaffold import Scaffolder, get_scaffolder


def _clean_docstring(docstring: str) -> str:
    lines = docstring.strip().splitlines()
    first_line = lines[0]
    if len(lines) == 1:
        return first_line
    else:
        rest = textwrap.dedent("\n".join(lines[1:]))
        return f"{first_line}\n{rest}"


def _get_scaffolder_snap(obj: object) -> Optional[ScaffolderSnap]:
    scaffolder = get_scaffolder(obj) if isinstance(obj, type) else None
    if not isinstance(scaffolder, Scaffolder):
        return None
    scaffolder_schema = scaffolder.get_scaffold_params()
    return ScaffolderSnap(
        schema=scaffolder_schema.model_json_schema() if scaffolder_schema else None
    )


def _get_summary_and_description(obj: object) -> tuple[Optional[str], Optional[str]]:
    docstring = obj.__doc__
    clean_docstring = _clean_docstring(docstring) if docstring else None
    summary = clean_docstring.split("\n\n")[0] if clean_docstring else None
    description = clean_docstring if clean_docstring else None
    return summary, description


def _get_component_type_snap(key: LibraryObjectKey, obj: type[Component]) -> ComponentTypeSnap:
    summary, description = _get_summary_and_description(obj)
    component_schema = obj.get_schema()
    return ComponentTypeSnap(
        key=key,
        summary=summary,
        description=description,
        schema=component_schema.model_json_schema() if component_schema else None,
        scaffolder=_get_scaffolder_snap(obj),
    )


def _get_library_object_snap(key: LibraryObjectKey, obj: object) -> LibraryObjectSnap:
    summary, description = _get_summary_and_description(obj)
    return LibraryObjectSnap(
        key=key, summary=summary, description=description, scaffolder=_get_scaffolder_snap(obj)
    )


def get_library_object_snap(key: LibraryObjectKey, obj: object) -> LibraryObjectSnap:
    if isinstance(obj, type) and issubclass(obj, Component):
        return _get_component_type_snap(key, obj)
    else:
        return _get_library_object_snap(key, obj)
