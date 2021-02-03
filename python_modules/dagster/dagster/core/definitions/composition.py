import warnings
from collections import namedtuple

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster.utils import frozentags

from .config import ConfigMapping
from .decorators.solid import validate_solid_fn
from .dependency import DependencyDefinition, MultiDependencyDefinition, SolidInvocation
from .hook import HookDefinition
from .inference import (
    has_explicit_return_type,
    infer_input_definitions_for_graph,
    infer_output_definitions,
)
from .output import OutputDefinition
from .solid import NodeDefinition
from .utils import validate_tags

_composition_stack = []


class MappedInputPlaceholder:
    """Marker for holding places in fan-in lists where input mappings will feed"""


def _not_invoked_warning(solid, context_source, context_name):
    check.inst_param(solid, "solid", CallableNode)

    warning_message = (
        "While in {context} context '{name}', received an uninvoked solid '{solid_name}'.\n"
    )
    if solid.given_alias:
        warning_message += "'{solid_name}' was aliased as '{given_alias}'.\n"
    if solid.tags:
        warning_message += "Provided tags: {tags}.\n"
    if solid.hook_defs:
        warning_message += "Provided hook definitions: {hooks}.\n"

    warning_message = warning_message.format(
        context=context_source,
        name=context_name,
        solid_name=solid.node_def.name,
        given_alias=solid.given_alias,
        tags=solid.tags,
        hooks=[hook.name for hook in solid.hook_defs],
    )

    warnings.warn(warning_message.strip())


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
            "Calling solids is only valid in a function decorated with "
            "@pipeline or @composite_solid.".format(solid_name=solid_name)
        )


def _is_in_composition():
    return _composition_stack


class InProgressCompositionContext:
    """This context captures invocations of solids within a
    composition function such as @composite_solid or @pipeline
    """

    def __init__(self, name, source):
        self.name = check.str_param(name, "name")
        self.source = check.str_param(source, "source")
        self._invocations = {}
        self._collisions = {}
        self._pending_invocations = {}

    def observe_invocation(self, given_alias, node_def, input_bindings, tags=None, hook_defs=None):
        if given_alias is None:
            node_name = node_def.name
            self._pending_invocations.pop(node_name, None)
            if self._collisions.get(node_name):
                self._collisions[node_name] += 1
                node_name = "{node_name}_{n}".format(
                    node_name=node_name, n=self._collisions[node_name]
                )
            else:
                self._collisions[node_name] = 1
        else:
            node_name = given_alias
            self._pending_invocations.pop(node_name, None)

        if self._invocations.get(node_name):
            raise DagsterInvalidDefinitionError(
                "{source} {name} invoked the same node ({node_name}) twice without aliasing.".format(
                    source=self.source, name=self.name, node_name=node_name
                )
            )

        self._invocations[node_name] = InvokedNode(
            node_name, node_def, input_bindings, tags, hook_defs
        )
        return node_name

    def add_pending_invocation(self, solid):
        solid = check.opt_inst_param(solid, "solid", CallableNode)
        solid_name = solid.given_alias if solid.given_alias else solid.node_def.name
        self._pending_invocations[solid_name] = solid

    def complete(self, output):
        return CompleteCompositionContext(
            self.name,
            self.source,
            self._invocations,
            check.opt_dict_param(output, "output"),
            self._pending_invocations,
        )


