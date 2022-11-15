import inspect
import sys
from collections.abc import Generator
from contextlib import contextmanager
from types import ModuleType
from typing import Any, Dict, Iterable, Mapping, Optional, Union

import dagster._check as check
from dagster._annotations import experimental
from dagster._core.execution.with_resources import with_resources

from .assets import AssetsDefinition, SourceAsset
from .cacheable_assets import CacheableAssetsDefinition
from .decorators import repository
from .job_definition import JobDefinition
from .repository_definition import PendingRepositoryDefinition, RepositoryDefinition
from .resource_definition import ResourceDefinition
from .schedule_definition import ScheduleDefinition
from .sensor_definition import SensorDefinition

MAGIC_REGISTERED_DEFINITIONS_KEY = "__registered_definitions"


class ModuleHasRegisteredDefinitionsError(Exception):
    pass


# invoke this function to get the module name the function that called the current
# scope
def get_module_name_of_caller() -> str:
    # based on https://stackoverflow.com/questions/2000861/retrieve-module-object-from-stack-frame
    # two f_backs to get past get_module_name_of_caller frame

    # Need to do none checking because of:
    # https://docs.python.org/3/library/inspect.html#inspect.currentframe
    # CPython implementation detail: This function relies on Python stack frame
    # support in the interpreter, which isn’t guaranteed to exist in all
    # implementations of Python. If running in an implementation without
    # Python stack frame support this function returns None.

    frame = check.not_none(inspect.currentframe(), NO_STACK_FRAME_ERROR_MSG)
    back_frame = check.not_none(frame.f_back, NO_STACK_FRAME_ERROR_MSG)
    back_back_frame = check.not_none(back_frame.f_back, NO_STACK_FRAME_ERROR_MSG)
    return back_back_frame.f_globals["__name__"]


# @experimental
def register_definitions(
    *,
    assets: Optional[
        Iterable[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]]
    ] = None,
    schedules: Optional[Iterable[ScheduleDefinition]] = None,
    sensors: Optional[Iterable[SensorDefinition]] = None,
    jobs: Optional[Iterable[JobDefinition]] = None,
    resources: Optional[Mapping[str, Any]] = None,
) -> None:
    """
    Make a set of definitions explicitly available and loadable by dagster tools.

    Dagster separates user-defined code from system tools such the web server and
    the daemon. These tools must be able to locate and load this code when they start.
    Python modules that dagster tools can load are known as "code locations".

    A code location is defined as a python module that has either:

    (1) Has one or more dagster definitions as module-level attributes (e.g. a function
    declared at the top-level of a module decorated with @asset).

    or

    (2) A module that contains an explicit call to register_definitions.

    For anything beyond lightweight testing and exploration, the use of register_definitions
    is strongly recommended.

    This function provides a few conveniences for the user that do not apply to vanilla dagster
    definitions:

    (1) It takes a dictionary of top-level resources which are automatically bound
    (via with_resources) to any asset passed to it. If you need to apply different
    resources to different assets, use legacy @repository and use with_resources as before.

    (2) The resources dictionary takes raw python objects, not just resource definitions.

    Invoking this function dynamically injects an attribute named "__registered_definitions" into
    the calling module that contains a handle to the definitions.
    """
    module_name = get_module_name_of_caller()
    python_module = sys.modules[module_name]

    if MAGIC_REGISTERED_DEFINITIONS_KEY in python_module.__dict__:
        raise ModuleHasRegisteredDefinitionsError(
            f"Python module {module_name} already has registered definitions, likely because of a previous call to register_definitions"
        )

    # This grabs last component of a module name (typically the name
    # of the file) and uses it for the repository name. Code locations
    # defined with register_definitions will only have 1 repository defined. And
    # the web UI will not expose the concept of repository anywhere. In those
    # cases the name of the repository is immaterial. If the legacy UI is loaded
    # the repository will have a sensible enough name, but explicitly overriding
    # that name is not worth polluting this new, cleaner API.
    repo_name = module_name.split(".")[-1] if "." in module_name else module_name

    resource_defs = coerce_resources_to_defs(resources or {})

    @repository(name=repo_name)
    def registered_repository():
        return [
            *with_resources(assets or [], resource_defs),
            *(schedules or []),
            *(sensors or []),
            *(jobs or []),
        ]

    python_module.__dict__[MAGIC_REGISTERED_DEFINITIONS_KEY] = registered_repository


NO_STACK_FRAME_ERROR_MSG = "Python interpreter must support Python stack frames. Python interpreters that are not CPython do not necessarily implement the necessary APIs."


@contextmanager
def register_definitions_test_scope(dundername: str) -> Generator[None, None, None]:
    """
    A testing utility. Intended usage:

    with register_definitions_test_scope(__name__):
        register_definitions(...)

    This function ensures that no definitions have been registered
    in the current module. Then in the with block the test can invoke
    register_definitions. Upon exiting the with both the registered definitions
    in that module are "unregistered" by deleting the magic attribute.
    """
    parent_mod = sys.modules[dundername]
    assert MAGIC_REGISTERED_DEFINITIONS_KEY not in parent_mod.__dict__
    try:
        yield
    finally:
        if MAGIC_REGISTERED_DEFINITIONS_KEY in parent_mod.__dict__:
            del parent_mod.__dict__[MAGIC_REGISTERED_DEFINITIONS_KEY]


def get_registered_repository_in_module(
    module_name: str,
) -> Union[RepositoryDefinition, PendingRepositoryDefinition]:
    return sys.modules[module_name].__dict__[MAGIC_REGISTERED_DEFINITIONS_KEY]


def coerce_resources_to_defs(resources: Mapping[str, Any]) -> Dict[str, ResourceDefinition]:
    resource_defs = {}
    for key, resource_obj in resources.items():
        resource_defs[key] = (
            resource_obj
            if isinstance(resource_obj, ResourceDefinition)
            else ResourceDefinition.hardcoded_resource(resource_obj)
        )
    return resource_defs
