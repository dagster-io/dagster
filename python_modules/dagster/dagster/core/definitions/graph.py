from collections import OrderedDict

import six
from toposort import CircularDependencyError, toposort_flatten

from dagster import check
from dagster.core.definitions.config import ConfigMapping
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.types.dagster_type import DagsterTypeKind

from .dependency import DependencyStructure, Solid, SolidHandle
from .i_solid_definition import ISolidDefinition
from .input import InputDefinition, InputMapping
from .output import OutputDefinition, OutputMapping
from .solid_container import create_execution_structure, validate_dependency_dict


def _check_solids_arg(graph_name, solid_defs):
    if not isinstance(solid_defs, list):
        raise DagsterInvalidDefinitionError(
            '"solids" arg to "{name}" is not a list. Got {val}.'.format(
                name=graph_name, val=repr(solid_defs)
            )
        )
    for solid_def in solid_defs:
        if isinstance(solid_def, ISolidDefinition):
            continue
        elif callable(solid_def):
            raise DagsterInvalidDefinitionError(
                """You have passed a lambda or function {func} into {name} that is
                not a solid. You have likely forgetten to annotate this function with
                an @solid or @lambda_solid decorator.'
                """.format(
                    name=graph_name, func=solid_def.__name__
                )
            )
        else:
            raise DagsterInvalidDefinitionError(
                "Invalid item in solid list: {item}".format(item=repr(solid_def))
            )

    return solid_defs


def _create_adjacency_lists(solids, dep_structure):
    check.list_param(solids, "solids", Solid)
    check.inst_param(dep_structure, "dep_structure", DependencyStructure)

    visit_dict = {s.name: False for s in solids}
    forward_edges = {s.name: set() for s in solids}
    backward_edges = {s.name: set() for s in solids}

    def visit(solid_name):
        if visit_dict[solid_name]:
            return

        visit_dict[solid_name] = True

        for output_handle in dep_structure.all_upstream_outputs_from_solid(solid_name):
            forward_node = output_handle.solid.name
            backward_node = solid_name
            if forward_node in forward_edges:
                forward_edges[forward_node].add(backward_node)
                backward_edges[backward_node].add(forward_node)
                visit(forward_node)

    for s in solids:
        visit(s.name)

    return (forward_edges, backward_edges)


