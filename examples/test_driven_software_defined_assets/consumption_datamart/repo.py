import warnings

import dagster
from consumption_datamart.assets.acme_lake.cloud_deployment_heartbeats import cloud_deployment_heartbeats
from consumption_datamart.assets.acme_lake.invoice_line_items import invoice_order_lines
from consumption_datamart.assets.acme_lake.sql_lake_io_manager import asset_lake_input_manager, \
    foreign_asset_lake_input_manager
from consumption_datamart.assets.consumption_datamart.fact_usage_daily import fact_usage_daily
from consumption_datamart.resources.datawarehouse_resources import inmemory_datawarehouse_resource
from dagster import repository
from dagster.core.asset_defs import build_assets_job

warnings.filterwarnings("ignore", category=dagster.ExperimentalWarning)


@repository
def dev_repository():
    jobs = [
        build_assets_job(
            name="acme_lake",
            description=(
                "TODO"
            ),
            resource_defs={
                "datawarehouse": inmemory_datawarehouse_resource.configured({
                    "log_sql": True
                }),
                "lake_input_manager": asset_lake_input_manager.configured({}),
            },
            assets=[
                invoice_order_lines,
            ]
        ),
        build_assets_job(
            name="consumption_datamart",
            description=(
                "TODO"
            ),
            resource_defs={
                "datawarehouse": inmemory_datawarehouse_resource.configured({
                    "log_sql": True
                }),
                "lake_input_manager": foreign_asset_lake_input_manager.configured({}),
            },
            assets=[
                fact_usage_daily,
            ],
            source_assets=[
                invoice_order_lines,
                cloud_deployment_heartbeats
            ]
        ),
    ]

    return jobs
