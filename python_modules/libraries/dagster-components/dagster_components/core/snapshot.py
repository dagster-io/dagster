import textwrap
from typing import Optional

from dagster_shared.serdes.objects import LibraryEntryKey, LibraryEntrySnap
from dagster_shared.serdes.objects.library_object import ComponentTypeData, ScaffoldTargetTypeData

from dagster_components.component.component import Component
from dagster_components.scaffold.scaffold import Scaffolder, get_scaffolder


def _clean_docstring(docstring: str) -> str:
    lines = docstring.strip().splitlines()
    first_line = lines[0]
    if len(lines) == 1:
        return first_line
    else:
        rest = textwrap.dedent("\n".join(lines[1:]))
        return f"{first_line}\n{rest}"


def _get_summary_and_description(obj: object) -> tuple[Optional[str], Optional[str]]:
    docstring = obj.__doc__
    clean_docstring = _clean_docstring(docstring) if docstring else None
    summary = clean_docstring.split("\n\n")[0] if clean_docstring else None
    description = clean_docstring if clean_docstring else None
    return summary, description


def _get_component_type_data(obj: type[Component]) -> ComponentTypeData:
    component_schema = obj.get_schema()
    component_json_schema = component_schema.model_json_schema() if component_schema else None
    return ComponentTypeData(schema=component_json_schema)


def _get_scaffold_target_type_data(scaffolder: Scaffolder) -> ScaffoldTargetTypeData:
    scaffolder_schema = scaffolder.get_scaffold_params()
    return ScaffoldTargetTypeData(
        schema=scaffolder_schema.model_json_schema() if scaffolder_schema else None
    )


def get_library_object_snap(key: LibraryEntryKey, obj: object) -> LibraryEntrySnap:
    type_data = []
    if isinstance(obj, type) and issubclass(obj, Component):
        type_data.append(_get_component_type_data(obj))

    scaffolder = get_scaffolder(obj) if isinstance(obj, type) else None
    if isinstance(scaffolder, Scaffolder):
        type_data.append(_get_scaffold_target_type_data(scaffolder))

    summary, description = _get_summary_and_description(obj)
    return LibraryEntrySnap(key=key, summary=summary, description=description, type_data=type_data)
