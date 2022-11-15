import inspect
from types import ModuleType
from typing import Any, Iterable, Mapping, Optional, Union

import dagster._check as check

from .assets import AssetsDefinition, SourceAsset
from .cacheable_assets import CacheableAssetsDefinition

# from .decorators import repository
from .job_definition import JobDefinition

# from .resource_definition import ResourceDefinition
from .schedule_definition import ScheduleDefinition
from .sensor_definition import SensorDefinition

# from .repository_definition import PendingRepositoryDefinition, RepositoryDefinition


MAGIC_REGISTERED_DEFINITIONS_KEY = "__registered_definitions"


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

    alts:
    dagsterify_module
    make_module_loadable
    defined_loadable_module
    definitions_in_module
    register_definitions

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
    raise NotImplementedError("Not implemented yet")


NO_STACK_FRAME_ERROR_MSG = "Python interpreter must support Python stack frames. Python interpreters that are not CPython do not necessarily implement the necessary APIs."

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
