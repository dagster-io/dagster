import warnings

from sqlalchemy import Column, String, Date, Numeric, Integer

import dagster
from consumption_datamart.assets.typed_dataframe.typed_dataframe import make_typed_dataframe_dagster_type
from dagster import Output
from dagster.core.asset_defs import asset

warnings.filterwarnings("ignore", category=dagster.ExperimentalWarning)


class InvoiceOrderItemsDataFrameSchema:
    invoice_id = Column(
        'invoice_id', String, nullable=False,
        comment="Id of the invoice")
    order_date = Column(
        'order_date', Date, nullable=False,
        comment="Date the Order was place (and the subscription started")
    customer_id = Column(
        'customer_id', String, nullable=False,
        comment="Customer Identifier")
    subscription_sku = Column(
        'subscription_sku', String, nullable=False,
        comment="SKU the subscription order is for")
    subscription_sku_name = Column(
        'subscription_sku_name', String, nullable=False,
        comment="SKU the subscription order is for")
    subscription_quantity = Column(
        'subscription_quantity', Numeric(12, 2), nullable=False,
        comment="Quantity of subscription")
    subscription_term = Column(
        'subscription_term', Integer, nullable=False,
        comment="subscription_term")


InvoiceOrderItemsDataFrameType = make_typed_dataframe_dagster_type("InvoiceOrderItemsDataFrame", InvoiceOrderItemsDataFrameSchema)


@asset(
    namespace='acme_lake',
    compute_kind='lake',
    required_resource_keys={"datawarehouse"},
)
def invoice_order_lines(context) -> InvoiceOrderItemsDataFrameType:
    """An immutable snapshot containing all customer invoice line items"""

    df = context.resources.datawarehouse.read_sql_query('''
        SELECT
            invoice_id
        ,   order_date
        ,   customer_id
        ,   customer_name
        ,   subscription_sku
        ,   subscription_sku_name
        ,   subscription_quantity
        ,   subscription_term
        FROM acme_lake.invoice_line_items
    ''')

    typed_df = InvoiceOrderItemsDataFrameType.convert_dtypes(df)

    return Output(typed_df, metadata=InvoiceOrderItemsDataFrameType.extract_event_metadata(df))
