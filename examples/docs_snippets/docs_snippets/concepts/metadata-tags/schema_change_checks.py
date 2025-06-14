from dagster import asset


@asset
def my_other_asset(): ...


# start_check
import dagster as dg

schema_checks = dg.build_column_schema_change_checks(assets=[my_other_asset])

# end_check
