from typing import Sequence
from .fetch_assets import repository_iter
from fuzzywuzzy import process
from dagster._core.workspace.context import WorkspaceRequestContext

def scrape_workspace_objects(context: WorkspaceRequestContext):
    scraped_objects = {
        "resource_names": set(),
        "job_names": set(),
        "schedule_names": set(),
        "sensor_names": set(),
        "asset_keys": set(),
        "asset_groups": set(),
    }
    for _, external_repo in repository_iter(context):
        scraped_objects["resource_names"].update(
            [resource.name for resource in external_repo.get_external_resources()]
        )
        scraped_objects["schedule_names"].update(
            [schedule.name for schedule in external_repo.get_external_schedules()]
        )
        scraped_objects["sensor_names"].update(
            [sensor.name for sensor in external_repo.get_external_sensors()]
        )
        scraped_objects["job_names"].update(
            [job.name for job in external_repo.get_all_external_jobs()]
        )
        for external_asset_node in external_repo.get_external_asset_nodes():
            scraped_objects["asset_keys"].add(external_asset_node.asset_key.to_user_string())
            scraped_objects["asset_groups"].add(external_asset_node.group_name)

    return scraped_objects

def search_workspace(context: WorkspaceRequestContext, query: str) -> Sequence[str]:
    workspace_objects_by_type = scrape_workspace_objects(context)
    workspace_objects = [
        *workspace_objects_by_type["resource_names"],
        *workspace_objects_by_type["job_names"],
        *workspace_objects_by_type["schedule_names"],
        *workspace_objects_by_type["sensor_names"],
        *workspace_objects_by_type["asset_keys"],
        *workspace_objects_by_type["asset_groups"]
    ]
    matches_and_scores = process.extract(query, workspace_objects, limit=10)
    return [match for match, _ in matches_and_scores]