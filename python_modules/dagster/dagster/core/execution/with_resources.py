from typing import Any, Dict, Mapping, Optional, Sequence, Union

from dagster import _check as check

from ..asset_defs import AssetsDefinition
from ..definitions import ResourceDefinition
from ..definitions.resource_requirement import ResourceAddable


def with_resources(
    definitions: Sequence[ResourceAddable],
    resource_defs: Mapping[str, ResourceDefinition],
    config: Optional[Dict[str, Any]] = None,
) -> Sequence[ResourceAddable]:
    check.mapping_param(resource_defs, "resource_defs")
    config = check.opt_dict_param(config, "config")

    resource_defs = dict(resource_defs)
    for key in resource_defs.keys():
        if key in config:
            resource_defs[key] = resource_defs[key].configured(config[key])

    transformed_defs = []
    for definition in definitions:
        transformed_defs.append(definition.with_resources(resource_defs))

    return transformed_defs
