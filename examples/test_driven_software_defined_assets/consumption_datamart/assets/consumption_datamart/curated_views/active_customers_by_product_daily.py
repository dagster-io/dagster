from dagster import Output, op
from dagster.core.asset_defs import asset, AssetIn
from sqlalchemy import Column, DateTime, String

from consumption_datamart.assets.consumption_datamart.fact_usage_daily import FactUsageDailyDataFrameType
from consumption_datamart.assets.typed_dataframe.dataframe_schema import DataFrameSchema
from consumption_datamart.assets.typed_dataframe.typed_dataframe import make_typed_dataframe_dagster_type


class ActiveCustomerByProductDataFrameSchema(DataFrameSchema):
    dim_day_ts = Column(
        'ts', DateTime, nullable=False,
        comment="Day this row's data represents (UTC)")
    product_id = Column(
        'product_id', String, nullable=False,
        comment="Customer Identifier")
    customer_id = Column(
        'customer_id', String, nullable=False,
        comment="Customer Identifier")


ActiveCustomerByProductDataFrameType = make_typed_dataframe_dagster_type(
    "ActiveCustomerByProductDataFrameType", ActiveCustomerByProductDataFrameSchema()
)


@asset(
    namespace='consumption_datamart_curated_views',
    compute_kind='mart',
    required_resource_keys={"datawarehouse"},
    ins={
        'fact_usage_daily': AssetIn(namespace="consumption_datamart"),
    }
)
def active_customers_by_product_daily(context,
                                      fact_usage_daily: FactUsageDailyDataFrameType,
                     ) -> ActiveCustomerByProductDataFrameType:
    """Active Customers By Product
    A customer is considered active if they have any product usage during the preceding 30 days
    """

    context.resources.datawarehouse.update_view(
        schema="consumption_datamart", view_name="active_customers_by_product_daily",
        comment="Active Customers By Product",
        view_query="""
        SELECT
            CAST('2021-01-01' AS TIMESTAMP) AS ts
        ,   'product_1'                     AS product_id
        ,   'customer_1'                    AS customer_id
        FROM consumption_datamart.fact_usage_daily 
        """)

    df = context.resources.datawarehouse.read_sql_query("""
        SELECT *
        FROM consumption_datamart.active_customers_by_product_daily
    """)
    typed_df = ActiveCustomerByProductDataFrameType.convert_dtypes(df)

    ActiveCustomerByProductDataFrameType.calculate_data_quality(typed_df)

    return Output(typed_df, metadata=ActiveCustomerByProductDataFrameType.extract_event_metadata(typed_df))


@op(
    tags={'kind': 'monitoring'},
    required_resource_keys={"datawarehouse"},
)
def validate_active_customers_by_product_daily(context):
    """Validate the active customers by product daily asset
    """

    df = context.resources.datawarehouse.read_sql_query("""
        SELECT *
        FROM consumption_datamart.active_customers_by_product_daily
    """)
    typed_df = ActiveCustomerByProductDataFrameType.convert_dtypes(df)

    ActiveCustomerByProductDataFrameType.calculate_data_quality(typed_df)

    return Output(True, metadata=ActiveCustomerByProductDataFrameType.extract_event_metadata(typed_df))

