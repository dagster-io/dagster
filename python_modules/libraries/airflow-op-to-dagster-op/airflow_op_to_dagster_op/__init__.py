from dagster.core.utils import check_dagster_package_version

from .version import __version__
from .operator_to_op import operator_to_op

check_dagster_package_version("airflow-op-to-dagster-op", __version__)

__all__ = [
    "operator_to_op",
]
