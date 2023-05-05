import os

import pytest
import requests
from pyspark.sql import SparkSession

BIGQUERY_JARS = "com.google.cloud.spark:spark-bigquery-with-dependencies_2.12:0.28.0"


@pytest.fixture(scope="module")
def gcs_jar_path(tmp_path_factory):
    # the shaded gcs connector jar is required to avoid dependency conflicts with the bigquery connector jar
    # however, the shaded jar cannot be automatically downloaded from the maven central repository when setting up
    # the spark session. So we download the jar ourselves
    jar_name = "gcs-connector-hadoop2-2.2.11-shaded.jar"
    jar_path = f"https://repo1.maven.org/maven2/com/google/cloud/bigdataoss/gcs-connector/hadoop2-2.2.11/{jar_name}"
    r = requests.get(jar_path)
    local_path = os.path.join(tmp_path_factory.mktemp("jars"), jar_name)
    with open(local_path, "wb+") as f:
        f.write(r.content)

    return local_path


@pytest.fixture(scope="module")
def spark(gcs_jar_path):
    spark = (
        SparkSession.builder.config(
            key="spark.jars.packages",
            value=BIGQUERY_JARS,
        )
        .config(key="spark.jars", value=gcs_jar_path)
        .getOrCreate()
    )

    # required config for the gcs connector
    spark._jsc.hadoopConfiguration().set(  # noqa: SLF001
        "fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem"
    )
    spark._jsc.hadoopConfiguration().set(  # noqa: SLF001
        "fs.gs.auth.service.account.enable", "true"
    )
    spark._jsc.hadoopConfiguration().set(  # noqa: SLF001
        "google.cloud.auth.service.account.json.keyfile",
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
    )

    return spark