class GraphDefinition(ISolidDefinition):
    def __init__(
        self,
        name,
        description,
        solid_defs,
        dependencies,
        input_mappings,
        output_mappings,
        config_mapping,
        _configured_config_mapping_fn,
        _configured_config_schema,
        **kwargs
    ):
        self._solid_defs = _check_solids_arg(name, solid_defs)
        self._dependencies = validate_dependency_dict(dependencies)
        self._dependency_structure, self._solid_dict = create_execution_structure(
            solid_defs, self._dependencies, graph_definition=self
        )

        # List[InputMapping]
        self._input_mappings, input_defs = _validate_in_mappings(
            check.opt_list_param(input_mappings, "input_mappings"),
            self._solid_dict,
            name,
            class_name=type(self).__name__,
        )
        # List[OutputMapping]
        self._output_mappings = _validate_out_mappings(
            check.opt_list_param(output_mappings, "output_mappings"),
            self._solid_dict,
            name,
            class_name=type(self).__name__,
        )

        self._config_mapping = check.opt_inst_param(config_mapping, "config_mapping", ConfigMapping)

        self.__configured_config_mapping_fn = check.opt_callable_param(
            _configured_config_mapping_fn, "_configured_config_mapping_fn"
        )
        self.__configured_config_schema = _configured_config_schema

        super(GraphDefinition, self).__init__(
            name=name,
            description=description,
            input_defs=input_defs,
            output_defs=[output_mapping.definition for output_mapping in self._output_mappings],
            **kwargs
        )

        # must happen after base class construction as properties are assumed to be there
        # eager computation to detect cycles
        self.solids_in_topological_order = self._solids_in_topological_order()

    def _solids_in_topological_order(self):

        _forward_edges, backward_edges = _create_adjacency_lists(
            self.solids, self.dependency_structure
        )

        try:
            order = toposort_flatten(backward_edges)
        except CircularDependencyError as err:
            six.raise_from(
                DagsterInvalidDefinitionError(str(err)), err,
            )

        return [self.solid_named(solid_name) for solid_name in order]

    @property
    def solids(self):
        """List[Solid]: Top-level solids in the graph.
        """
        return list(set(self._solid_dict.values()))

    def has_solid_named(self, name):
        """Return whether or not there is a top level solid with this name in the graph.

        Args:
            name (str): Name of solid

        Returns:
            bool: True if the solid is in the graph.
        """
        check.str_param(name, "name")
        return name in self._solid_dict

    def solid_named(self, name):
        """Return the top level solid named "name". Throws if it does not exist.

        Args:
            name (str): Name of solid

        Returns:
            Solid:
        """
        check.str_param(name, "name")
        check.invariant(
            name in self._solid_dict,
            "{graph_name} has no solid named {name}.".format(graph_name=self._name, name=name),
        )

        return self._solid_dict[name]

    def get_solid(self, handle):
        """Return the solid contained anywhere within the graph via its handle.

        Args:
            handle (SolidHandle): The solid's handle

        Returns:
            Solid:

        """
        check.inst_param(handle, "handle", SolidHandle)
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

    def iterate_solid_defs(self):
        yield self
        for outer_solid_def in self._solid_defs:
            for solid_def in outer_solid_def.iterate_solid_defs():
                yield solid_def

    @property
    def input_mappings(self):
        return self._input_mappings

    @property
    def output_mappings(self):
        return self._output_mappings

    @property
    def config_mapping(self):
        return self._config_mapping

    @property
    def has_config_mapping(self):
        return self._config_mapping is not None

    def get_input_mapping(self, input_name):
        check.str_param(input_name, "input_name")
        for mapping in self._input_mappings:
            if mapping.definition.name == input_name:
                return mapping
        return None

    def mapped_input(self, solid_name, input_name):
        check.str_param(solid_name, "solid_name")
        check.str_param(input_name, "input_name")

        for mapping in self._input_mappings:
            if mapping.solid_name == solid_name and mapping.input_name == input_name:
                return mapping
        return None

    def get_output_mapping(self, output_name):
        check.str_param(output_name, "output_name")
        for mapping in self._output_mappings:
            if mapping.definition.name == output_name:
                return mapping
        return None

    def resolve_output_to_origin(self, output_name, handle):
        check.str_param(output_name, "output_name")
        check.inst_param(handle, "handle", SolidHandle)

        mapping = self.get_output_mapping(output_name)
        check.invariant(mapping, "Can only resolve outputs for valid output names")
        mapped_solid = self.solid_named(mapping.solid_name)
        return mapped_solid.definition.resolve_output_to_origin(
            mapping.output_name, SolidHandle(mapped_solid.name, handle),
        )

    def default_value_for_input(self, input_name):
        check.str_param(input_name, "input_name")

        # base case
        if self.input_def_named(input_name).has_default_value:
            return self.input_def_named(input_name).default_value

        mapping = self.get_input_mapping(input_name)
        check.invariant(mapping, "Can only resolve inputs for valid input names")
        mapped_solid = self.solid_named(mapping.solid_name)

        return mapped_solid.definition.default_value_for_input(mapping.input_name)

    def input_has_default(self, input_name):
        check.str_param(input_name, "input_name")

        # base case
        if self.input_def_named(input_name).has_default_value:
            return True

        mapping = self.get_input_mapping(input_name)
        check.invariant(mapping, "Can only resolve inputs for valid input names")
        mapped_solid = self.solid_named(mapping.solid_name)

        return mapped_solid.definition.input_has_default(mapping.input_name)

    @property
    def required_resource_keys(self):
        required_resource_keys = set()
        for solid in self.solids:
            required_resource_keys.update(solid.definition.required_resource_keys)
        return frozenset(required_resource_keys)

    @property
    def has_config_entry(self):
        has_child_solid_config = any([solid.definition.has_config_entry for solid in self.solids])
        return (
            self.has_config_mapping
            or has_child_solid_config
            or self.has_configurable_inputs
            or self.has_configurable_outputs
        )

    @property
    def dependencies(self):
        return self._dependencies

    @property
    def dependency_structure(self):
        return self._dependency_structure

    @property
    def config_schema(self):
        if self.is_preconfigured:
            return self.__configured_config_schema
        elif self.has_config_mapping:
            return self.config_mapping.config_schema

    @property
    def _configured_config_mapping_fn(self):
        return self.__configured_config_mapping_fn

    def configured(self, config_or_config_fn, config_schema=None, **kwargs):
        """
        Returns a new :py:class:`GraphDefinition` (PipelineDefinition or
        CompositeSolidDefinition depending whether self is a pipeline or a composite
        solid, respectively) that bundles this definition with the specified config
        or config function.

        For remainder of docblock "graph" should be interpreted as "pipeline or composite solid"

        Args:
            config_or_config_fn (Union[Any, Callable[[Any], Any]]): Either (1) Run configuration
                that fully satisfies this graph's config schema or (2) A
                function that accepts run configuration and returns run configuration that
                fully satisfies this graph's config schema.  In the latter case,
                config_schema must be specified.  When passing a function, it's easiest to
                use :py:func:`configured`.
            config_schema (ConfigSchema): If config_or_config_fn is a function, the config schema
                that its input must satisfy.
            name (str): Name of the new (configured) graph. Must be unique within the
                contained graph.
            **kwargs: Arbitrary keyword arguments that will be passed to the initializer of the
                returned graph.

        Returns (GraphDefinition): A configured version of this graph definition.
        """
        if not self.has_config_mapping:
            raise DagsterInvalidDefinitionError(
                "Only composite solids utilizing config mapping can be pre-configured. The solid "
                '"{graph_name}" does not have a config mapping, and thus has nothing to be '
                "configured.".format(graph_name=self.name)
            )

        fn_name = config_or_config_fn.__name__ if callable(config_or_config_fn) else None
        name = kwargs.get("name", fn_name)
        if not name:
            raise DagsterInvalidDefinitionError(
                'Missing string param "name" while attempting to configure the graph '
                '"{graph_name}". When configuring a solid, you must specify a name for the '
                "resulting solid definition as a keyword param or use `configured` in decorator "
                "form. For examples, visit https://docs.dagster.io/overview/configuration#configured.".format(
                    graph_name=self.name
                )
            )

        wrapped_config_mapping_fn = self._get_wrapped_config_mapping_fn(
            config_or_config_fn, config_schema
        )

        return self.construct_configured_copy(
            new_name=name,
            new_description=kwargs.get("description", self.description),
            new_configured_config_schema=config_schema,
            new_configured_config_mapping_fn=wrapped_config_mapping_fn,
        )

    def construct_configured_copy(
        self,
        new_name,
        new_description,
        new_configured_config_schema,
        new_configured_config_mapping_fn,
    ):
        raise NotImplementedError()


