from typing import Any, Callable, List, Optional
from pydantic import BaseModel
from dagster._record import record

# Type alias for raw Databricks job info
DatabricksJobInfo = dict[str, Any]

@record
class DatabricksFilter:
    include_job: Callable[[DatabricksJobInfo], bool]

class IncludeJobsConfig(BaseModel):
    job_ids: List[int]

class DatabricksFilterConfig(BaseModel):
    include_jobs: Optional[IncludeJobsConfig] = None

def resolve_databricks_filter(config: DatabricksFilterConfig) -> DatabricksFilter:
    """Convert a DatabricksFilterConfig into a DatabricksFilter."""
    if config and config.include_jobs and getattr(config.include_jobs, "job_ids", None):
        allowed_ids = set(config.include_jobs.job_ids)
        def include_job(job: DatabricksJobInfo) -> bool:
            return job.get("job_id") in allowed_ids
    else:
        def include_job(job: DatabricksJobInfo) -> bool:
            return True
    return DatabricksFilter(include_job=include_job)

class DatabricksWorkspaceConfig(BaseModel):
    host: str
    token: str

class AssetSpecConfig(BaseModel):
    key: str
    group: Optional[str] = None
    description: Optional[str] = None