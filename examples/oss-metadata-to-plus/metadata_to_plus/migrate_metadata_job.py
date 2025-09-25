# Docs: https://docs.dagster.io/api/python-api/external-assets-rest-api

import os
from typing import Optional

import requests
from dagster import (
    AssetExecutionContext,
    AssetKey,
    Config,
    EventLogRecord,
    EventRecordsResult,
    RunConfig,
    asset,
    define_asset_job,
)


def _report_asset_materialization_to_dagster_plus(
    new_organization: str,
    new_deployment: str,
    new_dagster_cloud_api_token: str,
    asset_key: str,
    partition: Optional[str],
    metadata: Optional[dict],
):
    url = "https://{organization}.dagster.cloud/{deployment_name}/report_asset_materialization/".format(  # noqa: UP032
        organization=new_organization, deployment_name=new_deployment
    )

    payload = {
        "asset_key": asset_key,
        "metadata": metadata,
        "partition": partition,
    }
    headers = {
        "Content-Type": "application/json",
        "Dagster-Cloud-Api-Token": new_dagster_cloud_api_token,
    }

    response = requests.request("POST", url, json=payload, headers=headers)
    response.raise_for_status()


class MetadataMigrationConfig(Config):
    new_organization: str
    new_deployment: str
    new_dagster_cloud_api_token: str
    # Optional parameters for different selection modes
    asset_key: Optional[str] = None  # For single asset migration
    asset_group: Optional[str] = None  # For asset group migration
    migrate_all: bool = False  # For migrating all assets in code location
    ignore_metadata_migration_asset: bool = (
        True  # Exclude the migration asset itself from selections
    )


def _get_asset_keys_to_migrate(
    context: AssetExecutionContext, config: MetadataMigrationConfig
) -> list[AssetKey]:
    """Get list of asset keys to migrate based on configuration."""
    migration_asset_key = AssetKey(["migrate_metadata_asset"])

    if config.asset_key:
        # Single asset mode
        asset_keys = [AssetKey.from_user_string(config.asset_key)]
    elif config.asset_group:
        # Asset group mode - get all assets in the specified group
        from dagster._core.definitions.repository_definition import RepositoryDefinition

        # Get all assets from the repository definitions
        repo_def = context.repository_def
        if isinstance(repo_def, RepositoryDefinition):
            asset_graph = repo_def.asset_graph
            asset_keys = []
            for asset_key in asset_graph.materializable_asset_keys:
                node = asset_graph.get(asset_key)
                if hasattr(node, "group_name") and node.group_name == config.asset_group:
                    asset_keys.append(asset_key)
            context.log.info(f"Found {len(asset_keys)} assets in group {config.asset_group}")
        else:
            asset_keys = []
    elif config.migrate_all:
        # All assets mode - get all assets in the code location
        from dagster._core.definitions.repository_definition import RepositoryDefinition

        repo_def = context.repository_def
        if isinstance(repo_def, RepositoryDefinition):
            asset_graph = repo_def.asset_graph
            asset_keys = list(asset_graph.materializable_asset_keys)
            context.log.info(f"Found {len(asset_keys)} materializable assets in the repository")
        else:
            asset_keys = []
    else:
        raise ValueError("Must specify either asset_key, asset_group, or migrate_all=True")

    # Filter out the migration asset itself if configured to do so
    if config.ignore_metadata_migration_asset and migration_asset_key in asset_keys:
        asset_keys.remove(migration_asset_key)
        context.log.info("Excluded migrate_metadata_asset from migration selection")

    return asset_keys


def _migrate_single_asset(
    context: AssetExecutionContext, config: MetadataMigrationConfig, asset_key: AssetKey
):
    """Migrate metadata for a single asset."""
    cursor = None
    asset_key_str = asset_key.to_user_string()

    context.log.info(f"Starting migration for asset: {asset_key_str}")

    # can partition this to run in parallel
    for i in range(100):
        try:
            result: EventRecordsResult = context.instance.fetch_materializations(
                records_filter=asset_key,
                limit=1,
                cursor=cursor,
            )

            if not result.records:
                context.log.info(f"No more materialization records found for {asset_key_str}")
                break

            record: EventLogRecord = result.records[0]
            dagster_event = record.event_log_entry.dagster_event
            if dagster_event is not None:
                data = dagster_event.event_specific_data.materialization
                partition_to_report = data.partition
                metadata_to_report = {key: value.value for key, value in data.metadata.items()}

                _report_asset_materialization_to_dagster_plus(
                    new_organization=config.new_organization,
                    new_deployment=config.new_deployment,
                    new_dagster_cloud_api_token=config.new_dagster_cloud_api_token,
                    asset_key=asset_key_str,
                    partition=partition_to_report,
                    metadata=metadata_to_report,
                )
                context.log.info(
                    f"Migrated asset {asset_key_str} for partition {partition_to_report}"
                )

            cursor = result.cursor

        except Exception as e:
            context.log.error(f"Error migrating asset {asset_key_str} at iteration {i}: {e}")
            break


