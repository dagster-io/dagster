from sqlalchemy import Column, DateTime, String, Numeric

from consumption_datamart.assets.acme_lake.cloud_deployment_heartbeats import CloudDeploymentHeartbeatsDataFrameType
from consumption_datamart.assets.acme_lake.invoice_line_items import InvoiceOrderItemsDataFrameType
from consumption_datamart.assets.typed_dataframe.dataframe_schema import DataFrameSchema
from consumption_datamart.assets.typed_dataframe.typed_dataframe import make_typed_dataframe_dagster_type
from dagster import Output
from dagster.core.asset_defs import asset, AssetIn


class FactUsageDailyDataFrameSchema(DataFrameSchema):
    dim_day_ts = Column(
        'dim_day_ts', DateTime, nullable=False,
        comment="Day this row's data represents (UTC)")
    dim_deployment_id = Column(
        'dim_deployment_id', String, nullable=False,
        comment="Deployment Identifier")
    usage_quantity = Column(
        'usage_quantity', Numeric(12, 2), nullable=False,
        comment="Quantity of usage used by this deployment at time: dim_day_ts")
    usage_unit = Column(
        'usage_unit', String, nullable=False,
        comment="Unit of usage")


FactUsageDailyDataFrameType = make_typed_dataframe_dagster_type(
    "FactUsageDailyDataFrame", FactUsageDailyDataFrameSchema()
)


@asset(
    namespace='consumption_datamart',
    compute_kind='mart',
    required_resource_keys={"datawarehouse"},
    ins={
        'cloud_deployment_heartbeats': AssetIn(namespace="acme_lake"),
        'invoice_order_lines': AssetIn(namespace="acme_lake"),
    },
    io_manager_key="datawarehouse_io_manager",
    metadata={
       "load_sql": """
          SELECT *
          FROM consumption_datamart.fact_usage_daily
       """,
       "dagster_type": FactUsageDailyDataFrameType
    },
)
def fact_usage_daily(context,
                     cloud_deployment_heartbeats: CloudDeploymentHeartbeatsDataFrameType,
                     invoice_order_lines: InvoiceOrderItemsDataFrameType,
                     ) -> FactUsageDailyDataFrameType:
    """Daily facts related to usage"""

    df = context.resources.datawarehouse.read_sql_query("""
        SELECT 
            h.ts AS dim_day_ts
        ,   h.deployment_id AS dim_deployment_id
        ,   'PRODUCT_1' AS dim_product_id
        ,   1.0 AS usage_quantity
        ,   'flux capacitors' AS usage_unit
        FROM acme_lake.cloud_deployment_heartbeats AS h
    """)

    typed_df = FactUsageDailyDataFrameType.convert_dtypes(df)

    return Output(typed_df, metadata=FactUsageDailyDataFrameType.extract_event_metadata(typed_df))
