from typing import Any, Dict, Mapping, Optional, Sequence

from dagster import _check as check
from dagster.utils import merge_dicts

from ..definitions import ResourceDefinition
from ..definitions.resource_requirement import ResourceAddable


def with_resources(
    definitions: Sequence[ResourceAddable],
    resource_defs: Mapping[str, ResourceDefinition],
    config: Optional[Dict[str, Any]] = None,
) -> Sequence[ResourceAddable]:
    from dagster.core.storage.fs_io_manager import fs_io_manager

    check.mapping_param(resource_defs, "resource_defs")
    config = check.opt_dict_param(config, "config")

    resource_defs = merge_dicts({"io_manager": fs_io_manager}, resource_defs)
    for key in resource_defs.keys():
        if key in config:
            resource_defs[key] = resource_defs[key].configured(config[key])

    transformed_defs = []
    for definition in definitions:
        transformed_defs.append(definition.with_resources(resource_defs))

    return transformed_defs
