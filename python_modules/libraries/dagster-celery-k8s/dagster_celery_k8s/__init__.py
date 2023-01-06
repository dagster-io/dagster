from dagster._core.utils import check_dagster_package_version

from .executor import celery_k8s_job_executor as celery_k8s_job_executor
from .launcher import CeleryK8sRunLauncher as CeleryK8sRunLauncher
from .version import __version__ as __version__

check_dagster_package_version("dagster-celery-k8s", __version__)
