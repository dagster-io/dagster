from collections import namedtuple

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster.utils import frozentags

from .dependency import DependencyDefinition, MultiDependencyDefinition, SolidInvocation
from .output import OutputDefinition
from .solid import ISolidDefinition
from .utils import validate_tags

_composition_stack = []


def enter_composition(name, source):
    _composition_stack.append(InProgressCompositionContext(name, source))


def exit_composition(output=None):
    return _composition_stack.pop().complete(output)


def current_context():
    return _composition_stack[-1]


def assert_in_composition(solid_name):
    if len(_composition_stack) < 1:
        raise DagsterInvariantViolationError(
            'Attempted to call solid "{solid_name}" outside of a composition function. '
            'Calling solids is only valid in a function decorated with '
            '@pipeline or @composite_solid.'.format(solid_name=solid_name)
        )


class InProgressCompositionContext(object):
    '''This context captures invocations of solids within a
    composition function such as @composite_solid or @pipeline
    '''

    def __init__(self, name, source):
        self.name = check.str_param(name, 'name')
        self.source = check.str_param(source, 'source')
        self._invocations = {}
        self._collisions = {}

    def observe_invocation(self, given_alias, solid_def, input_bindings, input_mappings, metadata):

        if given_alias is None:
            solid_name = solid_def.name
            if self._collisions.get(solid_name):
                self._collisions[solid_name] += 1
                solid_name = '{solid_name}_{n}'.format(
                    solid_name=solid_name, n=self._collisions[solid_name]
                )
            else:
                self._collisions[solid_name] = 1
        else:
            solid_name = given_alias

        if self._invocations.get(solid_name):
            raise DagsterInvalidDefinitionError(
                '{source} {name} invoked the same solid ({solid_name}) twice without aliasing.'.format(
                    source=self.source, name=self.name, solid_name=solid_name
                )
            )

        self._invocations[solid_name] = InvokedSolidNode(
            solid_name, solid_def, input_bindings, input_mappings, metadata
        )
        return solid_name

    def complete(self, output):
        return CompleteCompositionContext(
            self.name, self._invocations, check.opt_dict_param(output, 'output')
        )


class CompleteCompositionContext(
    namedtuple(
        '_CompositionContext', 'name solid_defs dependencies input_mappings output_mapping_dict'
    )
):
    '''The processed information from capturing solid invocations during a composition function.
    '''

    def __new__(cls, name, invocations, output_mapping_dict):

        dep_dict = {}
        solid_def_dict = {}
        input_mappings = []

        for invocation in invocations.values():
            def_name = invocation.solid_def.name
            if def_name in solid_def_dict and solid_def_dict[def_name] is not invocation.solid_def:
                raise DagsterInvalidDefinitionError(
                    'Detected conflicting solid definitions with the same name "{name}"'.format(
                        name=def_name
                    )
                )
            solid_def_dict[def_name] = invocation.solid_def

            deps = {}
            for input_name, node in invocation.input_bindings.items():
                if isinstance(node, InvokedSolidOutputHandle):
                    deps[input_name] = DependencyDefinition(node.solid_name, node.output_name)
                elif isinstance(node, list) and all(
                    map(lambda item: isinstance(item, InvokedSolidOutputHandle), node)
                ):
                    deps[input_name] = MultiDependencyDefinition(
                        [DependencyDefinition(call.solid_name, call.output_name) for call in node]
                    )
                else:
                    check.failed('Unexpected input binding - got {node}'.format(node=node))

            dep_dict[
                SolidInvocation(
                    invocation.solid_def.name, invocation.solid_name, tags=invocation.tags
                )
            ] = deps

            for input_name, node in invocation.input_mappings.items():
                input_mappings.append(node.input_def.mapping_to(invocation.solid_name, input_name))

        return super(cls, CompleteCompositionContext).__new__(
            cls, name, list(solid_def_dict.values()), dep_dict, input_mappings, output_mapping_dict
        )


