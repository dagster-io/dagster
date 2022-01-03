import warnings

import dagster
from consumption_datamart.monitoring.asset_validation_graph import consumption_datamart_asset_validation_daily
from consumption_datamart.assets.acme_lake.cloud_deployment_heartbeats import cloud_deployment_heartbeats
from consumption_datamart.assets.acme_lake.invoice_line_items import invoice_order_lines
from consumption_datamart.assets.consumption_datamart.report_active_customers_by_product_daily import report_active_customers_by_product_daily
from consumption_datamart.assets.consumption_datamart.fact_usage_daily import fact_usage_daily
from consumption_datamart.resources.datawarehouse_resources import inmemory_datawarehouse_resource
from consumption_datamart.resources.datawarehouse_io_manager import inmemory_datawarehouse_io_manager

from dagster import repository, ScheduleDefinition
from dagster.core.asset_defs import build_assets_job

warnings.filterwarnings("ignore", category=dagster.ExperimentalWarning)

inmemory_acme_lake_job = build_assets_job(
    name="acme_lake",
    description=(
        "TODO"
    ),
    resource_defs={
        "datawarehouse": inmemory_datawarehouse_resource.configured({
            "log_sql": False
        }),
        "datawarehouse_io_manager": inmemory_datawarehouse_io_manager.configured({
            "log_sql": False
        }),
    },
    assets=[
        invoice_order_lines,
    ]
)
inmemory_consumption_datamart_job = build_assets_job(
    name="consumption_datamart",
    description=(
        "TODO"
    ),
    resource_defs={
        "datawarehouse": inmemory_datawarehouse_resource.configured({
            "log_sql": False
        }),
        "datawarehouse_io_manager": inmemory_datawarehouse_io_manager.configured({
            "log_sql": False
        }),
    },
    assets=[
        fact_usage_daily,
        report_active_customers_by_product_daily,
    ],
    source_assets=[
        invoice_order_lines,
        cloud_deployment_heartbeats
    ]
)
inmemory_monitoring_job = consumption_datamart_asset_validation_daily.to_job(
    resource_defs={
        "datawarehouse": inmemory_datawarehouse_resource.configured({
            "log_sql": False
        }),
    }
)
inmemory_monitoring_schedule = ScheduleDefinition(job=inmemory_monitoring_job, cron_schedule="0 0 * * *")


@repository
def inmemory_repository():
    jobs = [
        inmemory_acme_lake_job,
        inmemory_consumption_datamart_job,
        inmemory_monitoring_job,
    ]
    schedules = [
        inmemory_monitoring_schedule
    ]

    return jobs + schedules
