import logging
import os
import sys
import time

import kubernetes
from dagster import (
    DagsterEvent,
    DagsterEventType,
    DagsterInstance,
    Executor,
    _check as check,
    executor,
    multiple_process_executor_requirements,
)
from dagster._cli.api import ExecuteStepArgs
from dagster._core.errors import DagsterUnmetExecutorRequirementsError
from dagster._core.events import EngineEventData
from dagster._core.events.log import EventLogEntry
from dagster._core.events.utils import filter_dagster_events_from_cli_logs
from dagster._core.execution.plan.objects import StepFailureData, UserFailureData
from dagster._core.execution.retries import RetryMode
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._serdes import pack_value, serialize_value, unpack_value
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster_celery.config import DEFAULT_CONFIG, dict_wrapper
from dagster_celery.core_execution_loop import DELEGATE_MARKER
from dagster_celery.defaults import broker_url, result_backend
from dagster_k8s import DagsterK8sJobConfig, construct_dagster_k8s_job
from dagster_k8s.client import (
    DagsterK8sAPIRetryLimitExceeded,
    DagsterK8sError,
    DagsterK8sJobStatusException,
    DagsterK8sTimeoutError,
    DagsterK8sUnrecoverableAPIError,
    DagsterKubernetesClient,
)
from dagster_k8s.job import (
    UserDefinedDagsterK8sConfig,
    get_k8s_job_name,
    get_user_defined_k8s_config,
)

from .config import CELERY_K8S_CONFIG_KEY, celery_k8s_executor_config
from .launcher import CeleryK8sRunLauncher


@executor(
    name=CELERY_K8S_CONFIG_KEY,
    config_schema=celery_k8s_executor_config(),
    requirements=multiple_process_executor_requirements(),
)
def celery_k8s_job_executor(init_context):
    """Celery-based executor which launches tasks as Kubernetes Jobs.

    The Celery executor exposes config settings for the underlying Celery app under
    the ``config_source`` key. This config corresponds to the "new lowercase settings" introduced
    in Celery version 4.0 and the object constructed from config will be passed to the
    :py:class:`celery.Celery` constructor as its ``config_source`` argument.
    (See https://docs.celeryq.dev/en/stable/userguide/configuration.html for details.)

    The executor also exposes the ``broker``, `backend`, and ``include`` arguments to the
    :py:class:`celery.Celery` constructor.

    In the most common case, you may want to modify the ``broker`` and ``backend`` (e.g., to use
    Redis instead of RabbitMQ). We expect that ``config_source`` will be less frequently
    modified, but that when op executions are especially fast or slow, or when there are
    different requirements around idempotence or retry, it may make sense to execute dagster jobs
    with variations on these settings.

    To use the `celery_k8s_job_executor`, set it as the `executor_def` when defining a job:

    .. literalinclude:: ../../../../../../python_modules/libraries/dagster-celery-k8s/dagster_celery_k8s_tests/example_celery_mode_def.py
       :language: python

    Then you can configure the executor as follows:

    .. code-block:: YAML

        execution:
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

    In deployments where the celery_k8s_job_executor is used all appropriate celery and dagster_celery
    commands must be invoked with the `-A dagster_celery_k8s.app` argument.
    """
    run_launcher = init_context.instance.run_launcher
    exc_cfg = init_context.executor_config

    if not isinstance(run_launcher, CeleryK8sRunLauncher):
        raise DagsterUnmetExecutorRequirementsError(
            "This engine is only compatible with a CeleryK8sRunLauncher; configure the "
            "CeleryK8sRunLauncher on your instance to use it.",
        )

    job_config = run_launcher.get_k8s_job_config(
        job_image=exc_cfg.get("job_image") or os.getenv("DAGSTER_CURRENT_IMAGE"), exc_config=exc_cfg
    )

    # Set on the instance but overrideable here
    broker = run_launcher.broker or exc_cfg.get("broker")
    backend = run_launcher.backend or exc_cfg.get("backend")
    config_source = run_launcher.config_source or exc_cfg.get("config_source")
    include = run_launcher.include or exc_cfg.get("include")
    retries = run_launcher.retries or RetryMode.from_config(exc_cfg.get("retries"))

    return CeleryK8sJobExecutor(
        broker=broker,
        backend=backend,
        config_source=config_source,
        include=include,
        retries=retries,
        job_config=job_config,
        job_namespace=exc_cfg.get("job_namespace", run_launcher.job_namespace),
        load_incluster_config=exc_cfg.get("load_incluster_config"),
        kubeconfig_file=exc_cfg.get("kubeconfig_file"),
        repo_location_name=exc_cfg.get("repo_location_name"),
        job_wait_timeout=exc_cfg.get("job_wait_timeout"),
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
        job_wait_timeout=None,
    ):
        if load_incluster_config:
            check.invariant(
                kubeconfig_file is None,
                "`kubeconfig_file` is set but `load_incluster_config` is True.",
            )
        else:
            check.opt_str_param(kubeconfig_file, "kubeconfig_file")

        self._retries = check.inst_param(retries, "retries", RetryMode)
        self.broker = check.opt_str_param(broker, "broker", default=broker_url)
        self.backend = check.opt_str_param(backend, "backend", default=result_backend)
        self.include = check.opt_list_param(include, "include", of_type=str)
        self.config_source = dict_wrapper(
            dict(DEFAULT_CONFIG, **check.opt_dict_param(config_source, "config_source"))
        )
        self.job_config = check.inst_param(job_config, "job_config", DagsterK8sJobConfig)
        self.job_namespace = check.opt_str_param(job_namespace, "job_namespace")

        self.load_incluster_config = check.bool_param(
            load_incluster_config, "load_incluster_config"
        )

        self.kubeconfig_file = check.opt_str_param(kubeconfig_file, "kubeconfig_file")
        self.repo_location_name = check.opt_str_param(repo_location_name, "repo_location_name")
        self.job_wait_timeout = check.float_param(job_wait_timeout, "job_wait_timeout")

    @property
    def retries(self):
        return self._retries

    def execute(self, plan_context, execution_plan):
        from dagster_celery.core_execution_loop import core_celery_execution_loop

        return core_celery_execution_loop(
            plan_context, execution_plan, step_execution_fn=_submit_task_k8s_job
        )

    def app_args(self):
        return {
            "broker": self.broker,
            "backend": self.backend,
            "include": self.include,
            "config_source": self.config_source,
            "retries": self.retries,
        }


