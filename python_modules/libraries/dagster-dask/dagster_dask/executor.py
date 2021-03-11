import dask
import dask.distributed
from dagster import Executor, check, seven
from dagster.core.definitions.executor import check_cross_process_constraints, executor
from dagster.core.errors import raise_execution_interrupts
from dagster.core.events import DagsterEvent
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.execution.retries import RetryMode
from dagster.core.instance import DagsterInstance
from dagster.utils import frozentags, iterate_with_context

from .config import DaskConfigSchema, create_from_config

# Dask resource requirements are specified under this key
DASK_RESOURCE_REQUIREMENTS_KEY = "dagster-dask/resource_requirements"


@executor(
    name="dask",
    config_schema=DaskConfigSchema,
)
def dask_executor(init_context):
    """Dask-based executor.

    The 'cluster' can be one of the following:
    ('existing', 'local', 'yarn', 'ssh', 'pbs', 'moab', 'sge', 'lsf', 'slurm', 'oar', 'kube').

    If the Dask executor is used without providing executor-specific config, a local Dask cluster
    will be created (as when calling :py:class:`dask.distributed.Client() <dask:distributed.Client>`
    with :py:class:`dask.distributed.LocalCluster() <dask:distributed.LocalCluster>`).

    The Dask executor optionally takes the following config:

    .. code-block:: none

        cluster:
            {
                local?: # takes distributed.LocalCluster parameters
                    {
                        timeout?: 5,  # Timeout duration for initial connection to the scheduler
                        n_workers?: 4  # Number of workers to start
                        threads_per_worker?: 1 # Number of threads per each worker
                    }
            }

    If you'd like to configure a dask executor in addition to the
    :py:class:`~dagster.default_executors`, you should add it to the ``executor_defs`` defined on a
    :py:class:`~dagster.ModeDefinition` as follows:

    .. code-block:: python

        from dagster import ModeDefinition, default_executors, pipeline
        from dagster_dask import dask_executor

        @pipeline(mode_defs=[ModeDefinition(executor_defs=default_executors + [dask_executor])])
        def dask_enabled_pipeline():
            pass

    """
    check_cross_process_constraints(init_context)
    dask_config = {
        k: init_context.executor_config.get(k, None)
        for k in DaskConfigSchema.keys()
        if k in init_context.executor_config
    }

    return DaskExecutor(dask_config)


def query_on_dask_worker(
    dependencies,
    recon_pipeline,
    pipeline_run,
    run_config,
    step_keys,
    mode,
    instance_ref,
):  # pylint: disable=unused-argument
    """Note that we need to pass "dependencies" to ensure Dask sequences futures during task
    scheduling, even though we do not use this argument within the function.
    """

    with DagsterInstance.from_ref(instance_ref) as instance:
        execution_plan = create_execution_plan(
            recon_pipeline.subset_for_execution_from_existing_pipeline(
                pipeline_run.solids_to_execute
            ),
            run_config=run_config,
            step_keys_to_execute=step_keys,
            mode=mode,
        )

        return execute_plan(execution_plan, instance, pipeline_run, run_config=run_config)


def get_dask_resource_requirements(tags):
    check.inst_param(tags, "tags", frozentags)
    req_str = tags.get(DASK_RESOURCE_REQUIREMENTS_KEY)
    if req_str is not None:
        return seven.json.loads(req_str)

    return {}


class DaskExecutor(Executor):
    def __init__(self, dask_config):
        self.dask_config = dask_config

    @property
    def retries(self):
        return RetryMode.DISABLED

    def execute(self, pipeline_context, execution_plan):
        check.inst_param(pipeline_context, "pipeline_context", SystemPipelineExecutionContext)
        check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
        check.param_invariant(
            isinstance(pipeline_context.executor, DaskExecutor),
            "pipeline_context",
            "Expected executor to be DaskExecutor got {}".format(pipeline_context.executor),
        )

        check.invariant(
            pipeline_context.instance.is_persistent,
            "Dask execution requires a persistent DagsterInstance",
        )

        step_levels = execution_plan.get_steps_to_execute_by_level()

        pipeline_name = pipeline_context.pipeline_name

        instance = pipeline_context.instance

        client, cluster = create_from_config(self.dask_config)

        with client:
            execution_futures = []
            execution_futures_dict = {}

            for step_level in step_levels:
                for step in step_level:
                    # We ensure correctness in sequencing by letting Dask schedule futures and
                    # awaiting dependencies within each step.
                    dependencies = []
                    for step_input in step.step_inputs:
                        for key in step_input.dependency_keys:
                            dependencies.append(execution_futures_dict[key])

                    run_config = dict(pipeline_context.run_config, execution={"in_process": {}})
                    recon_repo = pipeline_context.pipeline.get_reconstructable_repository()

                    dask_task_name = "%s.%s" % (pipeline_name, step.key)

                    recon_pipeline = recon_repo.get_reconstructable_pipeline(pipeline_name)

                    future = client.submit(
                        query_on_dask_worker,
                        dependencies,
                        recon_pipeline,
                        pipeline_context.pipeline_run,
                        run_config,
                        [step.key],
                        pipeline_context.mode_def.name,
                        instance.get_ref(),
                        key=dask_task_name,
                        resources=get_dask_resource_requirements(step.tags),
                    )

                    execution_futures.append(future)
                    execution_futures_dict[step.key] = future

            # This tells Dask to awaits the step executions and retrieve their results to the
            # master
            futures = dask.distributed.as_completed(execution_futures, with_results=True)

            # Allow interrupts while waiting for the results from Dask
            for future, result in iterate_with_context(raise_execution_interrupts, futures):
                for step_event in result:
                    check.inst(step_event, DagsterEvent)
                    yield step_event

    def build_dict(self, pipeline_name):
        """Returns a dict we can use for kwargs passed to dask client instantiation.

        Intended to be used like:

        with dask.distributed.Client(**cfg.build_dict()) as client:
            << use client here >>

        """
        if self.cluster_type in ["yarn", "pbs", "moab", "sge", "lsf", "slurm", "oar", "kube"]:
            dask_cfg = {"name": pipeline_name}
        else:
            dask_cfg = {}

        if self.cluster_configuration:
            for k, v in self.cluster_configuration.items():
                dask_cfg[k] = v

        # if address is set, don't add LocalCluster args
        # context: https://github.com/dask/distributed/issues/3313
        if (self.cluster_type == "local") and ("address" not in dask_cfg):
            # We set threads_per_worker because Dagster is not thread-safe. Even though
            # environments=True by default, there is a clever piece of machinery
            # (dask.distributed.deploy.local.nprocesses_nthreads) that automagically makes execution
            # multithreaded by default when the number of available cores is greater than 4.
            # See: https://github.com/dagster-io/dagster/issues/2181
            # We may want to try to figure out a way to enforce this on remote Dask clusters against
            # which users run Dagster workloads.
            dask_cfg["threads_per_worker"] = 1

        return dask_cfg
