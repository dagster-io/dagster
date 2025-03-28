from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_celery_k8s.executor import celery_k8s_job_executor as celery_k8s_job_executor
from dagster_celery_k8s.launcher import CeleryK8sRunLauncher as CeleryK8sRunLauncher
from dagster_celery_k8s.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-celery-k8s", __version__)
