from dagster.core.utils import check_dagster_package_version

from .configs import define_spark_config
from .ops import create_spark_op, create_spark_solid
from .resources import spark_resource
from .types import SparkOpError, SparkSolidError
from .utils import construct_spark_shell_command
from .version import __version__

check_dagster_package_version("dagster-spark", __version__)

__all__ = [
    "construct_spark_shell_command",
    "create_spark_solid",
    "define_spark_config",
    "spark_resource",
    "SparkOpError",
]
