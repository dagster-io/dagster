import datetime
import os

from dagster.core.definitions.decorators import daily_schedule, schedule

from .repo import optional_outputs


def define_schedules():
    @daily_schedule(
        name='daily_optional_outputs',
        pipeline_name=optional_outputs.name,
        start_date=datetime.datetime(2020, 1, 1),
    )
    def daily_optional_outputs(_date):
        return {}

    @schedule(
        name='frequent_large_pipe',
        pipeline_name='large_pipeline_celery',
        cron_schedule='*/5 * * * *',
        environment_vars={
            key: os.environ.get(key)
            for key in [
                'DAGSTER_PG_PASSWORD',
                'DAGSTER_K8S_CELERY_BROKER',
                'DAGSTER_K8S_CELERY_BACKEND',
                'DAGSTER_K8S_PIPELINE_RUN_IMAGE',
                'DAGSTER_K8S_PIPELINE_RUN_NAMESPACE',
                'DAGSTER_K8S_INSTANCE_CONFIG_MAP',
                'DAGSTER_K8S_PG_PASSWORD_SECRET',
                'DAGSTER_K8S_PIPELINE_RUN_ENV_CONFIGMAP',
                'DAGSTER_K8S_PIPELINE_RUN_IMAGE_PULL_POLICY',
                'KUBERNETES_SERVICE_HOST',
                'KUBERNETES_SERVICE_PORT',
            ]
            if key in os.environ
        },
    )
    def frequent_large_pipe(_):
        from dagster_k8s import get_celery_engine_config

        cfg = get_celery_engine_config()
        cfg['storage'] = {'s3': {'config': {'s3_bucket': 'dagster-scratch-80542c2'}}}
        return cfg

    return {
        'daily_optional_outputs': daily_optional_outputs,
        'frequent_large_pipe': frequent_large_pipe,
    }