class CallableSolidNode(object):
    '''An intermediate object in solid composition to allow for binding information such as
    an alias before invoking.
    '''

    def __init__(self, solid_def, given_alias=None, tags=None):
        self.solid_def = solid_def
        self.given_alias = check.opt_str_param(given_alias, 'given_alias')
        self.tags = check.opt_inst_param(tags, 'tags', frozentags)

    def __call__(self, *args, **kwargs):
        solid_name = self.given_alias if self.given_alias else self.solid_def.name
        assert_in_composition(solid_name)

        input_bindings = {}
        input_mappings = {}

        # handle *args
        for idx, output_node in enumerate(args):
            if idx >= len(self.solid_def.input_defs):
                raise DagsterInvalidDefinitionError(
                    'In {source} {name} received too many inputs for solid '
                    'invocation {solid_name}. Only {def_num} defined, received {arg_num}'.format(
                        source=current_context().source,
                        name=current_context().name,
                        solid_name=solid_name,
                        def_num=len(self.solid_def.input_defs),
                        arg_num=len(args),
                    )
                )

            input_name = self.solid_def.resolve_input_name_at_position(idx)
            if input_name is None:
                raise DagsterInvalidDefinitionError(
                    'In {source} {name} could not resolve input based on position at '
                    'index {idx} for solid invocation {solid_name}. Use keyword args instead, '
                    'available inputs are: {inputs}'.format(
                        idx=idx,
                        source=current_context().source,
                        name=current_context().name,
                        solid_name=solid_name,
                        inputs=list(map(lambda inp: inp.name, self.solid_def.input_defs)),
                    )
                )

            self._process_argument_node(
                solid_name,
                output_node,
                input_name,
                input_mappings,
                input_bindings,
                '(at position {idx})'.format(idx=idx),
            )

        # then **kwargs
        for input_name, output_node in kwargs.items():
            self._process_argument_node(
                solid_name,
                output_node,
                input_name,
                input_mappings,
                input_bindings,
                '(passed by keyword)',
            )

        solid_name = current_context().observe_invocation(
            self.given_alias, self.solid_def, input_bindings, input_mappings, self.tags
        )

        if len(self.solid_def.output_defs) == 0:
            return None

        if len(self.solid_def.output_defs) == 1:
            output_name = self.solid_def.output_defs[0].name
            return InvokedSolidOutputHandle(solid_name, output_name)

        outputs = [output_def.name for output_def in self.solid_def.output_defs]
        return namedtuple('_{solid_def}_outputs'.format(solid_def=self.solid_def.name), outputs)(
            **{output: InvokedSolidOutputHandle(solid_name, output) for output in outputs}
        )

    def _process_argument_node(
        self, solid_name, output_node, input_name, input_mappings, input_bindings, arg_desc
    ):

        if isinstance(output_node, InvokedSolidOutputHandle):
            input_bindings[input_name] = output_node
        elif isinstance(output_node, InputMappingNode):
            input_mappings[input_name] = output_node
        elif isinstance(output_node, list):
            if all(map(lambda item: isinstance(item, InvokedSolidOutputHandle), output_node)):
                input_bindings[input_name] = output_node

            else:
                raise DagsterInvalidDefinitionError(
                    'In {source} {name} received a list containing invalid types for input '
                    '"{input_name}" {arg_desc} in solid invocation {solid_name}. '
                    'Lists can only contain the output from previous solid invocations.'.format(
                        source=current_context().source,
                        name=current_context().name,
                        arg_desc=arg_desc,
                        input_name=input_name,
                        solid_name=solid_name,
                    )
                )

        elif isinstance(output_node, tuple) and all(
            map(lambda item: isinstance(item, InvokedSolidOutputHandle), output_node)
        ):
            raise DagsterInvalidDefinitionError(
                'In {source} {name} received a tuple of multiple outputs for '
                'input "{input_name}" {arg_desc} in solid invocation {solid_name}. '
                'Must pass individual output, available from tuple: {options}'.format(
                    source=current_context().source,
                    name=current_context().name,
                    arg_desc=arg_desc,
                    input_name=input_name,
                    solid_name=solid_name,
                    options=output_node._fields,
                )
            )

        else:
            raise DagsterInvalidDefinitionError(
                'In {source} {name} received invalid type {type} for input '
                '"{input_name}" {arg_desc} in solid invocation "{solid_name}". '
                'Must pass the output from previous solid invocations or inputs to the '
                'composition function as inputs when invoking solids during composition.'.format(
                    source=current_context().source,
                    name=current_context().name,
                    type=type(output_node),
                    arg_desc=arg_desc,
                    input_name=input_name,
                    solid_name=solid_name,
                )
            )

    def alias(self, name):
        return CallableSolidNode(self.solid_def, name, self.tags)

    def tag(self, tags):
        tags = validate_tags(tags)
        return CallableSolidNode(
            self.solid_def,
            self.given_alias,
            frozentags(tags) if self.tags is None else self.tags.updated_with(tags),
        )


