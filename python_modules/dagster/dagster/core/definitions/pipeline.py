import six

from dagster import check
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.utils import toposort_flatten
from dagster.core.errors import DagsterInvalidDefinitionError

from .context import PipelineContextDefinition, default_pipeline_context_definitions
from .dependency import DependencyDefinition, DependencyStructure, Solid, SolidHandle, SolidInstance
from .pipeline_creation import create_execution_structure, construct_runtime_type_dictionary
from .solid import ISolidDefinition


def _check_solids_arg(pipeline_name, solid_defs):
    if not isinstance(solid_defs, list):
        raise DagsterInvalidDefinitionError(
            '"solids" arg to pipeline "{name}" is not a list. Got {val}.'.format(
                name=pipeline_name, val=repr(solid_defs)
            )
        )
    for solid_def in solid_defs:
        if isinstance(solid_def, ISolidDefinition):
            continue
        elif callable(solid_def):
            raise DagsterInvalidDefinitionError(
                '''You have passed a lambda or function {func} into pipeline {name} that is
                not a solid. You have likely forgetten to annotate this function with
                an @solid or @lambda_solid decorator.'
                '''.format(
                    name=pipeline_name, func=solid_def.__name__
                )
            )
        else:
            raise DagsterInvalidDefinitionError(
                'Invalid item in solid list: {item}'.format(item=repr(solid_def))
            )

    return solid_defs


class PipelineDefinition(object):
    '''A instance of a PipelineDefinition represents a pipeline in dagster.

    A pipeline is comprised of:

    - Solids:
        Each solid represents a functional unit of data computation.

    - Context Definitions:
        Pipelines can be designed to execute in a number of different operating environments
        (e.g. prod, dev, unittest) that require different configuration and setup. A context
        definition defines how a context (of type ExecutionContext) is created and what
        configuration is necessary to create it.

    - Dependencies:
        Solids within a pipeline are arranged as a DAG (directed, acyclic graph). Dependencies
        determine how the values produced by solids flow through the DAG.

    Args:
        solids (List[SolidDefinition]):
            The set of solid definitions used in this pipeline.
        name (Optional[str])
        despcription (Optional[str])
        context_definitions (Optional[Dict[str, PipelineContextDefinition]]):
            A mapping of context names to PipelineContextDefinition.
        dependencies (Optional[Dict[Union[str, SolidInstance], Dict[str, DependencyDefinition]]]):
            A structure that declares where each solid gets its inputs. The keys at the top
            level dict are either string names of solids or SolidInstances. The values
            are dicts that map input names to DependencyDefinitions.


    Attributes:
        name (str):
            Name of the pipeline. Must be unique per-repository.
        description (str):
            Description of the pipeline. Optional.
        solids (List[SolidDefinition]):
            List of the solids in this pipeline.
        dependencies (Dict[str, Dict[str, DependencyDefinition]]) :
            Dependencies that constitute the structure of the pipeline. This is a two-dimensional
            array that maps solid_name => input_name => DependencyDefinition instance
        context_definitions (Dict[str, PipelineContextDefinition]):
            The context definitions available for consumers of this pipelines. For example, a
            unit-testing environment and a production environment probably have very different
            configuration and requirements. There would be one context definition per
            environment.

            Only one context will be used at runtime, selected by environment configuration.
        dependency_structure (DependencyStructure):
            Used mostly internally. This has the same information as the dependencies data
            structure, but indexed for fast usage.
    '''

    def __init__(
        self, solids, name=None, description=None, context_definitions=None, dependencies=None
    ):
        self.name = check.opt_str_param(name, 'name', '<<unnamed>>')
        self.description = check.opt_str_param(description, 'description')

        solids = check.list_param(
            _check_solids_arg(self.name, solids), 'solids', of_type=ISolidDefinition
        )

        if context_definitions is None:
            context_definitions = default_pipeline_context_definitions()

        self.context_definitions = check.dict_param(
            context_definitions,
            'context_definitions',
            key_type=str,
            value_type=PipelineContextDefinition,
        )

        self.dependencies = _validate_dependency_dict(dependencies)

        dependency_structure, pipeline_solid_dict = create_execution_structure(
            solids, self.dependencies
        )

        self._solid_dict = pipeline_solid_dict
        self.dependency_structure = dependency_structure

        self._runtime_type_dict = construct_runtime_type_dictionary(solids)

        # Validate solid resource dependencies
        _validate_resource_dependencies(self.context_definitions, solids)

    @property
    def display_name(self):
        '''Name suitable for exception messages, logging etc. If pipeline
        is unnamed the method with return "<<unnamed>>".

        Returns:
            str: Display name of pipeline
        '''
        return self.name if self.name else '<<unnamed>>'

    @property
    def solids(self):
        '''Return the solids in the pipeline.

        Returns:
            List[Solid]: List of solids.
        '''
        return list(set(self._solid_dict.values()))

    def has_solid_named(self, name):
        '''Return whether or not the solid is in the piepline

        Args:
            name (str): Name of solid

        Returns:
            bool: True if the solid is in the pipeline
        '''
        check.str_param(name, 'name')
        return name in self._solid_dict

    def solid_named(self, name):
        '''Return the solid named "name". Throws if it does not exist.

        Args:
            name (str): Name of solid

        Returns:
            SolidDefinition: SolidDefinition with correct name.
        '''
        check.str_param(name, 'name')
        if name not in self._solid_dict:
            raise DagsterInvariantViolationError(
                'Pipeline {pipeline_name} has no solid named {name}.'.format(
                    pipeline_name=self.name, name=name
                )
            )
        return self._solid_dict[name]

    def get_solid(self, handle):
        check.inst_param(handle, 'handle', SolidHandle)
        current = handle
        lineage = []
        while current:
            lineage.append(current.name)
            current = current.parent

        name = lineage.pop()
        solid = self.solid_named(name)
        while lineage:
            name = lineage.pop()
            solid = solid.definition.solid_named(name)

        return solid

    def has_runtime_type(self, name):
        check.str_param(name, 'name')
        return name in self._runtime_type_dict

    def runtime_type_named(self, name):
        check.str_param(name, 'name')
        return self._runtime_type_dict[name]

    def has_context(self, name):
        check.str_param(name, 'name')
        return name in self.context_definitions

    def all_runtime_types(self):
        return self._runtime_type_dict.values()

    @property
    def solid_defs(self):
        return list({solid.definition for solid in self.solids})

    def solid_def_named(self, name):
        check.str_param(name, 'name')

        for solid in self.solids:
            if solid.definition.name == name:
                return solid.definition

        check.failed('{} not found'.format(name))

    def has_solid_def(self, name):
        check.str_param(name, 'name')

        for solid in self.solids:
            if solid.definition.name == name:
                return True

        return False

    def build_sub_pipeline(self, solid_subset):
        return self if solid_subset is None else _build_sub_pipeline(self, solid_subset)


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
        pipeline.solids, pipeline.dependency_structure
    )

    order = toposort_flatten(backward_edges)
    return [pipeline.solid_named(solid_name) for solid_name in order]


