from dagster_celery.executor import CELERY_CONFIG
from dagster_k8s import DagsterK8sJobConfig
from dagster_k8s.client import DEFAULT_WAIT_TIMEOUT

from dagster import Field, Float, Noneable, StringSource
from dagster._core.host_representation import IN_PROCESS_NAME
from dagster._utils import merge_dicts

CELERY_K8S_CONFIG_KEY = "celery-k8s"


def celery_k8s_executor_config():

    # DagsterK8sJobConfig provides config schema for specifying Dagster K8s Jobs
    job_config = DagsterK8sJobConfig.config_type_job()

    additional_config = {
        "load_incluster_config": Field(
            bool,
            is_required=False,
            default_value=True,
            description="""Set this value if you are running the launcher within a k8s cluster. If
            ``True``, we assume the launcher is running within the target cluster and load config
            using ``kubernetes.config.load_incluster_config``. Otherwise, we will use the k8s config
            specified in ``kubeconfig_file`` (using ``kubernetes.config.load_kube_config``) or fall
            back to the default kubeconfig. Default: ``True``.""",
        ),
        "kubeconfig_file": Field(
            Noneable(str),
            is_required=False,
            description="Path to a kubeconfig file to use, if not using default kubeconfig.",
        ),
        "job_namespace": Field(
            StringSource,
            is_required=False,
            default_value="default",
            description="The namespace into which to launch new jobs. Note that any "
            "other Kubernetes resources the Job requires (such as the service account) must be "
            'present in this namespace. Default: ``"default"``',
        ),
        "repo_location_name": Field(
            StringSource,
            is_required=False,
            default_value=IN_PROCESS_NAME,
            description="The repository location name to use for execution.",
        ),
        "job_wait_timeout": Field(
            Float,
            is_required=False,
            default_value=DEFAULT_WAIT_TIMEOUT,
            description=f"Wait this many seconds for a job to complete before marking the run as failed. Defaults to {DEFAULT_WAIT_TIMEOUT} seconds.",
        ),
    }

    cfg = merge_dicts(CELERY_CONFIG, job_config)
    cfg = merge_dicts(cfg, additional_config)
    return cfg


def get_celery_engine_config(image_pull_policy=None, additional_env_config_maps=None):
    job_config = get_celery_engine_job_config(image_pull_policy, additional_env_config_maps)
    return {"execution": {CELERY_K8S_CONFIG_KEY: {"config": job_config["execution"]["config"]}}}


def get_celery_engine_job_config(image_pull_policy=None, additional_env_config_maps=None):
    return {
        "execution": {
            "config": merge_dicts(
                {
                    "job_namespace": {"env": "DAGSTER_K8S_PIPELINE_RUN_NAMESPACE"},
                    "env_config_maps": (
                        [
                            {"env": "DAGSTER_K8S_PIPELINE_RUN_ENV_CONFIGMAP"},
                        ]
                        + (additional_env_config_maps if additional_env_config_maps else [])
                    ),
                },
                (
                    {
                        "image_pull_policy": image_pull_policy,
                    }
                    if image_pull_policy
                    else {}
                ),
            )
        }
    }
