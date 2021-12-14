import warnings

import numpy
import pandas
from sqlalchemy import Column, String, Date, Numeric, Integer

import dagster
from consumption_datamart.assets.typed_dataframe.typed_dataframe import make_typed_dataframe_dagster_type
from dagster import Output, dagster_type_loader
from dagster.core.asset_defs import asset

warnings.filterwarnings("ignore", category=dagster.ExperimentalWarning)


def list_to_str(values: list):
    s = ';'.join(str(v) for v in values if pandas.notna(v))
    if s == '':
        return numpy.NaN
    return s


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


@dagster_type_loader(
    required_resource_keys={"datawarehouse"},
    config_schema={}
)
def invoice_order_lines_loader(context, _config):
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

    df['meta__warnings'] = numpy.empty((df.shape[0], 0)).tolist()

    has_invalid_customer_id = ~df.customer_id.str.match(r'^CUST-\d+$')
    df.loc[has_invalid_customer_id, 'meta__warnings'] = df.loc[has_invalid_customer_id, 'meta__warnings'].apply(lambda w: w + ['invalid_customer_id'])

    non_vcpu_sku = ~df.subscription_sku.str.contains('VCPU')
    df.loc[non_vcpu_sku, 'meta__warnings'] = df.loc[non_vcpu_sku, 'meta__warnings'].apply(lambda w: w + ['non_vcpu_sku'])

    df.loc[:, 'meta__warnings'] = df['meta__warnings'].apply(list_to_str)

    typed_df = InvoiceOrderItemsDataFrameType.convert_dtypes(df)

    return typed_df


InvoiceOrderItemsDataFrameType = make_typed_dataframe_dagster_type(
    "InvoiceOrderItemsDataFrame", InvoiceOrderItemsDataFrameSchema,
    dataframe_loader=invoice_order_lines_loader,
)


@asset(
    namespace='acme_lake',
    compute_kind='lake',
    dagster_type=InvoiceOrderItemsDataFrameType,
    io_manager_key="lake_input_manager",
)
def invoice_order_lines(context) -> InvoiceOrderItemsDataFrameType:
    """An immutable snapshot containing all customer invoice line items"""

    # TODO: Figure out a more elegant wat to dagster_type
    context.dagster_type = InvoiceOrderItemsDataFrameType
    typed_df = context.resources.lake_input_manager.load_input(context)

    return Output(typed_df, metadata=InvoiceOrderItemsDataFrameType.extract_event_metadata(typed_df))