class CompleteCompositionContext(
    namedtuple(
        "_CompositionContext", "name solid_defs dependencies input_mappings output_mapping_dict"
    )
):
    """The processed information from capturing solid invocations during a composition function."""

    def __new__(cls, name, source, invocations, output_mapping_dict, pending_invocations):

        dep_dict = {}
        node_def_dict = {}
        input_mappings = []

        for solid in pending_invocations.values():
            _not_invoked_warning(solid, source, name)

        for invocation in invocations.values():
            def_name = invocation.node_def.name
            if def_name in node_def_dict and node_def_dict[def_name] is not invocation.node_def:
                raise DagsterInvalidDefinitionError(
                    'Detected conflicting solid definitions with the same name "{name}"'.format(
                        name=def_name
                    )
                )
            node_def_dict[def_name] = invocation.node_def

            deps = {}
            for input_name, node in invocation.input_bindings.items():
                if isinstance(node, InvokedSolidOutputHandle):
                    deps[input_name] = DependencyDefinition(node.solid_name, node.output_name)
                elif isinstance(node, InputMappingNode):
                    input_mappings.append(
                        node.input_def.mapping_to(invocation.node_name, input_name)
                    )
                elif isinstance(node, list):
                    entries = []
                    for idx, fanned_in_node in enumerate(node):
                        if isinstance(fanned_in_node, InvokedSolidOutputHandle):
                            entries.append(
                                DependencyDefinition(
                                    fanned_in_node.solid_name, fanned_in_node.output_name
                                )
                            )
                        elif isinstance(fanned_in_node, InputMappingNode):
                            entries.append(MappedInputPlaceholder)
                            input_mappings.append(
                                fanned_in_node.input_def.mapping_to(
                                    invocation.node_name, input_name, idx
                                )
                            )
                        else:
                            check.invariant("Unexpected fanned in node received")

                    deps[input_name] = MultiDependencyDefinition(entries)
                else:
                    check.failed("Unexpected input binding - got {node}".format(node=node))

            dep_dict[
                SolidInvocation(
                    invocation.node_def.name,
                    invocation.node_name,
                    tags=invocation.tags,
                    hook_defs=invocation.hook_defs,
                )
            ] = deps

        return super(cls, CompleteCompositionContext).__new__(
            cls, name, list(node_def_dict.values()), dep_dict, input_mappings, output_mapping_dict
        )


