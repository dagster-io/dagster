import textwrap
from typing import Optional

from dagster_shared.serdes.objects.package_entry import (
    ComponentFeatureData,
    EnvRegistryKey,
    EnvRegistryObjectSnap,
    ScaffoldTargetTypeData,
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


def _get_summary_and_description(obj: object) -> tuple[Optional[str], Optional[str]]:
    docstring = obj.__doc__
    clean_docstring = _clean_docstring(docstring) if docstring else None
    summary = clean_docstring.split("\n\n")[0] if clean_docstring else None
    description = clean_docstring if clean_docstring else None
    return summary, description


def _get_component_type_data(obj: type[Component]) -> ComponentFeatureData:
    component_schema = obj.get_model_cls()
    component_json_schema = component_schema.model_json_schema() if component_schema else None
    return ComponentFeatureData(schema=component_json_schema)


def _get_scaffold_target_type_data(scaffolder: Scaffolder) -> ScaffoldTargetTypeData:
    scaffolder_schema = scaffolder.get_scaffold_params()
    return ScaffoldTargetTypeData(
        schema=scaffolder_schema.model_json_schema() if scaffolder_schema else None
    )


def get_package_entry_snap(key: EnvRegistryKey, obj: object) -> EnvRegistryObjectSnap:
    type_data = []
    owners = []
    tags = []
    aliases = []
    if isinstance(obj, type) and issubclass(obj, Component):
        type_data.append(_get_component_type_data(obj))
        spec = obj.get_spec()
        owners = spec.owners
        tags = spec.tags
        if obj.__module__ != key.namespace:
            # add the module that defines the class as an alias
            aliases.append(EnvRegistryKey(namespace=obj.__module__, name=obj.__name__))
    scaffolder = get_scaffolder(obj)
    if isinstance(scaffolder, Scaffolder):
        type_data.append(_get_scaffold_target_type_data(scaffolder))
    summary, description = _get_summary_and_description(obj)
    return EnvRegistryObjectSnap(
        key=key,
        aliases=aliases,
        summary=summary,
        owners=owners,
        tags=tags,
        description=description,
        feature_data=type_data,
    )
