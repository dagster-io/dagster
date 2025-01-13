from collections.abc import Mapping
from types import ModuleType
from typing import Any, Optional, Union

from dagster._annotations import experimental
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.executor_definition import ExecutorDefinition
from dagster._core.definitions.logger_definition import LoggerDefinition
from dagster._core.definitions.module_loaders.object_list import ModuleScopedDagsterDefs
from dagster._core.executor.base import Executor


@experimental
def load_definitions_from_module(
    module: ModuleType,
    resources: Optional[Mapping[str, Any]] = None,
    loggers: Optional[Mapping[str, LoggerDefinition]] = None,
    executor: Optional[Union[Executor, ExecutorDefinition]] = None,
) -> Definitions:
    return Definitions(
        **ModuleScopedDagsterDefs.from_modules([module]).get_object_list().to_definitions_args(),
        resources=resources,
        loggers=loggers,
        executor=executor,
    )
