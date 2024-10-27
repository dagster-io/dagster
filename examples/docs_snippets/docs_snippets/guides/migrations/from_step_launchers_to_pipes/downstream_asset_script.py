import boto3
import pyspark
from dagster_pipes import PipesS3MessageWriter, open_dagster_pipes

from my_lib import calculate_metric  # type: ignore


def main():
    with open_dagster_pipes(
        message_writer=PipesS3MessageWriter(client=boto3.client("s3")),
    ) as pipes:
        spark = pyspark.sql.SparkSession.builder.getOrCreate()

        upstream_path = pipes.get_extra("path")

        df = spark.read.parquet(upstream_path)

        my_metric = calculate_metric(df)

        pipes.report_asset_materialization(metadata={"my_metric": my_metric})


if __name__ == "__main__":
    main()
