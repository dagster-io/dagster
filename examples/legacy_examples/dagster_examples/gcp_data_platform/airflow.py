import datetime
import os

from airflow.contrib.operators import dataproc_operator
from airflow.contrib.operators.bigquery_operator import BigQueryOperator
from airflow.contrib.operators.gcs_to_bq import GoogleCloudStorageToBigQueryOperator
from airflow.models import DAG
from airflow.utils import trigger_rule

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DEPLOY_BUCKET_PREFIX = os.getenv("GCP_DEPLOY_BUCKET_PREFIX")
INPUT_BUCKET = os.getenv("GCP_INPUT_BUCKET")
OUTPUT_BUCKET = os.getenv("GCP_OUTPUT_BUCKET")

REGION = "us-west1"
LATEST_JAR_HASH = "214f4bff2eccb4e9c08578d96bd329409b7111c8"

yesterday = datetime.datetime.combine(
    datetime.datetime.today() - datetime.timedelta(1), datetime.datetime.min.time()
)

default_dag_args = {
    "start_date": yesterday,
    "email_on_failure": False,
    "email_on_retry": False,
    "email": ["airflow@example.com"],
}

with DAG(
    "gcp_data_platform", schedule_interval=datetime.timedelta(days=1), default_args=default_dag_args
) as dag:

    create_dataproc_cluster = dataproc_operator.DataprocClusterCreateOperator(
        project_id=PROJECT_ID,
        task_id="create_dataproc_cluster",
        cluster_name="gcp-data-platform",
        num_workers=0,
        zone="us-west1a",
        master_machine_type="n1-highmem-4",
    )

    run_dataproc_spark = dataproc_operator.DataProcSparkOperator(
        task_id="events_dataproc",
        cluster_name="gcp-data-platform",
        region=REGION,
        main_class="io.dagster.events.EventPipeline",
        dataproc_spark_jars=["%s/events-assembly-%s.jar" % (DEPLOY_BUCKET_PREFIX, LATEST_JAR_HASH)],
        arguments=[
            "--gcs-input-bucket",
            INPUT_BUCKET,
            "--gcs-output-bucket",
            OUTPUT_BUCKET,
            "--date",
            "{{ ds }}",
        ],
    )

    delete_dataproc_cluster = dataproc_operator.DataprocClusterDeleteOperator(
        project_id=PROJECT_ID,
        task_id="delete_dataproc_cluster",
        cluster_name="gcp-data-platform",
        trigger_rule=trigger_rule.TriggerRule.ALL_DONE,
    )

    gcs_to_bigquery = GoogleCloudStorageToBigQueryOperator(
        task_id="gcs_to_bigquery",
        bucket=OUTPUT_BUCKET,
        source_objects=['{{ ds_format(ds, "%Y/%m/%d") }}/*.parquet'],
        destination_project_dataset_table="{project_id}.events.events{{ ds_nodash }}".format(
            project_id=PROJECT_ID
        ),
        source_format="PARQUET",
        create_disposition="CREATE_IF_NEEDED",
        write_disposition="WRITE_TRUNCATE",
    )

    explore_visits_by_hour = BigQueryOperator(
        task_id="explore_visits_by_hour",
        sql="""
   SELECT FORMAT_DATETIME("%F %H:00:00", DATETIME(TIMESTAMP_SECONDS(CAST(timestamp AS INT64)))) AS ts,
          COUNT(1) AS num_visits
     FROM events.events
    WHERE url = '/explore'
 GROUP BY ts
 ORDER BY ts ASC
 """,
        destination_dataset_table="aggregations.explore_visits_per_hour",
        create_disposition="CREATE_IF_NEEDED",
        write_disposition="WRITE_TRUNCATE",
        use_legacy_sql=False,
    )

    # pylint: disable=pointless-statement
    (
        create_dataproc_cluster
        >> run_dataproc_spark
        >> delete_dataproc_cluster
        >> gcs_to_bigquery
        >> explore_visits_by_hour
    )
