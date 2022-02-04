from dagster import op, Failure

@op(
    tags={'kind': 'asset_validation'},
    required_resource_keys={"datawarehouse"},
)
def it_should_contain_current_data(context):
    """Description of test"""
    validation_sql = """
        SELECT COUNT(*) AS row_count
        FROM consumption_datamart.report_active_customers_by_product_daily
    """
    df = context.resources.datawarehouse.read_sql_query(validation_sql)

    if df.loc[0, 'row_count'] == 0:
        raise Failure("consumption_datamart.report_active_customers_by_product_daily does not contain any recent data",
                      metadata={'validation_sql': validation_sql})
