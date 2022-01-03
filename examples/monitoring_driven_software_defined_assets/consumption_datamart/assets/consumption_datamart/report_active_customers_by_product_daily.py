import textwrap

from sqlalchemy import Column, DateTime, String

from consumption_datamart.assets.consumption_datamart.fact_usage_daily import FactUsageDailyDataFrameType
from consumption_datamart.assets.typed_dataframe.dataframe_schema import DataFrameSchema
from consumption_datamart.assets.typed_dataframe.typed_dataframe import make_typed_dataframe_dagster_type
from dagster import Output
from dagster.core.asset_defs import asset, AssetIn


class ActiveCustomerByProductDataFrameSchema(DataFrameSchema):
    dim_day_ts = Column(
        'dim_day_ts', DateTime, nullable=False,
        comment="Day this row's data represents (UTC)")
    product_id = Column(
        'product_id', String, nullable=False,
        comment="Product Identifier")
    product_name = Column(
        'product_name', String, nullable=False,
        comment="Product Name")
    customer_id = Column(
        'customer_id', String, nullable=False,
        comment="Customer Identifier")
    customer_name = Column(
        'customer_name', String, nullable=False,
        comment="Customer Name")


ActiveCustomerByProductDataFrameType = make_typed_dataframe_dagster_type(
    "ActiveCustomerByProductDataFrameType", ActiveCustomerByProductDataFrameSchema()
)

@asset(
    namespace='consumption_datamart',
    compute_kind='mart_view',
    ins={
        'fact_usage_daily': AssetIn(namespace="consumption_datamart"),
    },
    io_manager_key="datawarehouse_io_manager",
    metadata={
        "load_sql": """
            SELECT *
            FROM consumption_datamart.report_active_customers_by_product_daily
        """,
        "dagster_type": ActiveCustomerByProductDataFrameType
    },
    description=f"""Active Customers By Product Report
-
A customer is considered active if they have any product usage during the preceding 30 days

{ActiveCustomerByProductDataFrameType.schema_as_markdown()}
"""
)
def report_active_customers_by_product_daily(context, fact_usage_daily: FactUsageDailyDataFrameType) -> ActiveCustomerByProductDataFrameType:

    asset_out = context.solid_def.outs['result']
    dagster_type = asset_out.metadata['dagster_type']

    typed_df = context.resources.datawarehouse_io_manager.load_input(context)

    yield Output(typed_df, metadata=dagster_type.extract_event_metadata(typed_df))
