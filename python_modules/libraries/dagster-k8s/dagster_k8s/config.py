from dagster import check


def get_celery_engine_config(config_source=None):
    config_source = check.opt_dict_param(config_source, 'config_source')
    return {
        'execution': {
            'celery': {
                'config': {
                    'broker': {'env': 'DAGSTER_K8S_CELERY_BROKER'},
                    'backend': {'env': 'DAGSTER_K8S_CELERY_BACKEND'},
                    'config_source': config_source,
                }
            }
        }
    }
