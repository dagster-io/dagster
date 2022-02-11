import sqlalchemy
from sqlalchemy import Column, DateTime, String, bindparam

from consumption_datamart.common.daily_partitions import daily_partitions
from consumption_datamart.common.typed_dataframe.dataframe_schema import DataFrameSchema
from consumption_datamart.common.typed_dataframe.typed_dataframe import make_typed_dataframe_dagster_type
from dagster import Output
from dagster.core.asset_defs import asset


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
    namespace=['phase_1', 'consumption_datamart'],
    compute_kind='mart_view',
    required_resource_keys={"datawarehouse"},
    partitions_def=daily_partitions,
    description=f"""Active Customers By Product Report
-
A customer is considered active if they have any product usage during the preceding 30 days

{ActiveCustomerByProductDataFrameType.schema_as_markdown()}
"""
)
def report_active_customers_by_product_daily(context) -> ActiveCustomerByProductDataFrameType:

    sql = sqlalchemy.text("""
        SELECT *
        FROM consumption_datamart.report_active_customers_by_product_daily
        WHERE dim_day_ts = :partition_key
    """).bindparams(bindparam('partition_key', value=context.partition_key))

    df = context.resources.datawarehouse.read_sql_query(sql)

    typed_df = ActiveCustomerByProductDataFrameType.convert_dtypes(df)

    yield Output(typed_df, metadata=ActiveCustomerByProductDataFrameType.extract_event_metadata(typed_df))
