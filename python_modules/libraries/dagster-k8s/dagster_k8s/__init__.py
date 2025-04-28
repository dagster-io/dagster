from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_k8s.executor import k8s_job_executor as k8s_job_executor
from dagster_k8s.job import (
    DagsterK8sJobConfig as DagsterK8sJobConfig,
    K8sConfigMergeBehavior as K8sConfigMergeBehavior,
    construct_dagster_k8s_job as construct_dagster_k8s_job,
)
from dagster_k8s.launcher import K8sRunLauncher as K8sRunLauncher
from dagster_k8s.ops import (
    execute_k8s_job as execute_k8s_job,
    k8s_job_op as k8s_job_op,
)
from dagster_k8s.pipes import (
    PipesK8sClient as PipesK8sClient,
    PipesK8sPodLogsMessageReader as PipesK8sPodLogsMessageReader,
)
from dagster_k8s.version import __version__ as __version__

DagsterLibraryRegistry.register("dagster-k8s", __version__)
