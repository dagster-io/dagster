import sqlalchemy
from sqlalchemy import bindparam

from dagster import op, Failure, AssetObservation, Output


@op(
    tags={'kind': 'asset_validation'},
    required_resource_keys={"datawarehouse"},
)
def it_should_contain_current_data(context):
    """The consumption_datamart.report_active_customers_by_product_daily dataset should contain data for the current partition"""

    validation_sql = sqlalchemy.text("""
        SELECT COUNT(*) AS row_count
        FROM consumption_datamart.report_active_customers_by_product_daily
        WHERE dim_day_ts = :partition_key
    """).bindparams(bindparam('partition_key', value=context.partition_key))
    df = context.resources.datawarehouse.read_sql_query(validation_sql)

    success = (df.loc[0, 'row_count'] > 0)

    yield AssetObservation(
        asset_key=['phase_1', 'consumption_datamart', 'report_active_customers_by_product_daily'],
        partition=context.partition_key,
        metadata={
            "it_should_contain_current_data": "\U00002705" if success else "\U0000274c"
        }
    )

    if not success:
        raise Failure("consumption_datamart.report_active_customers_by_product_daily does not contain any recent data",
                      metadata={
                          'validation_sql': str(validation_sql.compile(compile_kwargs={"literal_binds": True}))
                      })

    yield Output(None)
