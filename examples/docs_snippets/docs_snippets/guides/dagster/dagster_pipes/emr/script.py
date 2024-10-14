import boto3
from dagster_pipes import PipesS3MessageWriter, open_dagster_pipes
from pyspark.sql import SparkSession


def main():
    with open_dagster_pipes(
        message_writer=PipesS3MessageWriter(client=boto3.client("s3"))
    ) as pipes:
        pipes.log.info("Hello from AWS EMR!")

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

        print("Hello from stdout!")  # noqa: T201


if __name__ == "__main__":
    main()
