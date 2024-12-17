from types import ModuleType
from typing import Optional

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.module_loaders.object_list import ModuleScopedDagsterObjects
from dagster._core.definitions.module_loaders.utils import (
    ExecutorObject,
    LoggerDefinitionKeyMapping,
    ResourceDefinitionMapping,
)


def load_definitions_from_module(
    module: ModuleType,
    resources: Optional[ResourceDefinitionMapping] = None,
    loggers: Optional[LoggerDefinitionKeyMapping] = None,
    executor: Optional[ExecutorObject] = None,
) -> Definitions:
    return Definitions(
        **ModuleScopedDagsterObjects.from_modules([module]).get_object_list().to_definitions_args(),
        resources=resources,
        loggers=loggers,
        executor=executor,
    )