@asset
def migrate_metadata_asset(context: AssetExecutionContext, config: MetadataMigrationConfig):
    """Migrate metadata for assets based on configuration - supports single asset, asset group, or all assets."""
    asset_keys_to_migrate = _get_asset_keys_to_migrate(context, config)

    context.log.info(f"Found {len(asset_keys_to_migrate)} assets to migrate")

    for asset_key in asset_keys_to_migrate:
        _migrate_single_asset(context, config, asset_key)


# Job configuration examples for different migration modes
# Note: Set environment variables ORGANIZATION, DEPLOYMENT_NAME, and DAGSTER_CLOUD_API_TOKEN

# Single asset migration job
migrate_single_asset_job = define_asset_job(
    "migrate_single_asset_job",
    selection=[migrate_metadata_asset],
    config=RunConfig(
        ops={
            "migrate_metadata_asset": MetadataMigrationConfig(
                new_organization=os.environ.get("ORGANIZATION", "your-org"),
                new_deployment=os.environ.get("DEPLOYMENT_NAME", "your-deployment"),
                new_dagster_cloud_api_token=os.environ.get("DAGSTER_CLOUD_API_TOKEN", "your-token"),
                asset_key="my_daily_partitioned_asset",
            )
        }
    ),
)

# Asset group migration job
migrate_asset_group_job = define_asset_job(
    "migrate_asset_group_job",
    selection=[migrate_metadata_asset],
    config=RunConfig(
        ops={
            "migrate_metadata_asset": MetadataMigrationConfig(
                new_organization=os.environ.get("ORGANIZATION", "your-org"),
                new_deployment=os.environ.get("DEPLOYMENT_NAME", "your-deployment"),
                new_dagster_cloud_api_token=os.environ.get("DAGSTER_CLOUD_API_TOKEN", "your-token"),
                asset_group="my_asset_group",
            )
        }
    ),
)

# All assets migration job
migrate_all_assets_job = define_asset_job(
    "migrate_all_assets_job",
    selection=[migrate_metadata_asset],
    config=RunConfig(
        ops={
            "migrate_metadata_asset": MetadataMigrationConfig(
                new_organization=os.environ.get("ORGANIZATION", "your-org"),
                new_deployment=os.environ.get("DEPLOYMENT_NAME", "your-deployment"),
                new_dagster_cloud_api_token=os.environ.get("DAGSTER_CLOUD_API_TOKEN", "your-token"),
                migrate_all=True,
            )
        }
    ),
)

# Backward compatibility - keep original job name
migrate_metadata_job = migrate_single_asset_job
# example record looks like this:
# EventLogRecord(
#     storage_id=2547,
#     event_log_entry=EventLogEntry(
#         error_info=None,
#         level=10,
#         user_message="Materialized value my_daily_partitioned_asset.",
#         run_id="e5d8364f-8bed-4708-871b-3643c6768608",
#         timestamp=1717637561.615922,
#         step_key="my_daily_partitioned_asset",
#         job_name="partitioned_job",
#         dagster_event=DagsterEvent(
#             event_type_value="ASSET_MATERIALIZATION",
#             job_name="partitioned_job",
#             step_handle=StepHandle(
#                 node_handle=NodeHandle(
#                     name="my_daily_partitioned_asset", parent=None
#                 ),
#                 key="my_daily_partitioned_asset",
#             ),
#             node_handle=NodeHandle(name="my_daily_partitioned_asset", parent=None),
#             step_kind_value="COMPUTE",
#             logging_tags={
#                 "job_name": "partitioned_job",
#                 "op_name": "my_daily_partitioned_asset",
#                 "resource_fn_name": "None",
#                 "resource_name": "None",
#                 "run_id": "e5d8364f-8bed-4708-871b-3643c6768608",
#                 "step_key": "my_daily_partitioned_asset",
#             },
#             event_specific_data=StepMaterializationData(
#                 materialization=AssetMaterialization(
#                     asset_key=AssetKey(["my_daily_partitioned_asset"]),
#                     description=None,
#                     metadata={"foo": IntMetadataValue(value=75)},
#                     partition="2024-06-05",
#                     tags={
#                         "dagster/code_version": "e5d8364f-8bed-4708-871b-3643c6768608",
#                         "dagster/data_version": "f3c48603b4643933d49da87f1f18d2e5fa84a1eb64a9f2f5fed4de263e7f2e56",
#                     },
#                 ),
#                 asset_lineage=[],
#             ),
#             message="Materialized value my_daily_partitioned_asset.",
#             pid=61200,
#             step_key="my_daily_partitioned_asset",
#         ),
#     ),
# )
