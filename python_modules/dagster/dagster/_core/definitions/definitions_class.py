import inspect
from typing import Any, Dict, Iterable, Mapping, Optional, Union

from dagster import _check as check
from dagster._annotations import experimental
from dagster._core.execution.with_resources import with_resources

from .assets import AssetsDefinition, SourceAsset
from .cacheable_assets import CacheableAssetsDefinition
from .decorators import repository
from .job_definition import JobDefinition
from .repository_definition import (
    SINGLETON_REPOSITORY_NAME,
    PendingRepositoryDefinition,
    RepositoryDefinition,
)
from .resource_definition import ResourceDefinition
from .schedule_definition import ScheduleDefinition
from .sensor_definition import SensorDefinition

NO_STACK_FRAME_ERROR_MSG = "Python interpreter must support Python stack frames. Python interpreters that are not CPython do not necessarily implement the necessary APIs."

# invoke this function to get the module name the function
# that called regsiter_definitions
def get_module_name_of_definitions_caller() -> str:
    # based on https://stackoverflow.com/questions/2000861/retrieve-module-object-from-stack-frame
    # three f_backs to get past registered_definitions and @experimental frame
    # Need to do None checking because of:
    # https://docs.python.org/3/library/inspect.html#inspect.currentframe
    # Relevant comment is:
    # CPython implementation detail: This function relies on Python stack frame
    # support in the interpreter, which isn’t guaranteed to exist in all
    # implementations of Python. If running in an implementation without
    # Python stack frame support this function returns None.
    frame = check.not_none(inspect.currentframe(), NO_STACK_FRAME_ERROR_MSG)
    register_definitions_frame = check.not_none(frame.f_back, NO_STACK_FRAME_ERROR_MSG)
    experimental_frame = check.not_none(register_definitions_frame.f_back, NO_STACK_FRAME_ERROR_MSG)
    caller_frame = check.not_none(experimental_frame.f_back, NO_STACK_FRAME_ERROR_MSG)
    return caller_frame.f_globals["__name__"]


# will refactor to class
#  -> Union[RepositoryDefinition, PendingRepositoryDefinition]:
@experimental
class Definitions:
    def __init__(
        self,
        assets: Optional[
            Iterable[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]]
        ] = None,
        schedules: Optional[Iterable[ScheduleDefinition]] = None,
        sensors: Optional[Iterable[SensorDefinition]] = None,
        jobs: Optional[Iterable[JobDefinition]] = None,
        resources: Optional[Mapping[str, Any]] = None,
    ):
        """
        Example usage:

        defs = Definitions(
            assets=[asset_one, asset_two],
            schedules=[a_schedule],
            sensors=[a_sensor],
            jobs=[a_job],
            resources={
                "a_resource": some_resource,
            }
        )

        Create a set of definitions explicitly available and loadable by dagster tools.

        Dagster separates user-defined code from system tools such the web server and
        the daemon. Rather than loading code directly into process, a tool such as the
        webserver interacts with user-defined code over a serialization boundary.

        These tools must be able to locate and load this code when they start. Via CLI
        arguments or config, they specify a python module to inspect.

        A python module is loadable by dagster tools if:

        (1) Has one or more dagster definitions as module-level attributes (e.g. a function
        declared at the top-level of a module decorated with @asset).

        or

        (2) Has a `Definitions` object defined at module-scope

        For anything beyond lightweight testing and exploration, the use of `Definitions`
        is strongly recommended.

        This function provides a few conveniences for the user that do not apply to
        vanilla dagster definitions:

        (1) It takes a dictionary of top-level resources which are automatically bound
        (via with_resources) to any asset passed to it. If you need to apply different
        resources to different assets, use legacy @repository and use with_resources as before.

        (2) The resources dictionary takes raw python objects, not just resource definitions.
        """

        resource_defs = coerce_resources_to_defs(resources or {})

        @repository(name=SINGLETON_REPOSITORY_NAME)
        def created_repo():
            return [
                *with_resources(assets or [], resource_defs),
                *(schedules or []),
                *(sensors or []),
                *(jobs or []),
            ]

        self._created_repo = created_repo

    def get_inner_repository(self):
        return self._created_repo


def coerce_resources_to_defs(resources: Mapping[str, Any]) -> Dict[str, ResourceDefinition]:
    resource_defs = {}
    for key, resource_obj in resources.items():
        resource_defs[key] = (
            resource_obj
            if isinstance(resource_obj, ResourceDefinition)
            else ResourceDefinition.hardcoded_resource(resource_obj)
        )
    return resource_defs
