import warnings

import dagster
from consumption_datamart.assets.acme_lake.cloud_deployment_heartbeats import cloud_deployment_heartbeats
from consumption_datamart.assets.acme_lake.invoice_line_items import invoice_order_lines
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
                })
            },
            assets=[
                invoice_order_lines, cloud_deployment_heartbeats
            ]
        ),
    ]

    return jobs
