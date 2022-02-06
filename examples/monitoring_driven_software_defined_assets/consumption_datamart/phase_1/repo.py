from consumption_datamart.common.daily_partitions import daily_partitions
from consumption_datamart.phase_1.resources.inmemory_datawarehouse_resource import inmemory_datawarehouse_resource
from consumption_datamart.phase_1.assets.consumption_datamart.report_active_customers_by_product_daily import report_active_customers_by_product_daily
from consumption_datamart.phase_1.monitoring.asset_validation_graph import consumption_datamart_asset_validation_daily
from dagster import repository, ScheduleDefinition
from dagster.core.asset_defs import build_assets_job

inmemory_consumption_datamart_job = build_assets_job(
    name="consumption_datamart",
    description=(
        "Consumption focussed data mart"
    ),
    resource_defs={
        "datawarehouse": inmemory_datawarehouse_resource,
    },
    assets=[
        report_active_customers_by_product_daily,
    ],
)
inmemory_monitoring_job = consumption_datamart_asset_validation_daily.to_job(
    resource_defs={
        "datawarehouse": inmemory_datawarehouse_resource,
    },
    partitions_def=daily_partitions
)
inmemory_monitoring_schedule = ScheduleDefinition(job=inmemory_monitoring_job, cron_schedule="0 0 * * *")


@repository
def phase_1_inmemory_repository():
    jobs = [
        inmemory_consumption_datamart_job,
        inmemory_monitoring_job,
    ]
    schedules = [
        inmemory_monitoring_schedule
    ]

    return jobs + schedules
