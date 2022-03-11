from dagster._core.utils import check_dagster_package_version

from .version import __version__

check_dagster_package_version("dagster-azure", __version__)