def _submit_task_k8s_job(app, plan_context, step, queue, priority, known_state):
    user_defined_k8s_config = get_user_defined_k8s_config(step.tags)

    job_origin = plan_context.reconstructable_job.get_python_origin()

    execute_step_args = ExecuteStepArgs(
        job_origin=job_origin,
        run_id=plan_context.dagster_run.run_id,
        step_keys_to_execute=[step.key],
        instance_ref=plan_context.instance.get_ref(),
        retry_mode=plan_context.executor.retries.for_inner_plan(),
        known_state=known_state,
        should_verify_step=True,
        print_serialized_events=True,
    )

    job_config = plan_context.executor.job_config
    if not job_config.job_image:
        job_config = job_config.with_image(job_origin.repository_origin.container_image)

    if not job_config.job_image:
        raise Exception("No image included in either executor config or the dagster job")

    task = create_k8s_job_task(app)
    task_signature = task.si(
        execute_step_args_packed=pack_value(execute_step_args),
        job_config_dict=job_config.to_dict(),
        job_namespace=plan_context.executor.job_namespace,
        user_defined_k8s_config_dict=user_defined_k8s_config.to_dict(),
        load_incluster_config=plan_context.executor.load_incluster_config,
        job_wait_timeout=plan_context.executor.job_wait_timeout,
        kubeconfig_file=plan_context.executor.kubeconfig_file,
    )

    return task_signature.apply_async(
        priority=priority,
        queue=queue,
        routing_key=f"{queue}.execute_step_k8s_job",
    )


def construct_step_failure_event_and_handle(dagster_run, step_key, err, instance):
    step_failure_event = DagsterEvent(
        event_type_value=DagsterEventType.STEP_FAILURE.value,
        job_name=dagster_run.job_name,
        step_key=step_key,
        event_specific_data=StepFailureData(
            error=serializable_error_info_from_exc_info(sys.exc_info()),
            user_failure_data=UserFailureData(label="K8sError"),
        ),
    )
    event_record = EventLogEntry(
        user_message=str(err),
        level=logging.ERROR,
        job_name=dagster_run.job_name,
        run_id=dagster_run.run_id,
        error_info=None,
        step_key=step_key,
        timestamp=time.time(),
        dagster_event=step_failure_event,
    )
    instance.handle_new_event(event_record)
    return step_failure_event


