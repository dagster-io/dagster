from functools import update_wrapper
from typing import TYPE_CHECKING, AbstractSet, Any, Dict, List, Optional

from dagster import check
from dagster.core.definitions.policy import RetryPolicy
from dagster.core.selector.subset_selector import OpSelectionData, parse_solid_selection

from .executor_definition import ExecutorDefinition
from .graph_definition import GraphDefinition
from .hook_definition import HookDefinition
from .mode import ModeDefinition
from .partition import PartitionSetDefinition
from .pipeline_definition import PipelineDefinition
from .preset import PresetDefinition
from .resource_definition import ResourceDefinition
from .version_strategy import VersionStrategy

if TYPE_CHECKING:
    from dagster.core.instance import DagsterInstance
    from dagster.core.execution.execute_in_process_result import ExecuteInProcessResult
    from dagster.core.snap import PipelineSnapshot


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
        op_retry_policy: Optional[RetryPolicy] = None,
        version_strategy: Optional[VersionStrategy] = None,
        _op_selection_data: Optional[OpSelectionData] = None,
    ):

        self._cached_partition_set: Optional["PartitionSetDefinition"] = None
        self._op_selection_data = check.opt_inst_param(
            _op_selection_data, "_op_selection_data", OpSelectionData
        )

        super(JobDefinition, self).__init__(
            name=name,
            description=description,
            mode_defs=[mode_def],
            preset_defs=preset_defs,
            tags=tags,
            hook_defs=hook_defs,
            solid_retry_policy=op_retry_policy,
            graph_def=graph_def,
            version_strategy=version_strategy,
        )

    @property
    def target_type(self) -> str:
        return "job"

    @property
    def is_job(self) -> bool:
        return True

    def describe_target(self):
        return f"{self.target_type} '{self.name}'"

    @property
    def executor_def(self) -> ExecutorDefinition:
        return self.mode_definitions[0].executor_defs[0]

    def execute_in_process(
        self,
        run_config: Optional[Dict[str, Any]] = None,
        instance: Optional["DagsterInstance"] = None,
        partition_key: Optional[str] = None,
        raise_on_error: bool = True,
        op_selection: Optional[List[str]] = None,
    ) -> "ExecuteInProcessResult":
        """
        Execute the Job in-process, gathering results in-memory.

        The `executor_def` on the Job will be ignored, and replaced with the in-process executor.
        If using the default `io_manager`, it will switch from filesystem to in-memory.


        Args:
            run_config (Optional[Dict[str, Any]]:
                The configuration for the run
            instance (Optional[DagsterInstance]):
                The instance to execute against, an ephemeral one will be used if none provided.
            partition_key: (Optional[str])
                The string partition key that specifies the run config to execute. Can only be used
                to select run config for jobs with partitioned config.
            raise_on_error (Optional[bool]): Whether or not to raise exceptions when they occur.
                Defaults to ``True``.
            op_selection (Optional[List[str]]): A list of op selection queries (including single op
                names) to execute. For example:
                * ``['some_op']``: selects ``some_op`` itself.
                * ``['*some_op']``: select ``some_op`` and all its ancestors (upstream dependencies).
                * ``['*some_op+++']``: select ``some_op``, all its ancestors, and its descendants
                (downstream dependencies) within 3 levels down.
                * ``['*some_op', 'other_op_a', 'other_op_b+']``: select ``some_op`` and all its
                ancestors, ``other_op_a`` itself, and ``other_op_b`` and its direct child ops.
        Returns:
            :py:class:`~dagster.ExecuteInProcessResult`

        """
        from dagster.core.definitions.executor_definition import execute_in_process_executor
        from dagster.core.execution.execute_in_process import core_execute_in_process

        run_config = check.opt_dict_param(run_config, "run_config")
        op_selection = check.opt_list_param(op_selection, "op_selection", str)
        partition_key = check.opt_str_param(partition_key, "partition_key")

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
            op_retry_policy=self._solid_retry_policy,
            version_strategy=self.version_strategy,
        ).get_job_def_for_op_selection(op_selection)

        if partition_key:
            if not base_mode.partitioned_config:
                check.failed(
                    f"Provided partition key `{partition_key}` for job `{self._name}` without a partitioned config"
                )
            check.invariant(
                not run_config,
                "Cannot provide both run_config and partition_key arguments to `execute_in_process`",
            )
            run_config = base_mode.partitioned_config.get_run_config(partition_key)

        return core_execute_in_process(
            node=self._graph_def,
            ephemeral_pipeline=ephemeral_job,
            run_config=run_config,
            instance=instance,
            output_capturing_enabled=True,
            raise_on_error=raise_on_error,
            run_tags={"partition": partition_key} if partition_key else None,
        )

    @property
    def op_selection_data(self) -> Optional[OpSelectionData]:
        return self._op_selection_data

    def get_job_def_for_op_selection(
        self,
        op_selection: Optional[List[str]] = None,
    ) -> "JobDefinition":
        if not op_selection:
            return self

        op_selection = check.opt_list_param(op_selection, "op_selection", str)

        # TODO: https://github.com/dagster-io/dagster/issues/2115
        #   op selection currently still operates on PipelineSubsetDefinition. ideally we'd like to
        #   1) move away from creating PipelineSubsetDefinition
        #   2) consolidate solid selection and step selection
        #   3) enable subsetting nested graphs/ops which isn't working with the current setting
        solids_to_execute = (
            self._op_selection_data.resolved_op_selection if self._op_selection_data else None
        )
        if op_selection:
            solids_to_execute = parse_solid_selection(
                super(JobDefinition, self).get_pipeline_subset_def(solids_to_execute),
                op_selection,
            )
        subset_pipeline_def = super(JobDefinition, self).get_pipeline_subset_def(solids_to_execute)
        ignored_solids = [
            solid
            for solid in self._graph_def.solids
            if not subset_pipeline_def.has_solid_named(solid.name)
        ]

        return JobDefinition(
            name=self.name,
            description=self.description,
            mode_def=self.get_mode_definition(),
            preset_defs=self.preset_defs,
            tags=self.tags,
            hook_defs=self.hook_defs,
            op_retry_policy=self._solid_retry_policy,
            graph_def=subset_pipeline_def.graph,
            version_strategy=self.version_strategy,
            _op_selection_data=OpSelectionData(
                op_selection=op_selection,
                resolved_op_selection=solids_to_execute,
                ignored_solids=ignored_solids,
                parent_job_def=self,
            ),
        )

    def get_partition_set_def(self) -> Optional["PartitionSetDefinition"]:
        if not self.is_single_mode:
            return None

        mode = self.get_mode_definition()
        if not mode.partitioned_config:
            return None

        if not self._cached_partition_set:

            self._cached_partition_set = PartitionSetDefinition(
                job_name=self.name,
                name=f"{self.name}_partition_set",
                partitions_def=mode.partitioned_config.partitions_def,
                run_config_fn_for_partition=mode.partitioned_config.run_config_for_partition_fn,
                mode=mode.name,
            )

        return self._cached_partition_set

    def with_hooks(self, hook_defs: AbstractSet[HookDefinition]) -> "JobDefinition":
        """Apply a set of hooks to all op instances within the job."""

        hook_defs = check.set_param(hook_defs, "hook_defs", of_type=HookDefinition)

        job_def = JobDefinition(
            name=self.name,
            graph_def=self._graph_def,
            mode_def=self.mode_definitions[0],
            preset_defs=self.preset_defs,
            tags=self.tags,
            hook_defs=hook_defs | self.hook_defs,
            description=self._description,
            op_retry_policy=self._solid_retry_policy,
            _op_selection_data=self._op_selection_data,
        )

        update_wrapper(job_def, self, updated=())

        return job_def

    def get_parent_pipeline_snapshot(self) -> Optional["PipelineSnapshot"]:
        return (
            self.op_selection_data.parent_job_def.get_pipeline_snapshot()
            if self.op_selection_data
            else None
        )


def _swap_default_io_man(resources: Dict[str, ResourceDefinition], job: PipelineDefinition):
    """
    Used to create the user facing experience of the default io_manager
    switching to in-memory when using execute_in_process.
    """
    from dagster.core.storage.mem_io_manager import mem_io_manager
    from .graph_definition import default_job_io_manager

    if (
        # pylint: disable=comparison-with-callable
        resources.get("io_manager") == default_job_io_manager
        and job.version_strategy is None
    ):
        updated_resources = dict(resources)
        updated_resources["io_manager"] = mem_io_manager
        return updated_resources

    return resources
