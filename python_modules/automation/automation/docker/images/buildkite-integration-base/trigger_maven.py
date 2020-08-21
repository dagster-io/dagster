from pyspark.sql import SparkSession

# This is a brutal hack. When the SparkSession is created for the first time there is a lengthy
# download process from Maven. This allows us to run python -m airline_demo.resources in the
# Dockerfile and avoid a long runtime delay before each containerized solid executes.

# must stay in sync with airline_demo requirements


def spark_session():
    spark = (
        SparkSession.builder.appName("DownloadStuff")
        .config(
            "spark.jars.packages",
            "com.databricks:spark-avro_2.11:3.0.0,"
            "com.databricks:spark-redshift_2.11:2.0.1,"
            "com.databricks:spark-csv_2.11:1.5.0,"
            "org.postgresql:postgresql:42.2.5,"
            "org.apache.hadoop:hadoop-aws:2.6.5,"
            "com.amazonaws:aws-java-sdk:1.7.4",
        )
        .getOrCreate()
    )
    return spark


if __name__ == "__main__":
    spark_session()
