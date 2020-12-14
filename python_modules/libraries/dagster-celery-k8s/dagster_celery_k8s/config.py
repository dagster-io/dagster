from dagster import Field, Noneable, StringSource
from dagster.core.host_representation import IN_PROCESS_NAME
from dagster.utils import merge_dicts
from dagster_celery.executor import CELERY_CONFIG
from dagster_k8s import DagsterK8sJobConfig

CELERY_K8S_CONFIG_KEY = "celery-k8s"


def celery_k8s_config():

    # DagsterK8sJobConfig provides config schema for specifying Dagster K8s Jobs
    job_config = DagsterK8sJobConfig.config_type_pipeline_run()

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
    }

    cfg = merge_dicts(CELERY_CONFIG, job_config)
    cfg = merge_dicts(cfg, additional_config)
    return cfg


def get_celery_engine_config(additional_env_config_maps=None):
    return {
        "execution": {
            CELERY_K8S_CONFIG_KEY: {
                "config": {
                    "job_image": {"env": "DAGSTER_K8S_PIPELINE_RUN_IMAGE"},
                    "job_namespace": {"env": "DAGSTER_K8S_PIPELINE_RUN_NAMESPACE"},
                    "image_pull_policy": {"env": "DAGSTER_K8S_PIPELINE_RUN_IMAGE_PULL_POLICY"},
                    "env_config_maps": (
                        [{"env": "DAGSTER_K8S_PIPELINE_RUN_ENV_CONFIGMAP"},]
                        + (additional_env_config_maps if additional_env_config_maps else [])
                    ),
                }
            }
        }
    }


def get_celery_engine_grpc_config():
    return {
        "execution": {
            CELERY_K8S_CONFIG_KEY: {
                "config": {
                    "job_namespace": {"env": "DAGSTER_K8S_PIPELINE_RUN_NAMESPACE"},
                    "image_pull_policy": {"env": "DAGSTER_K8S_PIPELINE_RUN_IMAGE_PULL_POLICY"},
                    "env_config_maps": [{"env": "DAGSTER_K8S_PIPELINE_RUN_ENV_CONFIGMAP"}],
                }
            }
        }
    }
