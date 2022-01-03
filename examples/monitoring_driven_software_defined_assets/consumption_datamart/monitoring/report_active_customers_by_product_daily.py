from pandas._testing import assert_frame_equal

from consumption_datamart.assets.consumption_datamart.report_active_customers_by_product_daily import ActiveCustomerByProductDataFrameType
from dagster import graph, op, Failure


@op(
    tags={'kind': 'asset_validation'},
    required_resource_keys={"datawarehouse"},
)
def it_should_conform_to_the_schema(context):
    """The data returned from consumption_datamart.report_active_customers_by_product_daily should conform to the expected schema"""

    df = context.resources.datawarehouse.read_sql_query("""
        SELECT *
        FROM consumption_datamart.report_active_customers_by_product_daily
    """)
    type_check_result = ActiveCustomerByProductDataFrameType.type_check(
        context=context,
        value=ActiveCustomerByProductDataFrameType.convert_dtypes(df))

    if not type_check_result.success:
        raise Failure("ActiveCustomerByProductDataFrameType type check failed", metadata={'message': type_check_result.description})


@op(
    tags={'kind': 'asset_validation'},
    required_resource_keys={"datawarehouse"},
)
def it_should_contain_a_row_per_customer_product_combo(context):
    """There should be a single row for every unique customer / product combination that has had usage recorded in the last 30 days"""

    df_expected = context.resources.datawarehouse.read_sql_query("""
        SELECT DISTINCT c.customer_id, c.customer_name, p.product_id, p.product_name
        FROM consumption_datamart.fact_usage_daily AS f
        JOIN consumption_datamart.dim_deployment_daily AS d
          ON f.dim_deployment_id = d.dim_deployment_id
         AND f.dim_day_ts = d.dim_day_ts 
        JOIN consumption_datamart.dim_customer_daily AS c
          ON d.dim_customer_id = c.dim_customer_id
         AND f.dim_day_ts = c.dim_day_ts 
        JOIN consumption_datamart.dim_product_daily AS p
          ON d.dim_product_id = p.dim_product_id
         AND f.dim_day_ts = p.dim_day_ts
       WHERE f.dim_day_ts > DATE('now', '-30 day')
    """)

    df_actual = context.resources.datawarehouse.read_sql_query("""
        SELECT customer_id, customer_name, product_id, product_name
        FROM consumption_datamart.report_active_customers_by_product_daily
        WHERE dim_day_ts = DATE('now')
    """)

    try:
        assert_frame_equal(df_expected, df_actual)
    except AssertionError as ae:
        raise Failure(str(ae), metadata={
            'df_expected.head(5)': str(df_expected.head(5)),
            'df_actual.head(5)': str(df_actual.head(5))
        })


@op(
    tags={'kind': 'asset_validation'},
    required_resource_keys={"datawarehouse"},
)
def it_should_contain_a_information_about_foo(context):
    """Description of test"""

    df = context.resources.datawarehouse.read_sql_query("""
        SELECT *
        FROM consumption_datamart.report_active_customers_by_product_daily
    """)
    typed_df = ActiveCustomerByProductDataFrameType.convert_dtypes(df)

    ActiveCustomerByProductDataFrameType.calculate_data_quality(typed_df)


@graph
def validate_report_active_customers_by_product():
    """Description of graph"""

    it_should_conform_to_the_schema()
    it_should_contain_a_row_per_customer_product_combo()
    it_should_contain_a_information_about_foo()

