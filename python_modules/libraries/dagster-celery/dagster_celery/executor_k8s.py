from dagster import Executor, Field, Noneable, StringSource, check, executor
from dagster.core.definitions.executor import check_cross_process_constraints
from dagster.core.execution.retries import Retries
from dagster.core.host_representation.handle import IN_PROCESS_NAME
from dagster.utils import merge_dicts

from .config import DEFAULT_CONFIG, dict_wrapper
from .defaults import broker_url, result_backend
from .executor import CELERY_CONFIG

CELERY_K8S_CONFIG_KEY = 'celery-k8s'


def celery_k8s_config():
    from dagster_k8s import DagsterK8sJobConfig

    # DagsterK8sJobConfig provides config schema for specifying Dagster K8s Jobs
    job_config = DagsterK8sJobConfig.config_type_pipeline_run()

    additional_config = {
        'load_incluster_config': Field(
            bool,
            is_required=False,
            default_value=True,
            description='''Set this value if you are running the launcher within a k8s cluster. If
            ``True``, we assume the launcher is running within the target cluster and load config
            using ``kubernetes.config.load_incluster_config``. Otherwise, we will use the k8s config
            specified in ``kubeconfig_file`` (using ``kubernetes.config.load_kube_config``) or fall
            back to the default kubeconfig. Default: ``True``.''',
        ),
        'kubeconfig_file': Field(
            Noneable(str),
            is_required=False,
            description='Path to a kubeconfig file to use, if not using default kubeconfig.',
        ),
        'job_namespace': Field(
            StringSource,
            is_required=False,
            default_value='default',
            description='The namespace into which to launch new jobs. Note that any '
            'other Kubernetes resources the Job requires (such as the service account) must be '
            'present in this namespace. Default: ``"default"``',
        ),
        'repo_location_name': Field(
            StringSource,
            is_required=False,
            default_value=IN_PROCESS_NAME,
            description='The repository location name to use for execution.',
        ),
    }

    cfg = merge_dicts(CELERY_CONFIG, job_config)
    cfg = merge_dicts(cfg, additional_config)
    return cfg


@executor(name=CELERY_K8S_CONFIG_KEY, config_schema=celery_k8s_config())
def celery_k8s_job_executor(init_context):
    '''Celery-based executor which launches tasks as Kubernetes Jobs.

    The Celery executor exposes config settings for the underlying Celery app under
    the ``config_source`` key. This config corresponds to the "new lowercase settings" introduced
    in Celery version 4.0 and the object constructed from config will be passed to the
    :py:class:`celery.Celery` constructor as its ``config_source`` argument.
    (See https://docs.celeryproject.org/en/latest/userguide/configuration.html for details.)

    The executor also exposes the ``broker``, `backend`, and ``include`` arguments to the
    :py:class:`celery.Celery` constructor.

    In the most common case, you may want to modify the ``broker`` and ``backend`` (e.g., to use
    Redis instead of RabbitMQ). We expect that ``config_source`` will be less frequently
    modified, but that when solid executions are especially fast or slow, or when there are
    different requirements around idempotence or retry, it may make sense to execute pipelines
    with variations on these settings.

    If you'd like to configure a Celery Kubernetes Job executor in addition to the
    :py:class:`~dagster.default_executors`, you should add it to the ``executor_defs`` defined on a
    :py:class:`~dagster.ModeDefinition` as follows:

    .. code-block:: python

        from dagster import ModeDefinition, default_executors, pipeline
        from dagster_celery.executor_k8s import celery_k8s_job_executor

        @pipeline(mode_defs=[
            ModeDefinition(executor_defs=default_executors + [celery_k8s_job_executor])
        ])
        def celery_enabled_pipeline():
            pass

    Then you can configure the executor as follows:

    .. code-block:: YAML

        execution:
          celery-k8s:
            config:
              job_image: 'my_repo.com/image_name:latest'
              job_namespace: 'some-namespace'
              broker: 'pyamqp://guest@localhost//'  # Optional[str]: The URL of the Celery broker
              backend: 'rpc://' # Optional[str]: The URL of the Celery results backend
              include: ['my_module'] # Optional[List[str]]: Modules every worker should import
              config_source: # Dict[str, Any]: Any additional parameters to pass to the
                  #...       # Celery workers. This dict will be passed as the `config_source`
                  #...       # argument of celery.Celery().

    Note that the YAML you provide here must align with the configuration with which the Celery
    workers on which you hope to run were started. If, for example, you point the executor at a
    different broker than the one your workers are listening to, the workers will never be able to
    pick up tasks for execution.
    '''
    from dagster_k8s import DagsterK8sJobConfig, CeleryK8sRunLauncher

    check_cross_process_constraints(init_context)

    run_launcher = init_context.instance.run_launcher
    exc_cfg = init_context.executor_config

    check.inst(
        run_launcher,
        CeleryK8sRunLauncher,
        'This engine is only compatible with a CeleryK8sRunLauncher; configure the '
        'CeleryK8sRunLauncher on your instance to use it.',
    )

    job_config = DagsterK8sJobConfig(
        dagster_home=run_launcher.dagster_home,
        instance_config_map=run_launcher.instance_config_map,
        postgres_password_secret=run_launcher.postgres_password_secret,
        job_image=exc_cfg.get('job_image'),
        image_pull_policy=exc_cfg.get('image_pull_policy'),
        image_pull_secrets=exc_cfg.get('image_pull_secrets'),
        service_account_name=exc_cfg.get('service_account_name'),
        env_config_maps=exc_cfg.get('env_config_maps'),
        env_secrets=exc_cfg.get('env_secrets'),
    )

    # Set on the instance but overrideable here
    broker = run_launcher.broker or exc_cfg.get('broker')
    backend = run_launcher.backend or exc_cfg.get('backend')
    config_source = run_launcher.config_source or exc_cfg.get('config_source')
    include = run_launcher.include or exc_cfg.get('include')
    retries = run_launcher.retries or Retries.from_config(exc_cfg.get('retries'))

    return CeleryK8sJobExecutor(
        broker=broker,
        backend=backend,
        config_source=config_source,
        include=include,
        retries=retries,
        job_config=job_config,
        job_namespace=exc_cfg.get('job_namespace'),
        load_incluster_config=exc_cfg.get('load_incluster_config'),
        kubeconfig_file=exc_cfg.get('kubeconfig_file'),
        repo_location_name=exc_cfg.get('repo_location_name'),
    )


