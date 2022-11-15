from typing import Any, Dict, Generator, Iterable, Mapping, Optional, Union

from dagster._core.execution.with_resources import with_resources

from .assets import AssetsDefinition, SourceAsset
from .cacheable_assets import CacheableAssetsDefinition
from .decorators import repository
from .job_definition import JobDefinition
from .repository_definition import PendingRepositoryDefinition, RepositoryDefinition
from .resource_definition import ResourceDefinition
from .schedule_definition import ScheduleDefinition
from .sensor_definition import SensorDefinition


# will refactor to class
def Definitions(
    assets: Optional[
        Iterable[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]]
    ] = None,
    schedules: Optional[Iterable[ScheduleDefinition]] = None,
    sensors: Optional[Iterable[SensorDefinition]] = None,
    jobs: Optional[Iterable[JobDefinition]] = None,
    resources: Optional[Mapping[str, Any]] = None,
) -> Union[RepositoryDefinition, PendingRepositoryDefinition]:

    resource_defs = coerce_resources_to_defs(resources or {})

    @repository
    def designer_please_do_not_show_this_in_ui():
        return [
            *with_resources(assets or [], resource_defs),
            *(schedules or []),
            *(sensors or []),
            *(jobs or []),
        ]

    return designer_please_do_not_show_this_in_ui


def coerce_resources_to_defs(resources: Mapping[str, Any]) -> Dict[str, ResourceDefinition]:
    resource_defs = {}
    for key, resource_obj in resources.items():
        resource_defs[key] = (
            resource_obj
            if isinstance(resource_obj, ResourceDefinition)
            else ResourceDefinition.hardcoded_resource(resource_obj)
        )
    return resource_defs
