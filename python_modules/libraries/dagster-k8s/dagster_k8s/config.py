from dagster import check


def get_celery_engine_config(config_source=None):
    config_source = check.opt_dict_param(config_source, 'config_source')
    return {
        'execution': {
            'celery-k8s': {
                'config': {
                    'broker': {'env': 'DAGSTER_K8S_CELERY_BROKER'},
                    'backend': {'env': 'DAGSTER_K8S_CELERY_BACKEND'},
                    'config_source': config_source,
                    'job_image': {'env': 'DAGSTER_K8S_PIPELINE_RUN_IMAGE'},
                    'job_namespace': {'env': 'DAGSTER_K8S_PIPELINE_RUN_NAMESPACE'},
                    'instance_config_map': {'env': 'DAGSTER_K8S_INSTANCE_CONFIG_MAP'},
                    'image_pull_policy': 'Always',
                    'postgres_password_secret': {'env': 'DAGSTER_K8S_PG_PASSWORD_SECRET'},
                    'env_config_maps': [{'env': 'DAGSTER_K8S_PIPELINE_RUN_ENV_CONFIGMAP'}],
                }
            }
        }
    }
