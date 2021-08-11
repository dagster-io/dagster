from typing import TYPE_CHECKING, AbstractSet, Any, Dict, List, Optional, Union

from dagster import check
from dagster.core.definitions.policy import RetryPolicy
from dagster.core.definitions.solid import NodeDefinition

from .dependency import IDependencyDefinition, SolidInvocation
from .hook import HookDefinition
from .mode import ModeDefinition
from .pipeline import PipelineDefinition
from .preset import PresetDefinition
from .solid import NodeDefinition
from .version_strategy import VersionStrategy

if TYPE_CHECKING:
    from .run_config_schema import RunConfigSchema
    from dagster.core.snap import PipelineSnapshot, ConfigSchemaSnapshot
    from dagster.core.host_representation import PipelineIndex
    from dagster.core.instance import DagsterInstance
    from dagster.core.execution.execution_results import InProcessGraphResult


class JobDefinition(PipelineDefinition):
    def __init__(
        self,
        node_defs: Optional[List[NodeDefinition]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        dependencies: Optional[
            Dict[Union[str, SolidInvocation], Dict[str, IDependencyDefinition]]
        ] = None,
        mode_defs: Optional[List[ModeDefinition]] = None,
        preset_defs: Optional[List[PresetDefinition]] = None,
        tags: Dict[str, Any] = None,
        hook_defs: Optional[AbstractSet[HookDefinition]] = None,
        solid_retry_policy: Optional[RetryPolicy] = None,
        graph_def=None,
        version_strategy: Optional[VersionStrategy] = None,
    ):

        mode_defs = check.opt_list_param(mode_defs, "mode_defs", of_type=ModeDefinition)

        check.invariant(
            len(mode_defs) <= 1,
            "Instantiating a pipeline that represents a job, but pipeline has multiple modes.",
        )

        super(JobDefinition, self).__init__(
            solid_defs=node_defs,
            name=name,
            description=description,
            dependencies=dependencies,
            mode_defs=mode_defs,
            preset_defs=preset_defs,
            tags=tags,
            hook_defs=hook_defs,
            solid_retry_policy=solid_retry_policy,
            graph_def=graph_def,
            version_strategy=version_strategy,
        )
