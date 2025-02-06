from dagster_pipes import (
    PipesCliArgsParamsLoader,
    PipesGCSContextLoader,
    PipesGCSMessageWriter,
    open_dagster_pipes,
)
from google.cloud.storage import Client as GCSClient
from pyspark.sql import SparkSession


def main():
    gcs_client = GCSClient()
    with open_dagster_pipes(
        context_loader=PipesGCSContextLoader(client=gcs_client),
        message_writer=PipesGCSMessageWriter(client=gcs_client),
        params_loader=PipesCliArgsParamsLoader(),
    ) as pipes:
        pipes.log.info("Hello from GCP Dataproc!")

        print("Hello from GCP Dataproc Spark driver stdout!")  # noqa: T201

        spark = SparkSession.builder.appName("HelloWorld").getOrCreate()

        df = spark.createDataFrame(
            [(1, "Alice", 34), (2, "Bob", 45), (3, "Charlie", 56)],
            ["id", "name", "age"],
        )

        # calculate a really important statistic
        avg_age = float(df.agg({"age": "avg"}).collect()[0][0])

        # attach it to the asset materialization in Dagster
        pipes.report_asset_materialization(
            metadata={"average_age": {"raw_value": avg_age, "type": "float"}},
            data_version="alpha",
        )

        spark.stop()


if __name__ == "__main__":
    main()
