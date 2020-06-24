from dagster.core.utils import check_dagster_package_version

from .version import __version__

check_dagster_package_version('dagster-celery-k8s', __version__)