def create_k8s_job_task(celery_app, **task_kwargs):
    @celery_app.task(bind=True, name="execute_step_k8s_job", **task_kwargs)
    def _execute_step_k8s_job(
        self,
        execute_step_args_packed,
        job_config_dict,
        job_namespace,
        load_incluster_config,
        job_wait_timeout,
        user_defined_k8s_config_dict=None,
        kubeconfig_file=None,
    ):
        """Run step execution in a K8s job pod."""
        execute_step_args = unpack_value(
            check.dict_param(
                execute_step_args_packed,
                "execute_step_args_packed",
            )
        )
        check.inst_param(execute_step_args, "execute_step_args", ExecuteStepArgs)
        check.invariant(
            len(execute_step_args.step_keys_to_execute) == 1,
            "Celery K8s task executor can only execute 1 step at a time",
        )

        # Celery will serialize this as a list
        job_config = DagsterK8sJobConfig.from_dict(job_config_dict)
        check.inst_param(job_config, "job_config", DagsterK8sJobConfig)
        check.str_param(job_namespace, "job_namespace")

        check.bool_param(load_incluster_config, "load_incluster_config")

        user_defined_k8s_config = UserDefinedDagsterK8sConfig.from_dict(
            user_defined_k8s_config_dict
        )
        check.opt_inst_param(
            user_defined_k8s_config,
            "user_defined_k8s_config",
            UserDefinedDagsterK8sConfig,
        )
        check.opt_str_param(kubeconfig_file, "kubeconfig_file")

        # For when launched via DinD or running the cluster
        if load_incluster_config:
            kubernetes.config.load_incluster_config()
        else:
            kubernetes.config.load_kube_config(kubeconfig_file)

        api_client = DagsterKubernetesClient.production_client()
        instance = DagsterInstance.from_ref(execute_step_args.instance_ref)
        dagster_run = instance.get_run_by_id(execute_step_args.run_id)

        check.inst(
            dagster_run,
            DagsterRun,
            f"Could not load run {execute_step_args.run_id}",
        )
        step_key = execute_step_args.step_keys_to_execute[0]

        celery_worker_name = self.request.hostname
        celery_pod_name = os.environ.get("HOSTNAME")
        instance.report_engine_event(
            f"Task for step {step_key} picked up by Celery",
            dagster_run,
            EngineEventData(
                {
                    "Celery worker name": celery_worker_name,
                    "Celery worker Kubernetes Pod name": celery_pod_name,
                }
            ),
            CeleryK8sJobExecutor,
            step_key=step_key,
        )

        if dagster_run.status != DagsterRunStatus.STARTED:
            instance.report_engine_event(
                "Not scheduling step because dagster run status is not STARTED",
                dagster_run,
                EngineEventData(
                    {
                        "Step key": step_key,
                    }
                ),
                CeleryK8sJobExecutor,
                step_key=step_key,
            )
            return []

        # Ensure we stay below k8s name length limits
        k8s_name_key = get_k8s_job_name(execute_step_args.run_id, step_key)

        retry_state = execute_step_args.known_state.get_retry_state()

        if retry_state.get_attempt_count(step_key):
            attempt_number = retry_state.get_attempt_count(step_key)
            job_name = "dagster-step-%s-%d" % (k8s_name_key, attempt_number)
            pod_name = "dagster-step-%s-%d" % (k8s_name_key, attempt_number)
        else:
            job_name = "dagster-step-%s" % (k8s_name_key)
            pod_name = "dagster-step-%s" % (k8s_name_key)

        args = execute_step_args.get_command_args()

        labels = {
            "dagster/job": dagster_run.job_name,
            "dagster/op": step_key,
            "dagster/run-id": execute_step_args.run_id,
        }
        if dagster_run.external_job_origin:
            labels["dagster/code-location"] = (
                dagster_run.external_job_origin.external_repository_origin.code_location_origin.location_name
            )
        job = construct_dagster_k8s_job(
            job_config,
            args,
            job_name,
            user_defined_k8s_config,
            pod_name,
            component="step_worker",
            labels=labels,
            env_vars=[
                {
                    "name": "DAGSTER_RUN_JOB_NAME",
                    "value": dagster_run.job_name,
                },
                {"name": "DAGSTER_RUN_STEP_KEY", "value": step_key},
            ],
        )

        # Running list of events generated from this task execution
        events = []

        # Post event for starting execution
        job_name = job.metadata.name
        engine_event = instance.report_engine_event(
            f'Executing step "{step_key}" in Kubernetes job {job_name}.',
            dagster_run,
            EngineEventData(
                {
                    "Step key": step_key,
                    "Kubernetes Job name": job_name,
                    "Job image": job_config.job_image,
                    "Image pull policy": job_config.image_pull_policy,
                    "Image pull secrets": str(job_config.image_pull_secrets),
                    "Service account name": str(job_config.service_account_name),
                },
                marker_end=DELEGATE_MARKER,
            ),
            CeleryK8sJobExecutor,
            # validated above that step_keys is length 1, and it is not possible to use ETH or
            # execution plan in this function (Celery K8s workers should not access to user code)
            step_key=step_key,
        )
        events.append(engine_event)
        try:
            api_client.batch_api.create_namespaced_job(body=job, namespace=job_namespace)
        except kubernetes.client.rest.ApiException as e:
            if e.reason == "Conflict":
                # There is an existing job with the same name so proceed and see if the existing job succeeded
                instance.report_engine_event(
                    "Did not create Kubernetes job {} for step {} since job name already "
                    "exists, proceeding with existing job.".format(job_name, step_key),
                    dagster_run,
                    EngineEventData(
                        {
                            "Step key": step_key,
                            "Kubernetes Job name": job_name,
                        },
                        marker_end=DELEGATE_MARKER,
                    ),
                    CeleryK8sJobExecutor,
                    step_key=step_key,
                )
            else:
                instance.report_engine_event(
                    "Encountered unexpected error while creating Kubernetes job {} for step {}, "
                    "exiting.".format(job_name, step_key),
                    dagster_run,
                    EngineEventData(
                        {
                            "Step key": step_key,
                        },
                        error=serializable_error_info_from_exc_info(sys.exc_info()),
                    ),
                    CeleryK8sJobExecutor,
                    step_key=step_key,
                )
                return []

        try:
            api_client.wait_for_job_success(
                job_name=job_name,
                namespace=job_namespace,
                instance=instance,
                run_id=execute_step_args.run_id,
                wait_timeout=job_wait_timeout,
            )
        except (DagsterK8sError, DagsterK8sTimeoutError) as err:
            step_failure_event = construct_step_failure_event_and_handle(
                dagster_run, step_key, err, instance=instance
            )
            events.append(step_failure_event)
        except DagsterK8sJobStatusException:
            instance.report_engine_event(
                "Terminating Kubernetes Job because dagster run status is not STARTED",
                dagster_run,
                EngineEventData(
                    {
                        "Step key": step_key,
                        "Kubernetes Job name": job_name,
                        "Kubernetes Job namespace": job_namespace,
                    }
                ),
                CeleryK8sJobExecutor,
                step_key=step_key,
            )
            api_client.delete_job(job_name=job_name, namespace=job_namespace)
            return []
        except (
            DagsterK8sUnrecoverableAPIError,
            DagsterK8sAPIRetryLimitExceeded,
            # We shouldn't see unwrapped APIExceptions anymore, as they should all be wrapped in
            # a retry boundary. We still catch it here just in case we missed one so that we can
            # report it to the event log
            kubernetes.client.rest.ApiException,
        ):
            instance.report_engine_event(
                "Encountered unexpected error while waiting on Kubernetes job {} for step {}, "
                "exiting.".format(job_name, step_key),
                dagster_run,
                EngineEventData(
                    {
                        "Step key": step_key,
                    },
                    error=serializable_error_info_from_exc_info(sys.exc_info()),
                ),
                CeleryK8sJobExecutor,
                step_key=step_key,
            )
            return []

        try:
            pod_names = api_client.get_pod_names_in_job(job_name, namespace=job_namespace)
        except kubernetes.client.rest.ApiException:
            instance.report_engine_event(
                "Encountered unexpected error retreiving Pods for Kubernetes job {} for step {}, "
                "exiting.".format(job_name, step_key),
                dagster_run,
                EngineEventData(
                    {
                        "Step key": step_key,
                    },
                    error=serializable_error_info_from_exc_info(sys.exc_info()),
                ),
                CeleryK8sJobExecutor,
                step_key=step_key,
            )
            return []

        # Post engine event for log retrieval
        engine_event = instance.report_engine_event(
            "Retrieving logs from Kubernetes Job pods",
            dagster_run,
            EngineEventData({"Pod names": "\n".join(pod_names)}),
            CeleryK8sJobExecutor,
            step_key=step_key,
        )
        events.append(engine_event)

        logs = []
        for pod_name in pod_names:
            try:
                raw_logs = api_client.retrieve_pod_logs(pod_name, namespace=job_namespace)
                logs += raw_logs.split("\n")
            except kubernetes.client.exceptions.ApiException:
                instance.report_engine_event(
                    "Encountered unexpected error while fetching pod logs for Kubernetes job {}, "
                    "Pod name {} for step {}. Will attempt to continue with other pods.".format(
                        job_name, pod_name, step_key
                    ),
                    dagster_run,
                    EngineEventData(
                        {
                            "Step key": step_key,
                        },
                        error=serializable_error_info_from_exc_info(sys.exc_info()),
                    ),
                    CeleryK8sJobExecutor,
                    step_key=step_key,
                )

        events += filter_dagster_events_from_cli_logs(logs)
        serialized_events = [serialize_value(event) for event in events]
        return serialized_events

    return _execute_step_k8s_job
