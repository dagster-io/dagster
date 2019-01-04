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

from .input import InputDefinition

from .output import OutputDefinition

from .resource import ResourceDefinition

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


class RepositoryDefinition(object):
    '''Define a repository that contains a collection of pipelines.

    Attributes:
        name (str): The name of the pipeline.
        pipeline_dict (Dict[str, callable]):
            An dictionary of pipelines. The value of the dictionary is a function that takes
            no parameters and returns a PipelineDefiniton.

            We pass callables instead of the PipelineDefinitions itself so that they can be
            created on demand when accessed by name.

            As the pipelines are retrieved it ensures that the keys of the dictionary and the
            name of the pipeline are the same.

    '''

    def __init__(self, name, pipeline_dict, enforce_uniqueness=True):
        '''
        Args:
            name (str): Name of pipeline.
            pipeline_dict (Dict[str, callable]): See top-level class documentation
        '''
        self.name = check.str_param(name, 'name')

        check.dict_param(
            pipeline_dict,
            'pipeline_dict',
            key_type=str,
        )

        for val in pipeline_dict.values():
            check.is_callable(val, 'Value in pipeline_dict must be function')

        self.pipeline_dict = pipeline_dict

        self._pipeline_cache = {}

        self.enforce_uniqueness = enforce_uniqueness

    def has_pipeline(self, name):
        check.str_param(name, 'name')
        return name in self.pipeline_dict

    def get_pipeline(self, name):
        '''Get a pipeline by name. Only constructs that pipeline and caches it.

        Args:
            name (str): Name of the pipeline to retriever

        Returns:
            PipelineDefinition: Instance of PipelineDefinition with that name.
'''
        check.str_param(name, 'name')

        if name in self._pipeline_cache:
            return self._pipeline_cache[name]

        pipeline = self.pipeline_dict[name]()
        check.invariant(
            pipeline.name == name,
            'Name does not match. Name in dict {name}. Name in pipeline {pipeline.name}'.format(
                name=name, pipeline=pipeline
            )
        )

        self._pipeline_cache[name] = check.inst(
            pipeline,
            PipelineDefinition,
            'Function passed into pipeline_dict with key {key} must return a PipelineDefinition'.
            format(key=name),
        )

        return pipeline

    def iterate_over_pipelines(self):
        '''Yield all pipelines one at a time

        Returns:
            Iterable[PipelineDefinition]:
        '''
        for name in self.pipeline_dict.keys():
            yield self.get_pipeline(name)

    def get_all_pipelines(self):
        '''Return all pipelines as a list

        Returns:
            List[PipelineDefinition]:

        '''
        pipelines = list(self.iterate_over_pipelines())

        self._construct_solid_defs(pipelines)

        return pipelines

    def _construct_solid_defs(self, pipelines):
        solid_defs = {}
        solid_to_pipeline = {}
        for pipeline in pipelines:
            for solid_def in pipeline.solid_defs:
                if solid_def.name not in solid_defs:
                    solid_defs[solid_def.name] = solid_def
                    solid_to_pipeline[solid_def.name] = pipeline.name
                elif self.enforce_uniqueness:
                    if not solid_defs[solid_def.name] is solid_def:
                        raise DagsterInvalidDefinitionError(
                            'Trying to add duplicate solid def {} in {}, Already saw in {}'.format(
                                solid_def.name,
                                pipeline.name,
                                solid_to_pipeline[solid_def.name],
                            )
                        )
        return solid_defs

    def get_solid_def(self, name):
        check.str_param(name, 'name')

        if not self.enforce_uniqueness:
            raise DagsterInvariantViolationError(
                (
                    'In order for get_solid_def to have reliable semantics '
                    'you must construct the repo with ensure_uniqueness=True'
                )
            )

        solid_defs = self._construct_solid_defs(self.get_all_pipelines())

        if name not in solid_defs:
            check.failed('could not find solid_def {}'.format(name))

        return solid_defs[name]

    def solid_def_named(self, name):
        check.str_param(name, 'name')
        for pipeline in self.get_all_pipelines():
            for solid in pipeline.solids:
                if solid.definition.name == name:
                    return solid.definition

        check.failed('Did not find ' + name)


class ContextCreationExecutionInfo(
    namedtuple('_ContextCreationExecutionInfo', 'config pipeline_def run_id')
):
    def __new__(cls, config, pipeline_def, run_id):
        return super(ContextCreationExecutionInfo, cls).__new__(
            cls,
            config,
            check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            check.str_param(run_id, 'run_id'),
        )


class ExpectationExecutionInfo(
    namedtuple(
        '_ExpectationExecutionInfo',
        'context inout_def solid expectation_def',
    )
):
    def __new__(cls, context, inout_def, solid, expectation_def):
        return super(ExpectationExecutionInfo, cls).__new__(
            cls,
            check.inst_param(context, 'context', RuntimeExecutionContext),
            check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition)),
            check.inst_param(solid, 'solid', Solid),
            check.inst_param(expectation_def, 'expectation_def', ExpectationDefinition),
        )


class TransformExecutionInfo(
    namedtuple('_TransformExecutionInfo', 'context config solid pipeline_def')
):
    '''An instance of TransformExecutionInfo is passed every solid transform function.

    Attributes:

        context (ExecutionContext): Context instance for this pipeline invocation
        config (Any): Config object for current solid
    '''

    def __new__(cls, context, config, solid, pipeline_def):
        return super(TransformExecutionInfo, cls).__new__(
            cls, check.inst_param(context, 'context', RuntimeExecutionContext), config,
            check.inst_param(solid, 'solid', Solid),
            check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
        )

    @property
    def solid_def(self):
        return self.solid.definition


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
