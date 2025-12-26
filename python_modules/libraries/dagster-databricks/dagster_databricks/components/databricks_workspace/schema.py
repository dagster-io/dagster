from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any, Optional, Union

from dagster.components import Resolver
from pydantic import BaseModel

from dagster_databricks.components.databricks_asset_bundle.configs import DatabricksJob

DatabricksJobInfo = Union[dict[str, Any], DatabricksJob]


@dataclass
class DatabricksFilter:
    include_job: Callable[[DatabricksJobInfo], bool]


class IncludeJobsConfig(BaseModel):
    job_ids: list[int]


class DatabricksFilterConfig(BaseModel):
    include_jobs: Optional[IncludeJobsConfig] = None


def resolve_databricks_filter(context, config: DatabricksFilterConfig) -> DatabricksFilter:
    """Convert a DatabricksFilterConfig into a DatabricksFilter."""
    if config and config.include_jobs and getattr(config.include_jobs, "job_ids", None):
        allowed_ids = set(config.include_jobs.job_ids)

        def include_job(job: DatabricksJobInfo) -> bool:
            job_id = job.get("job_id") if isinstance(job, dict) else job.job_id
            return job_id in allowed_ids
    else:

        def include_job(job: DatabricksJobInfo) -> bool:
            return True

    return DatabricksFilter(include_job=include_job)


ResolvedDatabricksFilter = Annotated[
    DatabricksFilter,
    Resolver(
        resolve_databricks_filter,
        model_field_type=DatabricksFilterConfig,
        description="Filter which Databricks jobs to include",
    ),
]
