import warnings
from textwrap import dedent

import pandas

import dagster
from dagster import Output, EventMetadata
from dagster.core.asset_defs import asset

warnings.filterwarnings("ignore", category=dagster.ExperimentalWarning)


@asset(
    namespace='acme_lake',
    compute_kind='lake',
    required_resource_keys={"datawarehouse"},
)
def invoice_order_lines(context) -> pandas.DataFrame:
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

    yield Output(
        df,
        metadata={
            "Data Dictionary": EventMetadata.md(dedent(f"""
                | Column              	         | Type   	| Description                                            |
                |--------------------------------|----------|--------------------------------------------------------|
                | invoice_id        	         | String 	| Id of the invoice                                      |
                | order_date          	         | String 	| Date the Order was place (and the subscription started |
                | customer_id          	         | String 	| Customer Identifier                                    |
                | subscription_sku   	         | String 	| SKU the subscription order is for                      |
                | subscription_sku_name       	 | String 	| Name of SKU                                            |
                | subscription_quantity          | Decimal 	| Quantity of subscription                               |
                | subscription_term              | Int   	| Length of the subscription (in months)                 |                
            """)),
            "n_rows": EventMetadata.int(len(df)),
            "tail(5)": EventMetadata.md(df.tail(5).to_markdown()),
        },
    )
