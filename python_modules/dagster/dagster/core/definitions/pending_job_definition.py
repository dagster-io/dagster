from typing import TYPE_CHECKING, AbstractSet, Any, Dict, List, NamedTuple, Optional

import dagster._check as check
from dagster.core.definitions.policy import RetryPolicy
from dagster.core.selector.subset_selector import OpSelectionData, parse_op_selection
from dagster.utils import merge_dicts

from .asset_layer import AssetLayer
from .config import ConfigMapping
from .executor_definition import ExecutorDefinition
from .graph_definition import GraphDefinition
from .hook_definition import HookDefinition
from .job_definition import JobDefinition, get_subselected_graph_definition
from .logger_definition import LoggerDefinition
from .partition import PartitionedConfig
from .preset import PresetDefinition
from .resource_definition import ResourceDefinition
from .version_strategy import VersionStrategy

if TYPE_CHECKING:
    from dagster.core.execution.execute_in_process_result import ExecuteInProcessResult
    from dagster.core.instance import DagsterInstance
    from dagster.core.snap import PipelineSnapshot


class PendingJobDefinition(
    NamedTuple(
        "_PendingJobDefinition",
        [
            ("resource_defs", Dict[str, ResourceDefinition]),
            ("loggers", Dict[str, LoggerDefinition]),
            ("executor_def", Optional[ExecutorDefinition]),
            ("config_mapping", Optional[ConfigMapping]),
            ("partitioned_config", Optional[PartitionedConfig]),
            ("graph_def", GraphDefinition),
            ("name", Optional[str]),
            ("description", Optional[str]),
            ("preset_defs", List[PresetDefinition]),
            ("tags", Dict[str, Any]),
            ("hook_defs", AbstractSet[HookDefinition]),
            ("op_retry_policy", Optional[RetryPolicy]),
            ("version_strategy", Optional[VersionStrategy]),
            ("subset_selection_data", Optional[OpSelectionData]),
            ("asset_layer", Optional[AssetLayer]),
        ],
    )
):
    def __new__(
        cls,
        resource_defs: Dict[str, ResourceDefinition],
        loggers: Dict[str, LoggerDefinition],
        executor_def: Optional[ExecutorDefinition],
        config_mapping: Optional[ConfigMapping],
        partitioned_config: Optional[PartitionedConfig],
        graph_def: GraphDefinition,
        name: Optional[str],
        description: Optional[str],
        preset_defs: List[PresetDefinition],
        tags: Dict[str, Any],
        hook_defs: AbstractSet[HookDefinition],
        op_retry_policy: Optional[RetryPolicy],
        version_strategy: Optional[VersionStrategy],
        asset_layer: Optional[AssetLayer],
        subset_selection_data: Optional[OpSelectionData] = None,
    ):
        return super(PendingJobDefinition, cls).__new__(
            cls,
            resource_defs=dict(check.opt_mapping_param(resource_defs, "resource_defs")),
            loggers=check.opt_dict_param(loggers, "loggers"),
            executor_def=executor_def,
            config_mapping=config_mapping,
            partitioned_config=partitioned_config,
            graph_def=graph_def,
            name=name,
            description=description,
            preset_defs=preset_defs,
            tags=tags,
            hook_defs=hook_defs,
            op_retry_policy=op_retry_policy,
            version_strategy=version_strategy,
            subset_selection_data=subset_selection_data,
            asset_layer=asset_layer,
        )

    def coerce_to_job_def(self, resource_defs: Dict[str, ResourceDefinition]) -> JobDefinition:
        override_resource_defs = self.resource_defs

        resource_defs = merge_dicts(
            resource_defs, override_resource_defs if override_resource_defs else {}
        )

        return JobDefinition(
            resource_defs=resource_defs,
            logger_defs=self.loggers,
            executor_def=self.executor_def,
            config_mapping=self.config_mapping,
            partitioned_config=self.partitioned_config,
            graph_def=self.graph_def,
            name=self.name,
            description=self.description,
            preset_defs=self.preset_defs,
            tags=self.tags,
            hook_defs=self.hook_defs,
            op_retry_policy=self.op_retry_policy,
            version_strategy=self.version_strategy,
            _subset_selection_data=self.subset_selection_data,
            asset_layer=self.asset_layer,
        )

    def get_job_def_for_op_selection(
        self,
        op_selection: Optional[List[str]] = None,
    ) -> "PendingJobDefinition":
        if not op_selection:
            return self

        op_selection = check.opt_list_param(op_selection, "op_selection", str)

        resolved_op_selection_dict = parse_op_selection(
            graph_def=self.graph_def, op_selection=op_selection, is_job=True
        )

        sub_graph = get_subselected_graph_definition(self.graph_def, resolved_op_selection_dict)

        return PendingJobDefinition(
            name=self.name,
            description=self.description,
            resource_defs=self.resource_defs,
            loggers=self.loggers,
            executor_def=self.executor_def,
            config_mapping=self.config_mapping,
            partitioned_config=self.partitioned_config,
            preset_defs=self.preset_defs,
            tags=self.tags,
            hook_defs=self.hook_defs,
            op_retry_policy=self.op_retry_policy,
            graph_def=sub_graph,
            version_strategy=self.version_strategy,
            subset_selection_data=OpSelectionData(
                op_selection=op_selection,
                resolved_op_selection=set(
                    resolved_op_selection_dict.keys()
                ),  # equivalent to solids_to_execute. currently only gets top level nodes.
                parent_job_def=self,  # used by pipeline snapshot lineage
            ),
            asset_layer=self.asset_layer,
        )
