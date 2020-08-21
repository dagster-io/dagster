from dagster.core.utils import check_dagster_package_version

from .resources import github_resource
from .version import __version__

check_dagster_package_version("dagster-github", __version__)

__all__ = ["github_resource"]
