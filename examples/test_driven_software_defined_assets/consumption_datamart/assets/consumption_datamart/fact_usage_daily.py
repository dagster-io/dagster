from sqlalchemy import Column, DateTime, String

from consumption_datamart.assets.acme_lake.cloud_deployment_heartbeats import CloudDeploymentHeartbeatsDataFrameType
from consumption_datamart.assets.acme_lake.invoice_line_items import InvoiceOrderItemsDataFrameType
from consumption_datamart.assets.typed_dataframe.typed_dataframe import make_typed_dataframe_dagster_type
from dagster import Output
from dagster.core.asset_defs import asset, AssetIn


class FactUsageDailyDataFrameSchema:
    dim_day_ts = Column(
        'ts', DateTime, nullable=False,
        comment="Day this row's data represents (UTC)")
    deployment_id = Column(
        'deployment_id', String, nullable=False,
        comment="Deployment Identifier")


FactUsageDailyDataFrameType = make_typed_dataframe_dagster_type(
    "FactUsageDailyDataFrame", FactUsageDailyDataFrameSchema)


@asset(
    namespace='consumption_datamart',
    compute_kind='mart',
    required_resource_keys={"datawarehouse"},
    ins={
        'cloud_deployment_heartbeats': AssetIn(namespace="acme_lake"),
        'invoice_order_lines': AssetIn(namespace="acme_lake"),
    }
)
def fact_usage_daily(_context,
                     cloud_deployment_heartbeats: CloudDeploymentHeartbeatsDataFrameType,
                     invoice_order_lines: InvoiceOrderItemsDataFrameType,
                     ) -> FactUsageDailyDataFrameType:
    """Daily facts related to usage"""

    # TODO construct daily usage from inputs
    total_heartbeats = len(cloud_deployment_heartbeats)
    total_line_items = len(invoice_order_lines)

    typed_df = FactUsageDailyDataFrameType.empty()

    return Output(typed_df, metadata=FactUsageDailyDataFrameType.extract_event_metadata(typed_df))
