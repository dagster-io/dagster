import abc

import six
from dagster_spark.configs_spark import spark_config
from dagster_spark.utils import flatten_dict
from pyspark.sql import SparkSession

from dagster import Field, check, resource


def spark_session_from_config(spark_conf=None):
    spark_conf = check.opt_dict_param(spark_conf, 'spark_conf')
    builder = SparkSession.builder
    flat = flatten_dict(spark_conf)
    for key, value in flat:
        builder = builder.config(key, value)

    return builder.getOrCreate()


class PySparkResourceDefinition(six.with_metaclass(abc.ABCMeta)):
    def __init__(self, spark_conf):
        self._spark_session = spark_session_from_config(spark_conf)

    @property
    def spark_session(self):
        return self._spark_session

    @property
    def spark_context(self):
        return self.spark_session.sparkContext

    def stop(self):
        self._spark_session.stop()

    @abc.abstractmethod
    def get_compute_fn(self, fn, solid_name):
        pass


class SystemPySparkResource(PySparkResourceDefinition):
    def get_compute_fn(self, fn, solid_name):
        return fn


@resource(
    {
        'spark_conf': spark_config(),
        'stop_session': Field(
            bool,
            is_required=False,
            default_value=True,
            description='Whether to stop the Spark session on pipeline completion. '
            'Defaults to True.',
        ),
    }
)
def pyspark_resource(init_context):
    pyspark = SystemPySparkResource(init_context.resource_config['spark_conf'])
    try:
        yield pyspark
    finally:
        if init_context.resource_config['stop_session']:
            pyspark.stop()
