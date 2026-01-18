from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_spark.configs import define_spark_config as define_spark_config
from dagster_spark.ops import create_spark_op as create_spark_op
from dagster_spark.resources import spark_resource as spark_resource
from dagster_spark.types import SparkOpError as SparkOpError
from dagster_spark.utils import construct_spark_shell_command as construct_spark_shell_command
from dagster_spark.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-spark", __version__)
