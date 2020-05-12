from dagster.core.utils import check_dagster_package_version

from .config import get_celery_engine_config
from .launcher import K8sRunLauncher
from .version import __version__

check_dagster_package_version('dagster-k8s', __version__)

__all__ = ['K8sRunLauncher']
