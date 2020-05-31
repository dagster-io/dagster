def get_celery_engine_config():
    return {
        'execution': {
            'celery-k8s': {
                'config': {
                    'job_image': {'env': 'DAGSTER_K8S_PIPELINE_RUN_IMAGE'},
                    'job_namespace': {'env': 'DAGSTER_K8S_PIPELINE_RUN_NAMESPACE'},
                    'image_pull_policy': {'env': 'DAGSTER_K8S_PIPELINE_RUN_IMAGE_PULL_POLICY'},
                    'env_config_maps': [{'env': 'DAGSTER_K8S_PIPELINE_RUN_ENV_CONFIGMAP'}],
                }
            }
        }
    }
