from dagster import op, Failure, AssetObservation, Output


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

    success = (df.loc[0, 'row_count'] == 0)

    yield AssetObservation(
        asset_key=["consumption_datamart", "report_active_customers_by_product_daily"],
        partition="2022-02-03",
        metadata={
            "it_should_contain_current_data": "\U00002705" if success else "\U0000274c"
        }
    )

    if not success:
        raise Failure("consumption_datamart.report_active_customers_by_product_daily does not contain any recent data",
                      metadata={'validation_sql': validation_sql})

    yield Output(None)
