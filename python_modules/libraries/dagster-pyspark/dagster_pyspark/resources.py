from dagster import check, resource
from dagster_spark.configs_spark import spark_config
from dagster_spark.utils import flatten_dict
from pyspark.sql import SparkSession


def spark_session_from_config(spark_conf=None):
    spark_conf = check.opt_dict_param(spark_conf, "spark_conf")
    builder = SparkSession.builder
    flat = flatten_dict(spark_conf)
    for key, value in flat:
        builder = builder.config(key, value)

    return builder.getOrCreate()


class PySparkResource:
    def __init__(self, spark_conf):
        self._spark_session = spark_session_from_config(spark_conf)

    @property
    def spark_session(self):
        return self._spark_session

    @property
    def spark_context(self):
        return self.spark_session.sparkContext


@resource({"spark_conf": spark_config()})
def pyspark_resource(init_context):
    """This resource provides access to a PySpark SparkSession for executing PySpark code within
    Dagster.

    Example:

        .. code-block:: python

            @solid(required_resource_keys={"pyspark"})
            def my_solid(context):
                spark_session = context.pyspark.spark_session
                dataframe = spark_session.read.json("examples/src/main/resources/people.json")

            my_pyspark_resource = pyspark_resource.configured(
                {"spark_conf": {"spark.executor.memory": "2g"}}
            )

            @pipeline(mode_defs=[ModeDefinition(resource_defs={"pyspark"})])
            def my_pipeline():
                my_solid()
    """
    return PySparkResource(init_context.resource_config["spark_conf"])
