from consumption_datamart.phase_2.resources.inmemory_datawarehouse_io_manager import inmemory_datawarehouse_io_manager
from consumption_datamart.phase_2.resources.inmemory_datawarehouse_resources import inmemory_datawarehouse_resource
from consumption_datamart.phase_2.assets.consumption_datamart.report_active_customers_by_product_daily import report_active_customers_by_product_daily
from consumption_datamart.phase_2.monitoring.asset_validation_graph import consumption_datamart_asset_validation_daily
from dagster import repository, ScheduleDefinition
from dagster.core.asset_defs import build_assets_job

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
        report_active_customers_by_product_daily,
    ],
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
def phase_2_inmemory_repository():
    jobs = [
        inmemory_consumption_datamart_job,
        inmemory_monitoring_job,
    ]
    schedules = [
        inmemory_monitoring_schedule
    ]

    return jobs + schedules
