import pandas as pd
from dagster import DataVersion, observable_source_asset

from .resources import BigQueryResource

"""
Running the following query in bigquery gets you the last updated timestamp:
select
  table_id,
  TIMESTAMP_MILLIS(last_modified_time) AS last_modified
from
  `elementl-dev.IRIS.__TABLES__`; (elementl-dev is project_id, IRIS is dataset_id). To narrow this to a particular table, you can add a where clause for table_id.
"""


def observe_table_factory(dataset_id, table_id):
    @observable_source_asset
    def observe_table_last_modified_time(context, bigquery: BigQueryResource) -> DataVersion:
        with bigquery.get_client() as client:
            query = f"""
            select
              table_id,
              TIMESTAMP_MILLIS(last_modified_time) AS last_modified
            from
              `{bigquery.project}.{dataset_id}.__TABLES__`
            where
              table_id = '{table_id}'
            """
            df = client.query(query).to_dataframe()
        # context.log.info the last modified time as a UTC timestamp.
        context.log.info(
            f"Last modified time for table {table_id}: {df['last_modified'].values[0]}"
        )
        timestamp = pd.to_datetime(df["last_modified"].values[0])
        return DataVersion(str(timestamp))

    return observe_table_last_modified_time
