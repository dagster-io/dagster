from consumption_datamart.common.daily_partitions import daily_partitions
from consumption_datamart.phase_2.resources.fs_csv_io_manager import fs_csv_io_manager
from consumption_datamart.phase_2.resources.inmemory_datawarehouse_io_manager import inmemory_datawarehouse_io_manager
from consumption_datamart.phase_2.resources.fs_datawarehouse_io_manager import fs_datawarehouse_io_manager
from consumption_datamart.phase_2.resources.inmemory_datawarehouse_resources import inmemory_datawarehouse_resource
from consumption_datamart.phase_2.resources.fs_datawarehouse_resources import fs_datawarehouse_resource
from consumption_datamart.phase_2.assets.consumption_datamart.csv_active_customers_by_product import csv_active_customers_by_product
from consumption_datamart.phase_2.assets.consumption_datamart.report_active_customers_by_product_daily import report_active_customers_by_product_daily
from consumption_datamart.phase_2.monitoring.asset_validation_graph import consumption_datamart_asset_validation_daily
from dagster import repository, ScheduleDefinition, file_relative_path
from dagster.core.asset_defs import build_assets_job


inmemory_consumption_datamart_job = build_assets_job(
    name="consumption_datamart",
    description=(
        "Consumption focussed data mart"
    ),
    resource_defs={
        "datawarehouse": inmemory_datawarehouse_resource.configured({
            "log_sql": False
        }),
        "datawarehouse_io_manager": inmemory_datawarehouse_io_manager.configured({
            "log_sql": False
        }),
        "fs_csv_io_manager": fs_csv_io_manager.configured({
            "data_folder": file_relative_path(__file__, '../../schema')
        }),
    },
    source_assets=[
        csv_active_customers_by_product
    ],
    assets=[
        report_active_customers_by_product_daily,
    ],
)
inmemory_monitoring_job = consumption_datamart_asset_validation_daily.to_job(
    resource_defs={
        "datawarehouse": inmemory_datawarehouse_resource.configured({
            "log_sql": False
        }),
    },
    partitions_def=daily_partitions
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


fs_consumption_datamart_job = build_assets_job(
    name="consumption_datamart",
    description=(
        "Consumption focussed data mart"
    ),
    resource_defs={
        "datawarehouse": fs_datawarehouse_resource.configured({
            "log_sql": False,
            "base_path": file_relative_path(__file__, '../../schema/phase_2')
        }),
        "datawarehouse_io_manager": fs_datawarehouse_io_manager.configured({
            "log_sql": False,
            "base_path": file_relative_path(__file__, '../../schema/phase_2')
        }),
        "fs_csv_io_manager": fs_csv_io_manager.configured({
            "data_folder": file_relative_path(__file__, '../../schema')
        }),
    },
    source_assets=[
        csv_active_customers_by_product
    ],
    assets=[
        report_active_customers_by_product_daily,
    ],
)
fs_monitoring_job = consumption_datamart_asset_validation_daily.to_job(
    resource_defs={
        "datawarehouse": fs_datawarehouse_resource.configured({
            "log_sql": False,
            "base_path": file_relative_path(__file__, '../../schema/phase_2')
        }),
    },
    partitions_def=daily_partitions
)
fs_monitoring_schedule = ScheduleDefinition(job=fs_monitoring_job, cron_schedule="0 0 * * *")


@repository
def phase_2_fs_repository():
    jobs = [
        fs_consumption_datamart_job,
        fs_monitoring_job,
    ]
    schedules = [
        fs_monitoring_schedule
    ]

    return jobs + schedules
