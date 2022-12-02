from typing import Any, Dict, Iterable, Mapping, Optional, Union

import dagster._check as check
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

        A python module is loadable by dagster tools if it there is a top level variable
        named `defs` that is an instance of Definitions.

        Definitions provides a few conveniences for dealing with resources that do not apply to
        vanilla dagster definitions:

        (1) It takes a dictionary of top-level resources which are automatically bound
        (via with_resources) to any asset passed to it. If you need to apply different
        resources to different assets, use legacy @repository and use with_resources as before.

        (2) The resources dictionary takes raw python objects, not just resource definitions.
        """

        if assets:
            check.iterable_param(
                assets, "assets", (AssetsDefinition, SourceAsset, CacheableAssetsDefinition)
            )

        if schedules:
            check.iterable_param(schedules, "schedules", ScheduleDefinition)

        if sensors:
            check.iterable_param(sensors, "sensors", SensorDefinition)

        if jobs:
            check.iterable_param(jobs, "jobs", JobDefinition)

        if resources:
            check.mapping_param(resources, "resources", key_type=str)

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

    def get_inner_repository(self) -> Union[RepositoryDefinition, PendingRepositoryDefinition]:
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
