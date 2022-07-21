import dask
import dask.distributed

from dagster import Executor, Field, Permissive, Selector, StringSource
from dagster import _check as check
from dagster import _seven, multiple_process_executor_requirements
from dagster._core.definitions.executor_definition import executor
from dagster._core.errors import raise_execution_interrupts
from dagster._core.events import DagsterEvent
from dagster._core.execution.api import create_execution_plan, execute_plan
from dagster._core.execution.context.system import PlanOrchestrationContext
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.execution.retries import RetryMode
from dagster._core.instance import DagsterInstance
from dagster._utils import frozentags, iterate_with_context

# Dask resource requirements are specified under this key
DASK_RESOURCE_REQUIREMENTS_KEY = "dagster-dask/resource_requirements"


@executor(
    name="dask",
    requirements=multiple_process_executor_requirements(),
    config_schema={
        "cluster": Field(
            Selector(
                {
                    "existing": Field(
                        {"address": StringSource},
                        description="Connect to an existing scheduler.",
                    ),
                    "local": Field(
                        Permissive(), is_required=False, description="Local cluster configuration."
                    ),
                    "yarn": Field(
                        Permissive(), is_required=False, description="YARN cluster configuration."
                    ),
                    "ssh": Field(
                        Permissive(), is_required=False, description="SSH cluster configuration."
                    ),
                    "pbs": Field(
                        Permissive(), is_required=False, description="PBS cluster configuration."
                    ),
                    "moab": Field(
                        Permissive(), is_required=False, description="Moab cluster configuration."
                    ),
                    "sge": Field(
                        Permissive(), is_required=False, description="SGE cluster configuration."
                    ),
                    "lsf": Field(
                        Permissive(), is_required=False, description="LSF cluster configuration."
                    ),
                    "slurm": Field(
                        Permissive(), is_required=False, description="SLURM cluster configuration."
                    ),
                    "oar": Field(
                        Permissive(), is_required=False, description="OAR cluster configuration."
                    ),
                    "kube": Field(
                        Permissive(),
                        is_required=False,
                        description="Kubernetes cluster configuration.",
                    ),
                }
            )
        )
    },
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

    To use the `dask_executor`, set it as the `executor_def` when defining a job:

    .. code-block:: python

        from dagster import job
        from dagster_dask import dask_executor

        @job(executor_def=dask_executor)
        def dask_enabled_job():
            pass

    """
    ((cluster_type, cluster_configuration),) = init_context.executor_config["cluster"].items()
    return DaskExecutor(cluster_type, cluster_configuration)


def query_on_dask_worker(
    dependencies,
    recon_pipeline,
    pipeline_run,
    run_config,
    step_keys,
    mode,
    instance_ref,
    known_state,
):  # pylint: disable=unused-argument
    """Note that we need to pass "dependencies" to ensure Dask sequences futures during task
    scheduling, even though we do not use this argument within the function.
    """

    with DagsterInstance.from_ref(instance_ref) as instance:
        subset_pipeline = recon_pipeline.subset_for_execution_from_existing_pipeline(
            pipeline_run.solids_to_execute
        )

        execution_plan = create_execution_plan(
            subset_pipeline,
            run_config=run_config,
            step_keys_to_execute=step_keys,
            mode=mode,
            known_state=known_state,
        )

        return execute_plan(
            execution_plan, subset_pipeline, instance, pipeline_run, run_config=run_config
        )


def get_dask_resource_requirements(tags):
    check.inst_param(tags, "tags", frozentags)
    req_str = tags.get(DASK_RESOURCE_REQUIREMENTS_KEY)
    if req_str is not None:
        return _seven.json.loads(req_str)

    return {}


class DaskExecutor(Executor):
    def __init__(self, cluster_type, cluster_configuration):
        self.cluster_type = check.opt_str_param(cluster_type, "cluster_type", default="local")
        self.cluster_configuration = check.opt_dict_param(
            cluster_configuration, "cluster_configuration"
        )

    @property
    def retries(self):
        return RetryMode.DISABLED

    def execute(self, plan_context, execution_plan):
        check.inst_param(plan_context, "plan_context", PlanOrchestrationContext)
        check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
        check.param_invariant(
            isinstance(plan_context.executor, DaskExecutor),
            "plan_context",
            "Expected executor to be DaskExecutor got {}".format(plan_context.executor),
        )

        check.invariant(
            plan_context.instance.is_persistent,
            "Dask execution requires a persistent DagsterInstance",
        )

        step_levels = execution_plan.get_steps_to_execute_by_level()

        pipeline_name = plan_context.pipeline_name

        instance = plan_context.instance

        cluster_type = self.cluster_type
        if cluster_type == "existing":
            # address passed directly to Client() below to connect to existing Scheduler
            cluster = self.cluster_configuration["address"]
        elif cluster_type == "local":
            from dask.distributed import LocalCluster

            cluster = LocalCluster(**self.build_dict(pipeline_name))
        elif cluster_type == "yarn":
            from dask_yarn import YarnCluster

            cluster = YarnCluster(**self.build_dict(pipeline_name))
        elif cluster_type == "ssh":
            from dask.distributed import SSHCluster

            cluster = SSHCluster(**self.build_dict(pipeline_name))
        elif cluster_type == "pbs":
            from dask_jobqueue import PBSCluster

            cluster = PBSCluster(**self.build_dict(pipeline_name))
        elif cluster_type == "moab":
            from dask_jobqueue import MoabCluster

            cluster = MoabCluster(**self.build_dict(pipeline_name))
        elif cluster_type == "sge":
            from dask_jobqueue import SGECluster

            cluster = SGECluster(**self.build_dict(pipeline_name))
        elif cluster_type == "lsf":
            from dask_jobqueue import LSFCluster

            cluster = LSFCluster(**self.build_dict(pipeline_name))
        elif cluster_type == "slurm":
            from dask_jobqueue import SLURMCluster

            cluster = SLURMCluster(**self.build_dict(pipeline_name))
        elif cluster_type == "oar":
            from dask_jobqueue import OARCluster

            cluster = OARCluster(**self.build_dict(pipeline_name))
        elif cluster_type == "kube":
            from dask_kubernetes import KubeCluster

            cluster = KubeCluster(**self.build_dict(pipeline_name))
        else:
            raise ValueError(
                f"Must be providing one of the following ('existing', 'local', 'yarn', 'ssh', 'pbs', 'moab', 'sge', 'lsf', 'slurm', 'oar', 'kube') not {cluster_type}"
            )

        with dask.distributed.Client(cluster) as client:
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

                    if plan_context.pipeline.get_definition().is_job:
                        run_config = plan_context.run_config
                    else:
                        run_config = dict(plan_context.run_config, execution={"in_process": {}})

                    dask_task_name = "%s.%s" % (pipeline_name, step.key)

                    recon_pipeline = plan_context.reconstructable_pipeline

                    future = client.submit(
                        query_on_dask_worker,
                        dependencies,
                        recon_pipeline,
                        plan_context.pipeline_run,
                        run_config,
                        [step.key],
                        plan_context.pipeline_run.mode,
                        instance.get_ref(),
                        execution_plan.known_state,
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