def _validate_in_mappings(input_mappings, solid_dict, name, class_name):
    input_def_dict = OrderedDict()
    for mapping in input_mappings:
        if isinstance(mapping, InputMapping):
            if input_def_dict.get(mapping.definition.name):
                if input_def_dict[mapping.definition.name] != mapping.definition:
                    raise DagsterInvalidDefinitionError(
                        "In {class_name} {name} multiple input mappings with same "
                        "definition name but different definitions".format(
                            name=name, class_name=class_name
                        ),
                    )
            else:
                input_def_dict[mapping.definition.name] = mapping.definition

            target_solid = solid_dict.get(mapping.solid_name)
            if target_solid is None:
                raise DagsterInvalidDefinitionError(
                    "In {class_name} '{name}' input mapping references solid "
                    "'{solid_name}' which it does not contain.".format(
                        name=name, solid_name=mapping.solid_name, class_name=class_name
                    )
                )
            if not target_solid.has_input(mapping.input_name):
                raise DagsterInvalidDefinitionError(
                    "In {class_name} '{name}' input mapping to solid '{mapping.solid_name}' "
                    "which contains no input named '{mapping.input_name}'".format(
                        name=name, mapping=mapping, class_name=class_name
                    )
                )

            target_input = target_solid.input_def_named(mapping.input_name)
            if target_input.dagster_type != mapping.definition.dagster_type:
                raise DagsterInvalidDefinitionError(
                    "In {class_name} '{name}' input "
                    "'{mapping.definition.name}' of type {mapping.definition.dagster_type.display_name} maps to "
                    "{mapping.solid_name}.{mapping.input_name} of different type "
                    "{target_input.dagster_type.display_name}. InputMapping source and "
                    "destination must have the same type.".format(
                        mapping=mapping, name=name, target_input=target_input, class_name=class_name
                    )
                )

        elif isinstance(mapping, InputDefinition):
            raise DagsterInvalidDefinitionError(
                "In {class_name} '{name}' you passed an InputDefinition "
                "named '{input_name}' directly in to input_mappings. Return "
                "an InputMapping by calling mapping_to on the InputDefinition.".format(
                    name=name, input_name=mapping.name, class_name=class_name
                )
            )
        else:
            raise DagsterInvalidDefinitionError(
                "In {class_name} '{name}' received unexpected type '{type}' in input_mappings. "
                "Provide an OutputMapping using InputDefinition(...).mapping_to(...)".format(
                    type=type(mapping), name=name, class_name=class_name
                )
            )

    return input_mappings, input_def_dict.values()


