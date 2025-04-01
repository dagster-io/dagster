import inspect
from collections.abc import Iterable, Mapping
from importlib import import_module
from types import ModuleType
from typing import Any, Optional, Union

import dagster._check as check
from dagster._annotations import preview
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.executor_definition import ExecutorDefinition
from dagster._core.definitions.logger_definition import LoggerDefinition
from dagster._core.definitions.module_loaders.object_list import ModuleScopedDagsterDefs
from dagster._core.definitions.module_loaders.utils import find_modules_in_package
from dagster._core.executor.base import Executor


@preview
def load_definitions_from_modules(
    modules: Iterable[ModuleType],
    resources: Optional[Mapping[str, Any]] = None,
    loggers: Optional[Mapping[str, LoggerDefinition]] = None,
    executor: Optional[Union[Executor, ExecutorDefinition]] = None,
) -> Definitions:
    """Constructs the :py:class:`dagster.Definitions` from the given modules.

    Args:
        modules (Iterable[ModuleType]): The Python modules to look for :py:class:`dagster.Definitions` inside.
        resources (Optional[Mapping[str, Any]]):
            Dictionary of resources to bind to assets in the loaded :py:class:`dagster.Definitions`.
        loggers (Optional[Mapping[str, LoggerDefinition]]):
            Default loggers for jobs in the loaded :py:class:`dagster.Definitions`. Individual jobs
            can define their own loggers by setting them explicitly.
        executor (Optional[Union[Executor, ExecutorDefinition]]):
            Default executor for jobs in the loaded :py:class:`dagster.Definitions`. Individual jobs
            can define their own executors by setting them explicitly.

    Returns:
        Definitions:
            The :py:class:`dagster.Definitions` defined in the given modules.
    """
    return Definitions(
        **ModuleScopedDagsterDefs.from_modules(modules).get_object_list().to_definitions_args(),
        resources=resources,
        loggers=loggers,
        executor=executor,
    )


@preview
def load_definitions_from_module(
    module: ModuleType,
    resources: Optional[Mapping[str, Any]] = None,
    loggers: Optional[Mapping[str, LoggerDefinition]] = None,
    executor: Optional[Union[Executor, ExecutorDefinition]] = None,
) -> Definitions:
    """Constructs the :py:class:`dagster.Definitions` from the given module.

    Args:
        module (ModuleType): The Python module to look for :py:class:`dagster.Definitions` inside.
        resources (Optional[Mapping[str, Any]]):
            Dictionary of resources to bind to assets in the loaded :py:class:`dagster.Definitions`.
        loggers (Optional[Mapping[str, LoggerDefinition]]):
            Default loggers for jobs in the loaded :py:class:`dagster.Definitions`. Individual jobs
            can define their own loggers by setting them explicitly.
        executor (Optional[Union[Executor, ExecutorDefinition]]):
            Default executor for jobs in the loaded :py:class:`dagster.Definitions`. Individual jobs
            can define their own executors by setting them explicitly.

    Returns:
        Definitions:
            The :py:class:`dagster.Definitions` defined in the given module.
    """
    return load_definitions_from_modules(
        modules=[module], resources=resources, loggers=loggers, executor=executor
    )


@preview
def load_definitions_from_current_module(
    resources: Optional[Mapping[str, Any]] = None,
    loggers: Optional[Mapping[str, LoggerDefinition]] = None,
    executor: Optional[Union[Executor, ExecutorDefinition]] = None,
) -> Definitions:
    """Constructs the :py:class:`dagster.Definitions` from the module where this function is called.

    Args:
        resources (Optional[Mapping[str, Any]]):
            Dictionary of resources to bind to assets in the loaded :py:class:`dagster.Definitions`.
        loggers (Optional[Mapping[str, LoggerDefinition]]):
            Default loggers for jobs in the loaded :py:class:`dagster.Definitions`. Individual jobs
            can define their own loggers by setting them explicitly.
        executor (Optional[Union[Executor, ExecutorDefinition]]):
            Default executor for jobs in the loaded :py:class:`dagster.Definitions`. Individual jobs
            can define their own executors by setting them explicitly.

    Returns:
        Definitions:
            The :py:class:`dagster.Definitions` defined in the current module.
    """
    caller = inspect.stack()[1]
    module = inspect.getmodule(caller[0])
    if module is None:
        check.failed("Could not find a module for the caller")

    return load_definitions_from_modules(
        modules=[module], resources=resources, loggers=loggers, executor=executor
    )


@preview
def load_definitions_from_package_module(
    package_module: ModuleType,
    resources: Optional[Mapping[str, Any]] = None,
    loggers: Optional[Mapping[str, LoggerDefinition]] = None,
    executor: Optional[Union[Executor, ExecutorDefinition]] = None,
) -> Definitions:
    """Constructs the :py:class:`dagster.Definitions` from the given package module.

    Args:
        package_module (ModuleType):
            The package module to look for :py:class:`dagster.Definitions` inside.
        resources (Optional[Mapping[str, Any]]):
            Dictionary of resources to bind to assets in the loaded :py:class:`dagster.Definitions`.
        loggers (Optional[Mapping[str, LoggerDefinition]]):
            Default loggers for jobs in the loaded :py:class:`dagster.Definitions`. Individual jobs
            can define their own loggers by setting them explicitly.
        executor (Optional[Union[Executor, ExecutorDefinition]]):
            Default executor for jobs in the loaded :py:class:`dagster.Definitions`. Individual jobs
            can define their own executors by setting them explicitly.

    Returns:
        Definitions:
            The :py:class:`dagster.Definitions` defined in the given package module.
    """
    return load_definitions_from_modules(
        modules=[*find_modules_in_package(package_module)],
        resources=resources,
        loggers=loggers,
        executor=executor,
    )


@preview
def load_definitions_from_package_name(
    package_name: str,
    resources: Optional[Mapping[str, Any]] = None,
    loggers: Optional[Mapping[str, LoggerDefinition]] = None,
    executor: Optional[Union[Executor, ExecutorDefinition]] = None,
) -> Definitions:
    """Constructs the :py:class:`dagster.Definitions` from the package module for the given package name.

    Args:
        package_name (str):
            The name of the package module to look for :py:class:`dagster.Definitions` inside.
        resources (Optional[Mapping[str, Any]]):
            Dictionary of resources to bind to assets in the loaded :py:class:`dagster.Definitions`.
        loggers (Optional[Mapping[str, LoggerDefinition]]):
            Default loggers for jobs in the loaded :py:class:`dagster.Definitions`. Individual jobs
            can define their own loggers by setting them explicitly.
        executor (Optional[Union[Executor, ExecutorDefinition]]):
            Default executor for jobs in the loaded :py:class:`dagster.Definitions`. Individual jobs
            can define their own executors by setting them explicitly.

    Returns:
        Definitions:
            The :py:class:`dagster.Definitions` defined in the package module for the given package name.
    """
    package_module = import_module(package_name)
    return load_definitions_from_package_module(
        package_module=package_module,
        resources=resources,
        loggers=loggers,
        executor=executor,
    )