class CallableNode:
    """An intermediate object in composition to allow for binding information such as
    an alias before invoking.
    """

    def __init__(self, node_def, given_alias=None, tags=None, hook_defs=None):
        self.node_def = check.inst_param(node_def, "node_def", NodeDefinition)
        self.given_alias = check.opt_str_param(given_alias, "given_alias")
        self.tags = check.opt_inst_param(tags, "tags", frozentags)
        self.hook_defs = check.opt_set_param(hook_defs, "hook_defs", HookDefinition)

        if _is_in_composition():
            current_context().add_pending_invocation(self)

    def __call__(self, *args, **kwargs):
        node_name = self.given_alias if self.given_alias else self.node_def.name
        assert_in_composition(node_name)

        input_bindings = {}

        # handle *args
        for idx, output_node in enumerate(args):
            if idx >= len(self.node_def.input_defs):
                raise DagsterInvalidDefinitionError(
                    "In {source} {name}, received too many inputs for "
                    "invocation {node_name}. Only {def_num} defined, received {arg_num}".format(
                        source=current_context().source,
                        name=current_context().name,
                        node_name=node_name,
                        def_num=len(self.node_def.input_defs),
                        arg_num=len(args),
                    )
                )

            input_name = self.node_def.resolve_input_name_at_position(idx)
            if input_name is None:
                raise DagsterInvalidDefinitionError(
                    "In {source} {name}, could not resolve input based on position at "
                    "index {idx} for invocation {node_name}. Use keyword args instead, "
                    "available inputs are: {inputs}".format(
                        idx=idx,
                        source=current_context().source,
                        name=current_context().name,
                        node_name=node_name,
                        inputs=list(map(lambda inp: inp.name, self.node_def.input_defs)),
                    )
                )

            self._process_argument_node(
                node_name,
                output_node,
                input_name,
                input_bindings,
                "(at position {idx})".format(idx=idx),
            )

        # then **kwargs
        for input_name, output_node in kwargs.items():
            self._process_argument_node(
                node_name,
                output_node,
                input_name,
                input_bindings,
                "(passed by keyword)",
            )

        # the node name is potentially reassigned for aliasing
        resolved_node_name = current_context().observe_invocation(
            self.given_alias,
            self.node_def,
            input_bindings,
            self.tags,
            self.hook_defs,
        )

        if len(self.node_def.output_defs) == 0:
            return None

        if len(self.node_def.output_defs) == 1:
            output_def = self.node_def.output_defs[0]
            output_name = output_def.name
            if output_def.is_dynamic:
                return InvokedSolidDynamicOutputWrapper(resolved_node_name, output_name)
            else:
                return InvokedSolidOutputHandle(resolved_node_name, output_name)

        outputs = [output_def for output_def in self.node_def.output_defs]
        invoked_output_handles = {}
        for output_def in outputs:
            if output_def.is_dynamic:
                invoked_output_handles[output_def.name] = InvokedSolidDynamicOutputWrapper(
                    resolved_node_name, output_def.name
                )
            else:
                invoked_output_handles[output_def.name] = InvokedSolidOutputHandle(
                    resolved_node_name, output_def.name
                )

        return namedtuple(
            "_{node_def}_outputs".format(node_def=self.node_def.name),
            " ".join([output_def.name for output_def in outputs]),
        )(**invoked_output_handles)

    def _process_argument_node(self, solid_name, output_node, input_name, input_bindings, arg_desc):

        if isinstance(output_node, (InvokedSolidOutputHandle, InputMappingNode)):
            input_bindings[input_name] = output_node

        elif isinstance(output_node, list):
            input_bindings[input_name] = []
            for idx, fanned_in_node in enumerate(output_node):
                if isinstance(fanned_in_node, (InvokedSolidOutputHandle, InputMappingNode)):
                    input_bindings[input_name].append(fanned_in_node)
                else:
                    raise DagsterInvalidDefinitionError(
                        "In {source} {name}, received a list containing an invalid type "
                        'at index {idx} for input "{input_name}" {arg_desc} in '
                        "solid invocation {solid_name}. Lists can only contain the "
                        "output from previous solid invocations or input mappings, "
                        "received {type}".format(
                            source=current_context().source,
                            name=current_context().name,
                            arg_desc=arg_desc,
                            input_name=input_name,
                            solid_name=solid_name,
                            idx=idx,
                            type=type(output_node),
                        )
                    )

        elif isinstance(output_node, tuple) and all(
            map(lambda item: isinstance(item, InvokedSolidOutputHandle), output_node)
        ):
            raise DagsterInvalidDefinitionError(
                "In {source} {name}, received a tuple of multiple outputs for "
                'input "{input_name}" {arg_desc} in solid invocation {solid_name}. '
                "Must pass individual output, available from tuple: {options}".format(
                    source=current_context().source,
                    name=current_context().name,
                    arg_desc=arg_desc,
                    input_name=input_name,
                    solid_name=solid_name,
                    options=output_node._fields,
                )
            )
        elif isinstance(output_node, InvokedSolidDynamicOutputWrapper):
            raise DagsterInvalidDefinitionError(
                f"In {current_context().source} {current_context().name}, received the dynamic output "
                f"{output_node.output_name} from solid {output_node.solid_name} directly. Dynamic "
                "output must be unpacked by invoking map."
            )

        elif isinstance(output_node, CallableNode) or isinstance(output_node, NodeDefinition):
            raise DagsterInvalidDefinitionError(
                "In {source} {name}, received an un-invoked solid for input "
                '"{input_name}" {arg_desc} in solid invocation "{solid_name}". '
                "Did you forget parentheses?".format(
                    source=current_context().source,
                    name=current_context().name,
                    arg_desc=arg_desc,
                    input_name=input_name,
                    solid_name=solid_name,
                )
            )
        else:
            raise DagsterInvalidDefinitionError(
                "In {source} {name}, received invalid type {type} for input "
                '"{input_name}" {arg_desc} in solid invocation "{solid_name}". '
                "Must pass the output from previous solid invocations or inputs to the "
                "composition function as inputs when invoking solids during composition.".format(
                    source=current_context().source,
                    name=current_context().name,
                    type=type(output_node),
                    arg_desc=arg_desc,
                    input_name=input_name,
                    solid_name=solid_name,
                )
            )

    def alias(self, name):
        return CallableNode(self.node_def, name, self.tags)

    def tag(self, tags):
        tags = validate_tags(tags)
        return CallableNode(
            self.node_def,
            self.given_alias,
            frozentags(tags) if self.tags is None else self.tags.updated_with(tags),
        )

    def with_hooks(self, hook_defs):
        hook_defs = check.set_param(hook_defs, "hook_defs", of_type=HookDefinition)
        return CallableNode(
            self.node_def, self.given_alias, self.tags, hook_defs.union(self.hook_defs)
        )


