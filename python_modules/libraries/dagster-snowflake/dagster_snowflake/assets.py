from dagster import DataVersion, observable_source_asset

from .resources import SnowflakeResource

"""
Running the following query in snowflake gets you the last updated timestamp:
SELECT table_name, last_altered
FROM information_schema.tables
WHERE table_schema = 'your_schema' AND table_name = 'your_table_name';
  """


def observe_table_factory(schema, table):
    @observable_source_asset
    def observe_table_last_modified_time(context, snowflake: SnowflakeResource) -> DataVersion:
        with snowflake.get_connection() as conn:
            query = f"""
            SELECT table_name, last_altered
            FROM information_schema.tables
            WHERE table_schema = '{schema}' AND table_name = '{table}';
            """
            with conn.cursor() as cursor:
                result = cursor.execute(query)
                if not result:
                    raise ValueError("No results found")
                results = result.fetchall()

        # context.log.info the last modified time as a UTC timestamp.
        context.log.info(f"Last modified time for table {table}: {results[0][1]}")
        return DataVersion(results[0][1].strftime("%Y-%m-%d %H:%M:%S.%f"))

    return observe_table_last_modified_time
