from collections import (
    defaultdict,
    namedtuple,
)
import re
from toposort import toposort_flatten

from dagster import check
from dagster.core import types
from dagster.utils.logging import (
    level_from_string,
    define_colored_console_logger,
)

from dagster.core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
)

from dagster.core.execution_context import (
    RuntimeExecutionContext,
    ExecutionContext,
)

from dagster.core.system_config.objects import DEFAULT_CONTEXT_NAME

from dagster.core.types import (
    Field,
)

from .context import (
    default_pipeline_context_definitions,
    PipelineContextDefinition,
)

from .dependency import (
    DependencyDefinition,
    DependencyStructure,
    Solid,
    SolidInputHandle,
    SolidOutputHandle,
    SolidInstance,
)

from .expectation import (
    ExpectationDefinition,
    ExpectationResult,
)

from .infos import (
    ContextCreationExecutionInfo,
    ExpectationExecutionInfo,
    TransformExecutionInfo,
)

from .input import InputDefinition

from .output import OutputDefinition

from .resource import ResourceDefinition

from .repository import RepositoryDefinition

from .pipeline import PipelineDefinition

from .pipeline_creation import create_execution_structure, construct_type_dictionary

from .solid import SolidDefinition

from .utils import (
    DEFAULT_OUTPUT,
    check_opt_two_dim_dict,
    check_opt_two_dim_str_dict,
    check_two_dim_dict,
    check_two_dim_str_dict,
    check_valid_name,
)


class Result(namedtuple('_Result', 'value output_name')):
    '''A solid transform function return a stream of Result objects.
    An implementator of a SolidDefinition must provide a transform that
    yields objects of this type.

    Attributes:
        value (Any): Value returned by the transform.
        output_name (str): Name of the output returns. defaults to "result"
'''

    def __new__(cls, value, output_name=DEFAULT_OUTPUT):
        return super(Result, cls).__new__(
            cls,
            value,
            check.str_param(output_name, 'output_name'),
        )


def all_fields_optional(field_dict):
    for field in field_dict.values():
        if not field.is_optional:
            return False
    return True


def _create_adjacency_lists(solids, dep_structure):
    check.list_param(solids, 'solids', Solid)
    check.inst_param(dep_structure, 'dep_structure', DependencyStructure)

    visit_dict = {s.name: False for s in solids}
    forward_edges = {s.name: set() for s in solids}
    backward_edges = {s.name: set() for s in solids}

    def visit(solid_name):
        if visit_dict[solid_name]:
            return

        visit_dict[solid_name] = True

        for output_handle in dep_structure.deps_of_solid(solid_name):
            forward_node = output_handle.solid.name
            backward_node = solid_name
            if forward_node in forward_edges:
                forward_edges[forward_node].add(backward_node)
                backward_edges[backward_node].add(forward_node)
                visit(forward_node)

    for s in solids:
        visit(s.name)

    return (forward_edges, backward_edges)


def solids_in_topological_order(pipeline):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)

    _forward_edges, backward_edges = _create_adjacency_lists(
        pipeline.solids,
        pipeline.dependency_structure,
    )

    order = toposort_flatten(backward_edges, sort=True)
    return [pipeline.solid_named(solid_name) for solid_name in order]