class InvokedNode(namedtuple("_InvokedNode", "node_name, node_def input_bindings tags hook_defs")):
    """The metadata about a solid invocation saved by the current composition context."""

    def __new__(cls, node_name, node_def, input_bindings, tags=None, hook_defs=None):
        return super(cls, InvokedNode).__new__(
            cls,
            check.str_param(node_name, "node_name"),
            check.inst_param(node_def, "node_def", NodeDefinition),
            check.dict_param(input_bindings, "input_bindings", key_type=str),
            check.opt_inst_param(tags, "tags", frozentags),
            check.opt_set_param(hook_defs, "hook_defs", HookDefinition),
        )


class InvokedSolidOutputHandle:
    """The return value for an output when invoking a solid in a composition function."""

    def __init__(self, solid_name, output_name):
        self.solid_name = check.str_param(solid_name, "solid_name")
        self.output_name = check.str_param(output_name, "output_name")

    def __iter__(self):
        raise DagsterInvariantViolationError(
            'Attempted to iterate over an {cls}. This object represents the output "{out}" '
            'from the solid "{solid}". Consider yielding multiple Outputs if you seek to pass '
            "different parts of this output to different solids.".format(
                cls=self.__class__.__name__, out=self.output_name, solid=self.solid_name
            )
        )

    def __getitem__(self, idx):
        raise DagsterInvariantViolationError(
            'Attempted to index in to an {cls}. This object represents the output "{out}" '
            'from the solid "{solid}". Consider yielding multiple Outputs if you seek to pass '
            "different parts of this output to different solids.".format(
                cls=self.__class__.__name__, out=self.output_name, solid=self.solid_name
            )
        )

    def alias(self, _):
        raise DagsterInvariantViolationError(
            "In {source} {name}, attempted to call alias method for {cls}. This object "
            'represents the output "{out}" from the already invoked solid "{solid}". Consider '
            "checking the location of parentheses.".format(
                source=current_context().source,
                name=current_context().name,
                cls=self.__class__.__name__,
                solid=self.solid_name,
                out=self.output_name,
            )
        )

    def with_hooks(self, _):
        raise DagsterInvariantViolationError(
            "In {source} {name}, attempted to call hook method for {cls}. This object "
            'represents the output "{out}" from the already invoked solid "{solid}". Consider '
            "checking the location of parentheses.".format(
                source=current_context().source,
                name=current_context().name,
                cls=self.__class__.__name__,
                solid=self.solid_name,
                out=self.output_name,
            )
        )


class InvokedSolidDynamicOutputWrapper:
    """
    The return value for a dynamic output when invoking a solid in a composition function.
    Must be unwrapped by invoking map.
    """

    def __init__(self, solid_name, output_name):
        self.solid_name = check.str_param(solid_name, "solid_name")
        self.output_name = check.str_param(output_name, "output_name")

    def map(self, fn):
        check.is_callable(fn)
        result = fn(InvokedSolidOutputHandle(self.solid_name, self.output_name))
        if isinstance(result, InvokedSolidOutputHandle):
            return InvokedSolidDynamicOutputWrapper(result.solid_name, result.output_name)
        elif isinstance(result, tuple) and all(
            map(lambda item: isinstance(item, InvokedSolidOutputHandle), result)
        ):
            return tuple(
                map(
                    lambda item: InvokedSolidDynamicOutputWrapper(
                        item.solid_name, item.output_name
                    ),
                    result,
                )
            )
        elif result is None:
            return None
        else:
            check.failed(
                f"Could not handle output from map function invoked on {self.solid_name}:{self.output_name}, received {result}"
            )

    def unwrap_for_composite_mapping(self):
        return InvokedSolidOutputHandle(self.solid_name, self.output_name)

    def __iter__(self):
        raise DagsterInvariantViolationError(
            'Attempted to iterate over an {cls}. This object represents the dynamic output "{out}" '
            'from the solid "{solid}". Use the "map" method on this object to create '
            "downstream dependencies that will be cloned for each DynamicOutput "
            "that is resolved at runtime.".format(
                cls=self.__class__.__name__, out=self.output_name, solid=self.solid_name
            )
        )

    def __getitem__(self, idx):
        raise DagsterInvariantViolationError(
            'Attempted to index in to an {cls}. This object represents the dynamic output "{out}" '
            'from the solid "{solid}". Use the "map" method on this object to create '
            "downstream dependencies that will be cloned for each DynamicOutput "
            "that is resolved at runtime.".format(
                cls=self.__class__.__name__, out=self.output_name, solid=self.solid_name
            )
        )

    def alias(self, _):
        raise DagsterInvariantViolationError(
            "In {source} {name}, attempted to call alias method for {cls}. This object "
            'represents the dynamic output "{out}" from the already invoked solid "{solid}". Consider '
            "checking the location of parentheses.".format(
                source=current_context().source,
                name=current_context().name,
                cls=self.__class__.__name__,
                solid=self.solid_name,
                out=self.output_name,
            )
        )

    def with_hooks(self, _):
        raise DagsterInvariantViolationError(
            "In {source} {name}, attempted to call hook method for {cls}. This object "
            'represents the dynamic output "{out}" from the already invoked solid "{solid}". Consider '
            "checking the location of parentheses.".format(
                source=current_context().source,
                name=current_context().name,
                cls=self.__class__.__name__,
                solid=self.solid_name,
                out=self.output_name,
            )
        )