class InvokedSolidNode(
    namedtuple('_InvokedSolidNode', 'solid_name solid_def input_bindings input_mappings tags')
):
    '''The metadata about a solid invocation saved by the current composition context.
    '''

    def __new__(cls, solid_name, solid_def, input_bindings, input_mappings, tags=None):
        return super(cls, InvokedSolidNode).__new__(
            cls,
            check.str_param(solid_name, 'solid_name'),
            check.inst_param(solid_def, 'solid_def', ISolidDefinition),
            check.dict_param(input_bindings, 'input_bindings', key_type=str),
            check.dict_param(
                input_mappings, 'input_mappings', key_type=str, value_type=InputMappingNode
            ),
            check.opt_inst_param(tags, 'tags', frozentags),
        )


class InvokedSolidOutputHandle(object):
    '''The return value for an output when invoking a solid in a composition function.
    '''

    def __init__(self, solid_name, output_name):
        self.solid_name = check.str_param(solid_name, 'solid_name')
        self.output_name = check.str_param(output_name, 'output_name')

    def __iter__(self):
        raise DagsterInvariantViolationError(
            'Attempted to iterate over an {cls}. This object represents the output "{out}" '
            'from the solid "{solid}". Consider yielding multiple Outputs if you seek to pass '
            'different parts of this output to different solids.'.format(
                cls=self.__class__.__name__, out=self.output_name, solid=self.solid_name
            )
        )

    def __getitem__(self, idx):
        raise DagsterInvariantViolationError(
            'Attempted to index in to an {cls}. This object represents the output "{out}" '
            'from the solid "{solid}". Consider yielding multiple Outputs if you seek to pass '
            'different parts of this output to different solids.'.format(
                cls=self.__class__.__name__, out=self.output_name, solid=self.solid_name
            )
        )


class InputMappingNode(object):
    def __init__(self, input_def):
        self.input_def = input_def


def composite_mapping_from_output(output, output_defs, solid_name):
    # output can be different types
    check.list_param(output_defs, 'output_defs', OutputDefinition)
    check.str_param(solid_name, 'solid_name')

    # single output
    if isinstance(output, InvokedSolidOutputHandle):
        if len(output_defs) == 1:
            defn = output_defs[0]
            return {defn.name: defn.mapping_from(output.solid_name, output.output_name)}
        else:
            raise DagsterInvalidDefinitionError(
                'Returned a single output ({solid_name}.{output_name}) in '
                '@composite_solid {name} but {num} outputs are defined. '
                'Return a dict to map defined outputs.'.format(
                    solid_name=output.solid_name,
                    output_name=output.output_name,
                    name=solid_name,
                    num=len(output_defs),
                )
            )

    output_mapping_dict = {}
    output_def_dict = {output_def.name: output_def for output_def in output_defs}

    # tuple returned directly
    if isinstance(output, tuple) and all(
        map(lambda item: isinstance(item, InvokedSolidOutputHandle), output)
    ):
        for handle in output:
            if handle.output_name not in output_def_dict:
                raise DagsterInvalidDefinitionError(
                    'Output name mismatch returning output tuple in @composite_solid {name}. '
                    'No matching OutputDefinition named {output_name} for {solid_name}.{output_name}.'
                    'Return a dict to map to the desired OutputDefinition'.format(
                        name=solid_name,
                        output_name=handle.output_name,
                        solid_name=handle.solid_name,
                    )
                )
            output_mapping_dict[handle.output_name] = output_def_dict[
                handle.output_name
            ].mapping_from(handle.solid_name, handle.output_name)

        return output_mapping_dict

    # mapping dict
    if isinstance(output, dict):
        for name, handle in output.items():
            if name not in output_def_dict:
                raise DagsterInvalidDefinitionError(
                    '@composite_solid {name} referenced key {key} which does not match any '
                    'OutputDefinitions. Valid options are: {options}'.format(
                        name=solid_name, key=name, options=list(output_def_dict.keys())
                    )
                )
            if not isinstance(handle, InvokedSolidOutputHandle):
                raise DagsterInvalidDefinitionError(
                    '@composite_solid {name} returned problematic dict entry under '
                    'key {key} of type {type}. Dict values must be outputs of '
                    'invoked solids'.format(name=solid_name, key=name, type=type(handle))
                )

            output_mapping_dict[name] = output_def_dict[name].mapping_from(
                handle.solid_name, handle.output_name
            )

        return output_mapping_dict

    # error
    if output is not None:
        raise DagsterInvalidDefinitionError(
            '@composite_solid {name} returned problematic value '
            'of type {type}. Expected return value from invoked solid or dict mapping '
            'output name to return values from invoked solids'.format(
                name=solid_name, type=type(output)
            )
        )
