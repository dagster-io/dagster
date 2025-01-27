import dagster as dg
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_job import IMPLICIT_ASSET_JOB_NAME, build_asset_job
from dagster._core.definitions.repository_definition.repository_data import CachingRepositoryData
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)


@dg.asset(automation_condition=dg.AutomationCondition.initial_evaluation())
def old_asset() -> None: ...


# directly construct so we can simulate an older repo without auto-constructed sensors
repo_data = CachingRepositoryData(
    jobs={
        # implicit asset job to make this valid repo data
        IMPLICIT_ASSET_JOB_NAME: build_asset_job(
            IMPLICIT_ASSET_JOB_NAME,
            AssetGraph.from_assets([old_asset]),
            allow_different_partitions_defs=True,
        )
    },
    schedules={},
    sensors={},
    source_assets_by_key={},
    assets_defs_by_key={old_asset.key: old_asset},
    asset_checks_defs_by_key={},
    top_level_resources={},
    utilized_env_vars={},
    unresolved_partitioned_asset_schedules={},
)
repo = RepositoryDefinition("repo", repository_data=repo_data)
assert repo.schedule_defs == []