class InputMappingNode:
    def __init__(self, input_def):
        self.input_def = input_def


def composite_mapping_from_output(output, output_defs, solid_name):
    # output can be different types
    check.list_param(output_defs, "output_defs", OutputDefinition)
    check.str_param(solid_name, "solid_name")

    # single output
    if isinstance(output, InvokedSolidOutputHandle):
        if len(output_defs) == 1:
            defn = output_defs[0]
            return {defn.name: defn.mapping_from(output.solid_name, output.output_name)}
        else:
            raise DagsterInvalidDefinitionError(
                "Returned a single output ({solid_name}.{output_name}) in "
                "@composite_solid {name} but {num} outputs are defined. "
                "Return a dict to map defined outputs.".format(
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
                    "Output name mismatch returning output tuple in @composite_solid {name}. "
                    "No matching OutputDefinition named {output_name} for {solid_name}.{output_name}."
                    "Return a dict to map to the desired OutputDefinition".format(
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
                    "@composite_solid {name} referenced key {key} which does not match any "
                    "OutputDefinitions. Valid options are: {options}".format(
                        name=solid_name, key=name, options=list(output_def_dict.keys())
                    )
                )

            if isinstance(handle, InvokedSolidOutputHandle):
                output_mapping_dict[name] = output_def_dict[name].mapping_from(
                    handle.solid_name, handle.output_name
                )
            elif isinstance(handle, InvokedSolidDynamicOutputWrapper):
                unwrapped = handle.unwrap_for_composite_mapping()
                output_mapping_dict[name] = output_def_dict[name].mapping_from(
                    unwrapped.solid_name, unwrapped.output_name
                )
            else:
                raise DagsterInvalidDefinitionError(
                    "@composite_solid {name} returned problematic dict entry under "
                    "key {key} of type {type}. Dict values must be outputs of "
                    "invoked solids".format(name=solid_name, key=name, type=type(handle))
                )

        return output_mapping_dict

    elif isinstance(output, InvokedSolidDynamicOutputWrapper):
        return composite_mapping_from_output(
            output.unwrap_for_composite_mapping(), output_defs, solid_name
        )

    # error
    if output is not None:
        raise DagsterInvalidDefinitionError(
            "@composite_solid {name} returned problematic value "
            "of type {type}. Expected return value from invoked solid or dict mapping "
            "output name to return values from invoked solids".format(
                name=solid_name, type=type(output)
            )
        )


def do_composition(
    decorator_name,
    graph_name,
    fn,
    provided_input_defs,
    provided_output_defs,
    config_schema,
    config_fn,
    ignore_output_from_composition_fn,
):
    """
    This a function used by both @pipeline and @composite_solid to implement their composition
    function which is our DSL for constructing a dependency graph.

    Args:
        decorator_name (str): Name of the calling decorator. e.g. "@pipeline",
            "@composite_solid", "@graph"
        graph_name (str): User-defined name of the definition being constructed
        fn (Callable): The composition function to be called.
        provided_input_defs(List[InputDefinition]): List of input definitions
            explicitly provided to the decorator by the user.
        provided_output_defs(List[OutputDefinition]): List of output definitions
            explicitly provided to the decorator by the user.
        config_schema(Any): Config schema provided to decorator by user.
        config_fn(Callable): Config fn provided to decorator by user.
        ignore_output_from_composite_fn(Bool): Because of backwards compatibility
            issues, pipelines ignore the return value out of the mapping if
            the user has not explicitly provided the output definitions.
            This should be removed in 0.11.0.
    """

    actual_input_defs = (
        provided_input_defs
        if provided_input_defs is not None
        else infer_input_definitions_for_graph(decorator_name, graph_name, fn)
    )

    actual_output_defs, outputs_are_explicit = (
        (provided_output_defs, True)
        if provided_output_defs is not None
        else (
            infer_output_definitions(decorator_name, graph_name, fn),
            has_explicit_return_type(fn),
        )
    )

    positional_inputs = validate_solid_fn(
        decorator_name, graph_name, fn, actual_input_defs, exclude_nothing=False
    )

    kwargs = {input_def.name: InputMappingNode(input_def) for input_def in actual_input_defs}

    output = None
    returned_mapping = None
    enter_composition(graph_name, decorator_name)
    try:
        output = fn(**kwargs)
        if ignore_output_from_composition_fn:
            if output is not None:
                warnings.warn(
                    "You have returned a value out of a @pipeline-decorated function. "
                    "This currently has no effect on behavior, but will after 0.11.0 is "
                    "released. In order to preserve existing behavior to do not return "
                    "anything out of this function. Pipelines (and its successor, graphs) "
                    "will have meaningful outputs just like composite solids do today, "
                    "and the return value will be meaningful.",
                    stacklevel=3,
                )
            output = None

        returned_mapping = composite_mapping_from_output(output, actual_output_defs, graph_name)
    finally:
        context = exit_composition(returned_mapping)

    check.invariant(
        context.name == graph_name,
        "Composition context stack desync: received context for "
        '"{context.name}" expected "{graph_name}"'.format(context=context, graph_name=graph_name),
    )

    # line up mappings in definition order
    input_mappings = []
    for defn in actual_input_defs:
        mappings = [
            mapping for mapping in context.input_mappings if mapping.definition.name == defn.name
        ]

        if len(mappings) == 0:
            raise DagsterInvalidDefinitionError(
                "{decorator_name} '{graph_name}' has unmapped input '{input_name}'. "
                "Remove it or pass it to the appropriate solid invocation.".format(
                    decorator_name=decorator_name, graph_name=graph_name, input_name=defn.name
                )
            )

        input_mappings += mappings

    output_mappings = []
    for defn in actual_output_defs:
        mapping = context.output_mapping_dict.get(defn.name)
        if mapping is None:
            # if we inferred output_defs we will be flexible and either take a mapping or not
            if not outputs_are_explicit:
                continue

            # if we are ignoring the output, disregard this unsatisfied mapping
            if ignore_output_from_composition_fn:
                continue

            raise DagsterInvalidDefinitionError(
                "{decorator_name} '{graph_name}' has unmapped output '{output_name}'. "
                "Remove it or return a value from the appropriate solid invocation.".format(
                    decorator_name=decorator_name, graph_name=graph_name, output_name=defn.name
                )
            )
        output_mappings.append(mapping)

    config_mapping = _get_validated_config_mapping(graph_name, config_schema, config_fn)

    return (
        input_mappings,
        output_mappings,
        context.dependencies,
        context.solid_defs,
        config_mapping,
        positional_inputs,
    )


def _get_validated_config_mapping(name, config_schema, config_fn):
    """Config mapping must set composite config_schema and config_fn or neither."""

    if config_fn is None and config_schema is None:
        return None
    elif config_fn is not None and config_schema is not None:
        return ConfigMapping(config_fn=config_fn, config_schema=config_schema)
    else:
        if config_fn is not None:
            raise DagsterInvalidDefinitionError(
                "@composite_solid '{solid_name}' defines a configuration function {config_fn} "
                "but does not define a configuration schema. If you intend this composite to take "
                "no config_schema, you must explicitly specify config_schema={{}}.".format(
                    solid_name=name, config_fn=config_fn.__name__
                )
            )
        else:
            raise DagsterInvalidDefinitionError(
                "@composite_solid '{solid_name}' defines a configuration schema but does not "
                "define a configuration function.".format(solid_name=name)
            )
