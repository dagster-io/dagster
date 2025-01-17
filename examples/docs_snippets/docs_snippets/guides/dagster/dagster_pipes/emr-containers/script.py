import sys

import boto3
from dagster_pipes import PipesS3ContextLoader, PipesS3MessageWriter, open_dagster_pipes
from pyspark.sql import SparkSession


def main():
    s3_client = boto3.client("s3")

    with open_dagster_pipes(
        message_writer=PipesS3MessageWriter(client=s3_client),
        context_loader=PipesS3ContextLoader(client=s3_client),
    ) as pipes:
        pipes.log.info("Hello from AWS EMR Containers!")

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

        print("Hello from stdout!")  # noqa: T201
        print("Hello from stderr!", file=sys.stderr)  # noqa: T201


if __name__ == "__main__":
    main()

# import os
# import sys

# print(os.getcwd())
# print(os.environ)
# print(sys.path)
# print(sys.executable)
