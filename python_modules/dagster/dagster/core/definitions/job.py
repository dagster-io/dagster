import warnings
from typing import TYPE_CHECKING, AbstractSet, Any, Dict, List, Optional

from dagster import check
from dagster.core.definitions.policy import RetryPolicy

from .graph import GraphDefinition
from .hook import HookDefinition
from .mode import ModeDefinition
from .partition import Partition, PartitionSetDefinition
from .pipeline import PipelineDefinition
from .preset import PresetDefinition
from .resource import ResourceDefinition
from .version_strategy import VersionStrategy

if TYPE_CHECKING:
    from dagster.core.instance import DagsterInstance
    from dagster.core.execution.execute_in_process_result import ExecuteInProcessResult


class JobDefinition(PipelineDefinition):
    def __init__(
        self,
        mode_def: ModeDefinition,
        graph_def: GraphDefinition,
        name: Optional[str] = None,
        description: Optional[str] = None,
        preset_defs: Optional[List[PresetDefinition]] = None,
        tags: Dict[str, Any] = None,
        hook_defs: Optional[AbstractSet[HookDefinition]] = None,
        solid_retry_policy: Optional[RetryPolicy] = None,
        version_strategy: Optional[VersionStrategy] = None,
    ):

        self._cached_partition_set: Optional["PartitionSetDefinition"] = None

        super(JobDefinition, self).__init__(
            name=name,
            description=description,
            mode_defs=[mode_def],
            preset_defs=preset_defs,
            tags=tags,
            hook_defs=hook_defs,
            solid_retry_policy=solid_retry_policy,
            graph_def=graph_def,
            version_strategy=version_strategy,
        )

    @property
    def target_type(self):
        return "job"

    def describe_target(self):
        return f"{self.target_type} '{self.name}'"

    def execute_in_process(
        self,
        run_config: Optional[Dict[str, Any]] = None,
        instance: Optional["DagsterInstance"] = None,
        partition_name: Optional[str] = None,
        raise_on_error: bool = True,
    ) -> "ExecuteInProcessResult":
        """
        (Experimental) Execute the Job in-process, gathering results in-memory.

        The executor_def on the Job will be ignored, and replaced with the in-process executor.
        If using the default io_manager, it will switch from filesystem to in-memory.


        Args:
            run_config (Optional[Dict[str, Any]]:
                The configuration for the run
            instance (Optional[DagsterInstance]):
                The instance to execute against, an ephemeral one will be used if none provided.
            partition_name: (Optional[str])
                The name of the partition entry that specifies the run config to execute.  Can only
                be used to select run config for jobs with partitioned config.
            raise_on_error (Optional[bool]): Whether or not to raise exceptions when they occur.
                Defaults to ``True``.

        Returns:
            ExecuteInProcessResult

        """
        from dagster.core.definitions.executor import execute_in_process_executor
        from dagster.core.execution.execute_in_process import core_execute_in_process

        run_config = check.opt_dict_param(run_config, "run_config")
        partition_name = check.opt_str_param(partition_name, "partition_name")

        check.invariant(
            len(self._mode_definitions) == 1,
            "execute_in_process only supported on job / single mode pipeline",
        )

        base_mode = self.get_mode_definition()
        # create an ephemeral in process mode by replacing the executor_def and
        # switching the default fs io_manager to in mem, if another was not set
        in_proc_mode = ModeDefinition(
            name="in_process",
            executor_defs=[execute_in_process_executor],
            resource_defs=_swap_default_io_man(base_mode.resource_defs, self),
            logger_defs=base_mode.loggers,
            _config_mapping=base_mode.config_mapping,
            _partitioned_config=base_mode.partitioned_config,
        )

        ephemeral_job = JobDefinition(
            name=self._name,
            graph_def=self._graph_def,
            mode_def=in_proc_mode,
            hook_defs=self.hook_defs,
            tags=self.tags,
            version_strategy=self.version_strategy,
        )

        if partition_name:
            if not base_mode.partitioned_config:
                raise Exception("this is not a partitioned job")
            check.invariant(
                not run_config,
                "cannot provide both run_config and partition arguments to `execute_in_process`",
            )
            run_config = base_mode.partitioned_config.get_run_config(partition_name)

        return core_execute_in_process(
            node=self._graph_def,
            ephemeral_pipeline=ephemeral_job,
            run_config=run_config,
            instance=instance,
            output_capturing_enabled=True,
            raise_on_error=raise_on_error,
        )

    def get_pipeline_subset_def(self, solids_to_execute: AbstractSet[str]) -> PipelineDefinition:

        warnings.warn(
            f"Attempted to subset job {self.name}. The subsetted job will be represented by a "
            "PipelineDefinition."
        )

        return super(JobDefinition, self).get_pipeline_subset_def(solids_to_execute)

    def get_partition_set_def(self) -> Optional["PartitionSetDefinition"]:
        if not self.is_single_mode:
            return None

        mode = self.get_mode_definition()
        if not mode.partitioned_config:
            return None

        if not self._cached_partition_set:

            self._cached_partition_set = PartitionSetDefinition(
                pipeline_name=self.name,
                name=f"{self.name}_partition_set",
                partitions_def=mode.partitioned_config.partitions_def,
                run_config_fn_for_partition=mode.partitioned_config.run_config_for_partition_fn,
                mode=mode.name,
            )

        return self._cached_partition_set


def _swap_default_io_man(resources: Dict[str, ResourceDefinition], job: PipelineDefinition):
    """
    Used to create the user facing experience of the default io_manager
    switching to in-memory when using execute_in_process.
    """
    from dagster.core.storage.mem_io_manager import mem_io_manager
    from .graph import default_job_io_manager

    if (
        # pylint: disable=comparison-with-callable
        resources.get("io_manager") == default_job_io_manager
        and job.version_strategy is None
    ):
        updated_resources = dict(resources)
        updated_resources["io_manager"] = mem_io_manager
        return updated_resources

    return resources
