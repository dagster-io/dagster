from dagster_gcp import BigQueryResource
from google.cloud import bigquery as bq

# start_example
from dagster import asset

from .create_table import iris_data

# this example uses the iris_dataset asset from Step 2


@asset(deps=[iris_data])
def iris_setosa(bigquery: BigQueryResource) -> None:
    job_config = bq.QueryJobConfig(destination="iris.iris_setosa")
    sql = "SELECT * FROM iris.iris_data WHERE species = 'Iris-setosa'"

    with bigquery.get_client() as client:
        job = client.query(sql, job_config=job_config)
        job.result()


# end_example
