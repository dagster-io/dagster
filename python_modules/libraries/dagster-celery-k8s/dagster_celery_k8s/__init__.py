from dagster._core.libraries import DagsterLibraryRegistry

from .executor import celery_k8s_job_executor as celery_k8s_job_executor
from .launcher import CeleryK8sRunLauncher as CeleryK8sRunLauncher
from .version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-celery-k8s", __version__)
