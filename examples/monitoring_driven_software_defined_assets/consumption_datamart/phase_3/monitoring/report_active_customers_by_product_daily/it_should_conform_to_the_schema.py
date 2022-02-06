from consumption_datamart.phase_3.assets.consumption_datamart.report_active_customers_by_product_daily import ActiveCustomerByProductDataFrameType
from dagster import op, Failure, AssetObservation, Output


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

    yield AssetObservation(
        asset_key=["consumption_datamart", "report_active_customers_by_product_daily"],
        partition="2022-02-03",
        metadata={"it_should_conform_to_the_schema": "True"}
    )

    if not type_check_result.success:
        raise Failure("ActiveCustomerByProductDataFrameType type check failed", metadata={'message': type_check_result.description})

    yield Output(None)

