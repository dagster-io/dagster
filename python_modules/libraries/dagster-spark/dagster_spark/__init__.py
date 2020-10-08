from dagster.core.utils import check_dagster_package_version

from .configs import define_spark_config
from .resources import spark_resource
from .solids import create_spark_solid
from .types import SparkSolidError
from .utils import construct_spark_shell_command
from .version import __version__

check_dagster_package_version("dagster-spark", __version__)

__all__ = [
    "construct_spark_shell_command",
    "create_spark_solid",
    "define_spark_config",
    "spark_resource",
    "SparkSolidError",
]
