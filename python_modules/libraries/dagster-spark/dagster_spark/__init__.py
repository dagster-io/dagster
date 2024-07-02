from dagster._core.libraries import DagsterLibraryRegistry

from .ops import create_spark_op as create_spark_op
from .types import SparkOpError as SparkOpError
from .utils import construct_spark_shell_command as construct_spark_shell_command
from .configs import define_spark_config as define_spark_config
from .version import __version__ as __version__
from .resources import spark_resource as spark_resource

DagsterLibraryRegistry.register("dagster-spark", __version__)