def _validate_out_mappings(output_mappings, solid_dict, name, class_name):
    for mapping in output_mappings:
        if isinstance(mapping, OutputMapping):

            target_solid = solid_dict.get(mapping.solid_name)
            if target_solid is None:
                raise DagsterInvalidDefinitionError(
                    "In {class_name} '{name}' output mapping references solid "
                    "'{solid_name}' which it does not contain.".format(
                        name=name, solid_name=mapping.solid_name, class_name=class_name
                    )
                )
            if not target_solid.has_output(mapping.output_name):
                raise DagsterInvalidDefinitionError(
                    "In {class_name} {name} output mapping from solid '{mapping.solid_name}' "
                    "which contains no output named '{mapping.output_name}'".format(
                        name=name, mapping=mapping, class_name=class_name
                    )
                )

            target_output = target_solid.output_def_named(mapping.output_name)

            if mapping.definition.dagster_type.kind != DagsterTypeKind.ANY and (
                target_output.dagster_type != mapping.definition.dagster_type
            ):
                raise DagsterInvalidDefinitionError(
                    "In {class_name} '{name}' output "
                    "'{mapping.definition.name}' of type {mapping.definition.dagster_type.display_name} "
                    "maps from {mapping.solid_name}.{mapping.output_name} of different type "
                    "{target_output.dagster_type.display_name}. OutputMapping source "
                    "and destination must have the same type.".format(
                        class_name=class_name,
                        mapping=mapping,
                        name=name,
                        target_output=target_output,
                    )
                )

        elif isinstance(mapping, OutputDefinition):
            raise DagsterInvalidDefinitionError(
                "You passed an OutputDefinition named '{output_name}' directly "
                "in to output_mappings. Return an OutputMapping by calling "
                "mapping_from on the OutputDefinition.".format(output_name=mapping.name)
            )
        else:
            raise DagsterInvalidDefinitionError(
                "Received unexpected type '{type}' in output_mappings. "
                "Provide an OutputMapping using OutputDefinition(...).mapping_from(...)".format(
                    type=type(mapping)
                )
            )
    return output_mappings
