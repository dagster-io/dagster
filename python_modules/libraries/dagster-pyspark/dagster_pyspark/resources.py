from typing import Any, Dict

import dagster._check as check
from dagster import ConfigurableResource, IAttachDifferentObjectToOpContext, resource
from dagster._config.validate import validate_config
from dagster._core.errors import DagsterInvalidConfigError
from dagster._utils.cached_method import cached_method
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


class PySparkClient:
    def __init__(self, spark_conf):
        self._spark_session = spark_session_from_config(spark_conf)

    @property
    def spark_session(self):
        return self._spark_session

    @property
    def spark_context(self):
        return self.spark_session.sparkContext


class PySparkResource(ConfigurableResource, IAttachDifferentObjectToOpContext):
    """This resource provides access to a PySpark Session for executing PySpark code within Dagster.

    Example:
        .. code-block:: python

            @op
            def my_op(pyspark: PySparkResource)
                spark_session = pyspark.get_client().spark_session
                dataframe = spark_session.read.json("examples/src/main/resources/people.json")


            @job(
                resource_defs={
                    "pyspark": PySparkResource(
                        spark_config={
                            "spark.executor.memory": "2g"
                        }
                    )
                }
            )
            def my_spark_job():
                my_op()
    """

    spark_config: Dict[str, Any]

    @cached_method
    def get_client(self) -> PySparkClient:
        result = validate_config(spark_config(), self.spark_config)
        if not result.success:
            raise DagsterInvalidConfigError(
                "Error when processing PySpark resource config ",
                result.errors,
                self.spark_config,
            )
        return PySparkClient(self.spark_config)

    def get_object_to_set_on_execution_context(self) -> Any:
        return self.get_client()


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
    return PySparkClient(init_context.resource_config["spark_conf"])


class LazyPySparkClient:
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


class LazyPySparkResource(ConfigurableResource, IAttachDifferentObjectToOpContext):
    """This resource provides access to a lazily-created  PySpark SparkSession for executing PySpark
    code within Dagster, avoiding the creation of a SparkSession object until the .spark_session attribute
    of the resource is accessed. This is helpful for avoiding the creation (and startup penalty) of a SparkSession
    until it is actually needed / accessed by an op or IOManager.

    Example:
        .. code-block:: python

            @op
            def my_op(lazy_pyspark: LazyPySparkResource)
                spark_session = lazy_pyspark.get_client().spark_session
                dataframe = spark_session.read.json("examples/src/main/resources/people.json")

            @job(
                resource_defs={
                    "lazy_pyspark": LazyPySparkResource(
                        spark_config={
                            "spark.executor.memory": "2g"
                        }
                    )
                }
            )
            def my_spark_job():
                my_op()
    """

    spark_config: Dict[str, Any]

    @cached_method
    def get_client(self) -> LazyPySparkClient:
        result = validate_config(spark_config(), self.spark_config)
        if not result.success:
            raise DagsterInvalidConfigError(
                "Error when processing PySpark resource config ",
                result.errors,
                self.spark_config,
            )
        return LazyPySparkClient(self.spark_config)

    def get_object_to_set_on_execution_context(self) -> Any:
        return self.get_client()


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
    return LazyPySparkClient(init_context.resource_config["spark_conf"])
