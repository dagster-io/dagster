from collections import namedtuple

from dagster import check
from dagster.core.execution.config import ExecutorConfig
from dagster.core.execution.retries import Retries, RetryMode

from .defaults import (
    broker_transport_options,
    broker_url,
    result_backend,
    task_default_priority,
    task_default_queue,
)

DEFAULT_CONFIG = {
    # 'task_queue_max_priority': 10,
    'worker_prefetch_multiplier': 1,
    'broker_transport_options': broker_transport_options,
    'task_default_priority': task_default_priority,
    'task_default_queue': task_default_queue,
}


class dict_wrapper(object):
    '''Wraps a dict to convert `obj['attr']` to `obj.attr`.'''

    def __init__(self, dictionary):
        self.__dict__ = dictionary


class CeleryConfig(
    namedtuple('CeleryConfig', 'broker backend include config_source retries'), ExecutorConfig,
):
    '''Configuration class for the Celery execution engine.

    Params:
        broker (Optional[str]): The URL of the Celery broker.
        backend (Optional[str]): The URL of the Celery backend.
        include (Optional[List[str]]): List of modules every worker should import.
        config_source (Optional[Dict]): Config settings for the Celery app.
        retries (Retries): Controls retry behavior
    '''

    def __new__(
        cls, retries, broker=None, backend=None, include=None, config_source=None,
    ):

        return super(CeleryConfig, cls).__new__(
            cls,
            broker=check.opt_str_param(broker, 'broker', default=broker_url),
            backend=check.opt_str_param(backend, 'backend', default=result_backend),
            include=check.opt_list_param(include, 'include', of_type=str),
            config_source=dict_wrapper(
                dict(DEFAULT_CONFIG, **check.opt_dict_param(config_source, 'config_source'))
            ),
            retries=check.inst_param(retries, 'retries', Retries),
        )

    @staticmethod
    def for_cli(broker=None, backend=None, include=None, config_source=None):
        return CeleryConfig(
            retries=Retries(RetryMode.DISABLED),
            broker=broker,
            backend=backend,
            include=include,
            config_source=config_source,
        )

    @staticmethod
    def get_engine():
        from .engine import CeleryEngine

        return CeleryEngine()

    def app_args(self):
        return self._asdict()


class CeleryK8sJobConfig(
    namedtuple(
        'CeleryK8sJobConfig',
        'retries broker backend include config_source job_config job_namespace '
        'load_incluster_config kubeconfig_file',
    ),
    ExecutorConfig,
):
    '''Configuration class for the Celery execution engine.

    Params:
        retries (Retries): Controls retry behavior
        broker (Optional[str]): The URL of the Celery broker.
        backend (Optional[str]): The URL of the Celery backend.
        include (Optional[List[str]]): List of modules every worker should import.
        config_source (Optional[Dict]): Config settings for the Celery app.
        job_config (DagsterK8sJobConfig): Configuration for Kubernetes Job task execution.
        job_namespace (Optional[str]): The namespace into which to launch new jobs. Note that any
            other Kubernetes resources the Job requires (such as the service account) must be
            present in this namespace. Default: ``"default"``
        load_incluster_config (Optional[bool]):  Set this value if you are running the launcher
            within a k8s cluster. If ``True``, we assume the launcher is running within the target
            cluster and load config using ``kubernetes.config.load_incluster_config``. Otherwise,
            we will use the k8s config specified in ``kubeconfig_file`` (using
            ``kubernetes.config.load_kube_config``) or fall back to the default kubeconfig. Default:
            ``False``.
        kubeconfig_file (str): Path to a kubeconfig file to use. Unused when the coordinating
            process is within the cluster. Defaults to None (using the default kubeconfig).
    '''

    def __new__(
        cls,
        retries,
        broker=None,
        backend=None,
        include=None,
        config_source=None,
        job_config=None,
        job_namespace=None,
        load_incluster_config=False,
        kubeconfig_file=None,
    ):
        from dagster_k8s.job import DagsterK8sJobConfig

        if load_incluster_config:
            check.invariant(
                kubeconfig_file is None,
                '`kubeconfig_file` is set but `load_incluster_config` is True.',
            )
        else:
            check.opt_str_param(kubeconfig_file, 'kubeconfig_file')

        return super(CeleryK8sJobConfig, cls).__new__(
            cls,
            retries=check.inst_param(retries, 'retries', Retries),
            broker=check.opt_str_param(broker, 'broker', default=broker_url),
            backend=check.opt_str_param(backend, 'backend', default=result_backend),
            include=check.opt_list_param(include, 'include', of_type=str),
            config_source=dict_wrapper(
                dict(DEFAULT_CONFIG, **check.opt_dict_param(config_source, 'config_source'))
            ),
            job_config=check.inst_param(job_config, 'job_config', DagsterK8sJobConfig),
            job_namespace=check.opt_str_param(job_namespace, 'job_namespace', default='default'),
            load_incluster_config=check.bool_param(load_incluster_config, 'load_incluster_config'),
            kubeconfig_file=check.opt_str_param(kubeconfig_file, 'kubeconfig_file'),
        )

    @staticmethod
    def get_engine():
        from .engine import CeleryK8sJobEngine

        return CeleryK8sJobEngine()

    def app_args(self):
        '''Only include celery app arguments, skip k8s config
        '''
        from .executor import CELERY_CONFIG

        asdict = self._asdict()

        return {key: asdict[key] for key in CELERY_CONFIG.keys()}
