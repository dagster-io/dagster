from dagster.core.utils import check_dagster_package_version

from .dauphin_registry import DauphinRegistry
from .version import __version__

dauphin = DauphinRegistry()
check_dagster_package_version("dagster-graphql", __version__)
