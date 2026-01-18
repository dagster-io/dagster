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
    asset_key: str


@asset
def migrate_metadata_asset(context: AssetExecutionContext, config: MetadataMigrationConfig):
    new_organization = config.new_organization
    new_deployment = config.new_deployment
    new_dagster_cloud_api_token = config.new_dagster_cloud_api_token
    asset_key = config.asset_key
    cursor = None

    # can partition this to run in parallel
    for _ in range(100):
        result: EventRecordsResult = context.instance.fetch_materializations(
            records_filter=AssetKey.from_user_string(asset_key),
            limit=1,
            cursor=cursor,
        )
        record: EventLogRecord = result.records[0]
        dagster_event = record.event_log_entry.dagster_event
        if dagster_event is not None:
            data = dagster_event.event_specific_data.materialization  # pyright: ignore[reportAttributeAccessIssue,reportOptionalMemberAccess]
            partition_to_report = data.partition
            metadata_to_report = {key: value.value for key, value in data.metadata.items()}
        cursor = result.cursor
        _report_asset_materialization_to_dagster_plus(
            new_organization=new_organization,
            new_deployment=new_deployment,
            new_dagster_cloud_api_token=new_dagster_cloud_api_token,
            asset_key=asset_key,
            partition=partition_to_report,  # type: ignore
            metadata=metadata_to_report,  # type: ignore
        )
        print(f"Migrated asset {asset_key} for partition {partition_to_report}")  # type: ignore # noqa: T201


migrate_metadata_job = define_asset_job(
    "migrate_metadata_job",
    selection=[migrate_metadata_asset],
    config=RunConfig(
        ops={
            "migrate_metadata_asset": MetadataMigrationConfig(
                new_organization=os.environ["ORGANIZATION"],
                new_deployment=os.environ["DEPLOYMENT_NAME"],
                new_dagster_cloud_api_token=os.environ["DAGSTER_CLOUD_API_TOKEN"],
                asset_key="my_daily_partitioned_asset",
            )
        }
    ),
)
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
