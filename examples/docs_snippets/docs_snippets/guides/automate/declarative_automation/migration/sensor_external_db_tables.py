import dagster as dg


@dg.asset
def sales_report(): ...


analytics_job = dg.define_asset_job("analytics_job", selection=["sales_report"])


@dg.sensor(job=analytics_job, minimum_interval_seconds=60)
def db_table_sensor(context: dg.SensorEvaluationContext):
    last_checked = float(context.cursor) if context.cursor else 0

    # Query the database's information schema for table update times
    updated_tables = query_information_schema(last_checked)

    if updated_tables:
        context.update_cursor(str(max(t["last_altered"] for t in updated_tables)))
        return dg.RunRequest()


def query_information_schema(since_timestamp: float) -> list:
    # In practice, this would query your database, e.g.:
    # SELECT table_name, last_altered
    # FROM information_schema.tables
    # WHERE last_altered > :since_timestamp
    ...
