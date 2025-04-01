from dagster import asset


@asset
def my_other_asset(): ...


# start_check
from dagster import build_column_schema_change_checks

schema_checks = build_column_schema_change_checks(assets=[my_other_asset])

# end_check