class CeleryK8sJobExecutor(Executor):
    def __init__(
        self,
        retries,
        broker=None,
        backend=None,
        include=None,
        config_source=None,
        job_config=None,
        job_namespace=None,
        load_incluster_config=False,
        kubeconfig_file=None,
        repo_location_name=None,
    ):
        from dagster_k8s import DagsterK8sJobConfig

        if load_incluster_config:
            check.invariant(
                kubeconfig_file is None,
                '`kubeconfig_file` is set but `load_incluster_config` is True.',
            )
        else:
            check.opt_str_param(kubeconfig_file, 'kubeconfig_file')

        self.retries = check.inst_param(retries, 'retries', Retries)
        self.broker = check.opt_str_param(broker, 'broker', default=broker_url)
        self.backend = check.opt_str_param(backend, 'backend', default=result_backend)
        self.include = check.opt_list_param(include, 'include', of_type=str)
        self.config_source = dict_wrapper(
            dict(DEFAULT_CONFIG, **check.opt_dict_param(config_source, 'config_source'))
        )
        self.job_config = check.inst_param(job_config, 'job_config', DagsterK8sJobConfig)
        self.job_namespace = check.opt_str_param(job_namespace, 'job_namespace', default='default')

        self.load_incluster_config = check.bool_param(
            load_incluster_config, 'load_incluster_config'
        )

        self.kubeconfig_file = check.opt_str_param(kubeconfig_file, 'kubeconfig_file')
        self.repo_location_name = check.str_param(repo_location_name, 'repo_location_name')

    def execute(self, pipeline_context, execution_plan):
        from .core_execution_loop import core_celery_execution_loop

        return core_celery_execution_loop(
            pipeline_context, execution_plan, step_execution_fn=_submit_task_k8s_job
        )

    def app_args(self):
        return {
            'broker': self.broker,
            'backend': self.backend,
            'include': self.include,
            'config_source': self.config_source,
            'retries': self.retries,
        }


def _submit_task_k8s_job(app, pipeline_context, step, queue, priority):
    from .tasks import create_k8s_job_task

    from dagster_k8s.job import get_k8s_resource_requirements

    resources = get_k8s_resource_requirements(step.tags)
    task = create_k8s_job_task(app)

    recon_repo = pipeline_context.pipeline.get_reconstructable_repository()

    task_signature = task.si(
        instance_ref_dict=pipeline_context.instance.get_ref().to_dict(),
        step_keys=[step.key],
        run_config=pipeline_context.pipeline_run.run_config,
        mode=pipeline_context.pipeline_run.mode,
        repo_name=recon_repo.get_definition().name,
        repo_location_name=pipeline_context.executor.repo_location_name,
        run_id=pipeline_context.pipeline_run.run_id,
        job_config_dict=pipeline_context.executor.job_config.to_dict(),
        job_namespace=pipeline_context.executor.job_namespace,
        resources=resources,
        retries_dict=pipeline_context.executor.retries.for_inner_plan().to_config(),
        load_incluster_config=pipeline_context.executor.load_incluster_config,
        kubeconfig_file=pipeline_context.executor.kubeconfig_file,
    )

    return task_signature.apply_async(
        priority=priority,
        queue=queue,
        routing_key='{queue}.execute_step_k8s_job'.format(queue=queue),
    )
