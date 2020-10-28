# from dagster_aws.emr.configs_spark import spark_config as dagster_aws_spark_config
# from dagster_spark.configs_spark import spark_config as dagster_spark_spark_config

import dagster_aws.emr.configs_spark as aws_configs_spark
import dagster_spark.configs_spark as spark_configs_spark


def test_spark_configs_same_as_in_dagster_spark():
    aws_contents = open(aws_configs_spark.__file__).read()
    spark_contents = open(spark_configs_spark.__file__).read()
    assert aws_contents == spark_contents
