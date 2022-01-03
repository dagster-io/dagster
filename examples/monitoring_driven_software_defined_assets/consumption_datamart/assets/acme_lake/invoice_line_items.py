import warnings

from sqlalchemy import Column, String, Date, Numeric, Integer

import dagster
from consumption_datamart.assets.typed_dataframe.dataframe_schema import DataFrameSchema
from consumption_datamart.assets.typed_dataframe.typed_dataframe import make_typed_dataframe_dagster_type, list_to_str, str_to_list
from dagster import Output
from dagster.core.asset_defs import asset

warnings.filterwarnings("ignore", category=dagster.ExperimentalWarning)


class InvoiceOrderItemsDataFrameSchema(DataFrameSchema):
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

    @staticmethod
    def calculate_data_quality(df):
        df['meta__warnings'] = df['meta__warnings'].apply(str_to_list)

        has_invalid_customer_id = ~df.customer_id.str.match(r'^CUST-\d+$')
        df.loc[has_invalid_customer_id, 'meta__warnings'] = df.loc[has_invalid_customer_id, 'meta__warnings'].apply(lambda w: w + ['invalid_customer_id'])

        non_vcpu_sku = ~df.subscription_sku.str.contains('VCPU')
        df.loc[non_vcpu_sku, 'meta__warnings'] = df.loc[non_vcpu_sku, 'meta__warnings'].apply(lambda w: w + ['non_vcpu_sku'])

        df.loc[:, 'meta__warnings'] = df['meta__warnings'].apply(list_to_str)

        return df


InvoiceOrderItemsDataFrameType = make_typed_dataframe_dagster_type(
    "InvoiceOrderItemsDataFrame", InvoiceOrderItemsDataFrameSchema()
)


@asset(
    namespace='acme_lake',
    compute_kind='lake',
    io_manager_key="datawarehouse_io_manager",
    metadata={
        "load_sql": """
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
        """,
        "dagster_type": InvoiceOrderItemsDataFrameType
    },
)
def invoice_order_lines(context) -> InvoiceOrderItemsDataFrameType:
    """An immutable snapshot containing all customer invoice line items"""

    asset_out = context.solid_def.outs['result']
    dagster_type = asset_out.metadata['dagster_type']

    typed_df = context.resources.datawarehouse_io_manager.load_input(context)

    yield Output(typed_df, metadata=dagster_type.extract_event_metadata(typed_df))
