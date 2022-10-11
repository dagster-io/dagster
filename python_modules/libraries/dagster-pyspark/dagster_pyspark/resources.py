from dagster_spark.configs_spark import spark_config
from dagster_spark.utils import flatten_dict
from pyspark.sql import SparkSession

import dagster._check as check
from dagster import resource


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
    """This resource provides access to a PySpark SparkSession for executing PySpark code within Dagster.

    Example:

    .. code-block:: python

        @op(required_resource_keys={"pyspark"})
        def my_op(context):
            spark_session = context.resources.pyspark.spark_session
            dataframe = spark_session.read.json("examples/src/main/resources/people.json")

        my_pyspark_resource = pyspark_resource.configured(
            {"spark_conf": {"spark.executor.memory": "2g"}}
        )

        @job(resource_defs={"pyspark": my_pyspark_resource})
        def my_spark_job():
            my_op()

    """
    return PySparkResource(init_context.resource_config["spark_conf"])


class LazyPySparkResource:
    def __init__(self, spark_conf):
        self._spark_session = None
        self._spark_conf = spark_conf

    def _init_session(self):
        if self._spark_session is None:
            self._spark_session = spark_session_from_config(self._spark_conf)

    @property
    def spark_session(self):
        self._init_session()
        return self._spark_session

    @property
    def spark_context(self):
        self._init_session()
        return self._spark_session.sparkContext


@resource({"spark_conf": spark_config()})
def lazy_pyspark_resource(init_context):
    """This resource provides access to a lazily-created  PySpark SparkSession for executing PySpark
    code within Dagster, avoiding the creation of a SparkSession object until the .spark_session attribute
    of the resource is accessed. This is helpful for avoiding the creation (and startup penalty) of a SparkSession
    until it is actually needed / accessed by an op or IOManager.

    Example:

    .. code-block:: python

        @op(required_resource_keys={"lazy_pyspark"})
        def my_op(context):
            spark_session = context.resources.lazy_pyspark.spark_session
            dataframe = spark_session.read.json("examples/src/main/resources/people.json")

        my_pyspark_resource = lazy_pyspark_resource.configured(
            {"spark_conf": {"spark.executor.memory": "2g"}}
        )

        @job(resource_defs={"lazy_pyspark": my_pyspark_resource})
        def my_spark_job():
            my_op()

    """
    return LazyPySparkResource(init_context.resource_config["spark_conf"])
