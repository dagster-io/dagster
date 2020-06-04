def get_celery_engine_config():
    from dagster_celery.executor_k8s import CELERY_K8S_CONFIG_KEY

    return {
        'execution': {
            CELERY_K8S_CONFIG_KEY: {
                'config': {
                    'job_image': {'env': 'DAGSTER_K8S_PIPELINE_RUN_IMAGE'},
                    'job_namespace': {'env': 'DAGSTER_K8S_PIPELINE_RUN_NAMESPACE'},
                    'image_pull_policy': {'env': 'DAGSTER_K8S_PIPELINE_RUN_IMAGE_PULL_POLICY'},
                    'env_config_maps': [{'env': 'DAGSTER_K8S_PIPELINE_RUN_ENV_CONFIGMAP'}],
                }
            }
        }
    }
