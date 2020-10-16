from dagster.core.utils import check_dagster_package_version

from .pyspark_step_launcher import emr_pyspark_step_launcher
from .version import __version__

check_dagster_package_version("dagster-aws-pyspark", __version__)


__all__ = ["emr_pyspark_step_launcher"]