def _dep_key_of(solid):
    return SolidInstance(solid.definition.name, solid.name)


def _build_sub_pipeline(pipeline_def, solid_names):
    '''
    Build a pipeline which is a subset of another pipeline.
    Only includes the solids which are in solid_names.
    '''

    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.list_param(solid_names, 'solid_names', of_type=str)

    solid_name_set = set(solid_names)
    solids = list(map(pipeline_def.solid_named, solid_names))
    deps = {_dep_key_of(solid): {} for solid in solids}

    def _out_handle_of_inp(input_handle):
        if pipeline_def.dependency_structure.has_dep(input_handle):
            output_handle = pipeline_def.dependency_structure.get_dep(input_handle)
            if output_handle.solid.name in solid_name_set:
                return output_handle
        return None

    for solid in solids:
        for input_handle in solid.input_handles():
            output_handle = _out_handle_of_inp(input_handle)
            if output_handle:
                deps[_dep_key_of(solid)][input_handle.input_def.name] = DependencyDefinition(
                    solid=output_handle.solid.name, output=output_handle.output_def.name
                )

    return PipelineDefinition(
        name=pipeline_def.name,
        solids=list({solid.definition for solid in solids}),
        context_definitions=pipeline_def.context_definitions,
        dependencies=deps,
    )


def _validate_dependency_dict(dependencies):
    prelude = (
        'The expected type for "dependencies" is dict[Union[str, SolidInstance], dict[str, '
        'DependencyDefinition]]. '
    )

    if dependencies is None:
        return {}

    if not isinstance(dependencies, dict):
        raise DagsterInvalidDefinitionError(
            prelude
            + 'Received value {val} of type {type} at the top level.'.format(
                val=dependencies, type=type(dependencies)
            )
        )

    for key, dep_dict in dependencies.items():
        if not (isinstance(key, six.string_types) or isinstance(key, SolidInstance)):
            raise DagsterInvalidDefinitionError(
                prelude + 'Expected str or SolidInstance key in the top level dict. '
                'Received value {val} of type {type}'.format(val=key, type=type(key))
            )
        if not isinstance(dep_dict, dict):
            if isinstance(dep_dict, DependencyDefinition):
                raise DagsterInvalidDefinitionError(
                    prelude + 'Received a DependencyDefinition one layer too high under key {key}. '
                    'The DependencyDefinition should be moved in to a dict keyed on '
                    'input name.'.format(key=key)
                )
            else:
                raise DagsterInvalidDefinitionError(
                    prelude + 'Under key {key} received value {val} of type {type}. '
                    'Expected dict[str, DependencyDefinition]'.format(
                        key=key, val=dep_dict, type=type(dep_dict)
                    )
                )

        for input_key, dep in dep_dict.items():
            if not isinstance(input_key, six.string_types):
                raise DagsterInvalidDefinitionError(
                    prelude
                    + 'Received non-sting key in the inner dict for key {key}.'.format(key=key)
                )
            if not isinstance(dep, DependencyDefinition):
                raise DagsterInvalidDefinitionError(
                    prelude
                    + 'Expected DependencyDefinition for solid "{key}" input "{input_key}". '
                    'Received value {val} of type {type}.'.format(
                        key=key, input_key=input_key, val=dep, type=type(dep)
                    )
                )

    return dependencies


def _validate_resource_dependencies(context_definitions, solids):
    '''This validation ensures that each pipeline context provides the resources that are required
    by each solid.
    '''
    check.dict_param(
        context_definitions, 'context_definitions', str, value_type=PipelineContextDefinition
    )
    check.list_param(solids, 'solids', of_type=ISolidDefinition)

    for context_name, context in context_definitions.items():
        context_resources = set(context.resources.keys())

        for solid in solids:
            for resource in solid.resources:
                if resource not in context_resources:
                    raise DagsterInvalidDefinitionError(
                        (
                            'Resource "{resource}" is required by solid {solid_name}, but is not '
                            'provided by context "{context_name}"'
                        ).format(
                            resource=resource, solid_name=solid.name, context_name=context_name
                        )
                    )
