from abc import ABCMeta, abstractproperty, abstractmethod

import six

from dagster import check
from dagster.core.definitions.config import ConfigMapping
from dagster.core.types.field_utils import check_user_facing_opt_field_param
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.utils import frozendict, frozenlist

from .input import InputDefinition, InputMapping
from .output import OutputDefinition, OutputMapping
from .utils import check_valid_name
from .container import IContainSolids, create_execution_structure, validate_dependency_dict


class ISolidDefinition(six.with_metaclass(ABCMeta)):
    def __init__(self, name, input_defs, output_defs, description=None, metadata=None):
        self._name = check_valid_name(name)
        self._description = check.opt_str_param(description, 'description')
        self._metadata = check.opt_dict_param(metadata, 'metadata', key_type=str)
        self._input_defs = frozenlist(input_defs)
        self._input_dict = frozendict({input_def.name: input_def for input_def in input_defs})
        self._output_defs = frozenlist(output_defs)
        self._output_dict = frozendict({output_def.name: output_def for output_def in output_defs})

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def metadata(self):
        return self._metadata

    @property
    def input_defs(self):
        return self._input_defs

    @property
    def input_dict(self):
        return self._input_dict

    @property
    def output_defs(self):
        return self._output_defs

    @property
    def output_dict(self):
        return self._output_dict

    def has_input(self, name):
        check.str_param(name, 'name')
        return name in self._input_dict

    def input_def_named(self, name):
        check.str_param(name, 'name')
        return self._input_dict[name]

    def has_output(self, name):
        check.str_param(name, 'name')
        return name in self._output_dict

    def output_def_named(self, name):
        check.str_param(name, 'name')
        return self._output_dict[name]

    @property
    def has_configurable_inputs(self):
        return any([inp.runtime_type.input_hydration_config for inp in self._input_defs])

    @property
    def has_configurable_outputs(self):
        return any([out.runtime_type.output_materialization_config for out in self._output_defs])

    @abstractproperty
    def has_config_entry(self):
        raise NotImplementedError()

    @abstractmethod
    def iterate_solid_defs(self):
        raise NotImplementedError()

    @abstractmethod
    def resolve_output_to_origin(self, output_name):
        raise NotImplementedError()

    def all_input_output_types(self):
        for input_def in self._input_defs:
            yield input_def.runtime_type
            for inner_type in input_def.runtime_type.inner_types:
                yield inner_type

        for output_def in self._output_defs:
            yield output_def.runtime_type
            for inner_type in output_def.runtime_type.inner_types:
                yield inner_type

    def __call__(self, *args, **kwargs):
        from .composition import CallableSolidNode

        return CallableSolidNode(self)(*args, **kwargs)

    def alias(self, name):
        from .composition import CallableSolidNode

        return CallableSolidNode(self, name)


class SolidDefinition(ISolidDefinition):
    '''
    The definition of a Solid that peforms a user defined computation.

    For more details on what a solid is, reference the
    `Solid Guide <../../learn/guides/solid/solid.html>`_ .

    End users should prefer the :py:func:`solid` and :py:func:`lambda_solid`
    decorators. SolidDefinition is generally used by framework authors.

    Args:
        name (str): Name of the solid.
        input_defs (List[InputDefinition]): Inputs of the solid.

        compute_fn (Callable):
            The core of the solid, the function that does the actual computation. The signature of
            this function is determined by ``input_defs``, with the first argument always being
            ``context``, a collection of information provided by the system.

            This function must return a Generator, yielding :py:class:`Output` according to its
            ``output_defs`` and may yield other types of dagster events including
            :py:class:`Materialization` and :py:class:`ExpectationResult`.

        output_defs (List[OutputDefinition]): Outputs of the solid.
        config_field (Optional[Field]): How the solid configured.
        description (Optional[str]): Description of the solid.
        metadata (Optional[Dict[Any, Any]]):
            Arbitrary metadata for the solid. Some frameworks expect and require
            certain metadata to be attached to a solid.
        required_resource_keys (Optional[Set[str]]): List of resources handles required by this solid.

    Examples:
        .. code-block:: python

            def _add_one(_context, inputs):
                yield Output(inputs["num"] + 1)

            SolidDefinition(
                name="add_one",
                input_defs=[InputDefinition("num", Int)],
                output_defs=[OutputDefinition(Int)], # default name ("result")
                compute_fn=_add_one,
            )
    '''

    def __init__(
        self,
        name,
        input_defs,
        compute_fn,
        output_defs,
        config_field=None,
        description=None,
        metadata=None,
        required_resource_keys=None,
        step_metadata_fn=None,
    ):
        self._compute_fn = check.callable_param(compute_fn, 'compute_fn')
        self._config_field = check_user_facing_opt_field_param(
            config_field,
            'config_field',
            'of a SolidDefinition or @solid named "{name}"'.format(name=name),
        )
        self._required_resource_keys = check.opt_set_param(
            required_resource_keys, 'required_resource_keys', of_type=str
        )
        self._step_metadata_fn = step_metadata_fn

        super(SolidDefinition, self).__init__(
            name=name,
            input_defs=check.list_param(input_defs, 'input_defs', InputDefinition),
            output_defs=check.list_param(output_defs, 'output_defs', OutputDefinition),
            description=description,
            metadata=metadata,
        )

    @property
    def compute_fn(self):
        return self._compute_fn

    @property
    def config_field(self):
        return self._config_field

    @property
    def required_resource_keys(self):
        return self._required_resource_keys

    @property
    def step_metadata_fn(self):
        return self._step_metadata_fn

    @property
    def has_config_entry(self):
        return self._config_field or self.has_configurable_inputs or self.has_configurable_outputs

    def all_runtime_types(self):
        for tt in self.all_input_output_types():
            yield tt

    def iterate_solid_defs(self):
        yield self

    def resolve_output_to_origin(self, output_name):
        return self.output_def_named(output_name)


class CompositeSolidDefinition(ISolidDefinition, IContainSolids):
    '''
    The core unit of composition and abstraction, composite solids allow you to
    define a solid from a graph of solids.

    In the same way you would refactor a block of code in to a function to deduplicate, organize,
    or manage complexity - you can refactor solids in a pipeline in to a composite solid.

    Args:
        name (str)
        solid_defs (List[ISolidDefinition]):
            The set of solid definitions used in this composite
        input_mappings (List[InputMapping]):
            Define inputs and how they map to the constituent solids within.
        output_mappings (List[OutputMapping]):
            Define outputs and how they map from the constituent solids within.
        config_mapping (ConfigMapping):
            By specifying a config mapping, you can override the configuration for child solids
            contained within this composite solid. Config mappings require both a configuration
            field to be specified, which is exposed as the configuration for this composite solid,
            and a configuration mapping function, which maps the parent configuration of this solid
            into a configuration that is applied to any child solids.
        dependencies (Optional[Dict[Union[str, SolidInvocation], Dict[str, DependencyDefinition]]]):
            A structure that declares where each solid gets its inputs. The keys at the top
            level dict are either string names of solids or SolidInvocations. The values
            are dicts that map input names to DependencyDefinitions.
        description (Optional[str])
        metadata (Optional[Dict[Any, Any]]):
            Arbitrary metadata for the solid. Some frameworks expect and require
            certain metadata to be attached to a solid.

    Examples:

        .. code-block:: python

            @lambda_solid
            def add_one(num: int) -> int:
                return num + 1

            add_two = CompositeSolidDefinition(
                'add_two',
                solid_defs=[add_one],
                dependencies={
                    SolidInvocation('add_one', 'adder_1'): {},
                    SolidInvocation('add_one', 'adder_2'): {'num': DependencyDefinition('adder_1')},
                },
                input_mappings=[InputDefinition('num', Int).mapping_to('adder_1', 'num')],
                output_mappings=[OutputDefinition(Int).mapping_from('adder_2')],
            )
    '''

    def __init__(
        self,
        name,
        solid_defs,
        input_mappings=None,
        output_mappings=None,
        config_mapping=None,
        dependencies=None,
        description=None,
        metadata=None,
    ):
        check.list_param(solid_defs, 'solid_defs', of_type=ISolidDefinition)

        # List[InputMapping]
        self._input_mappings = _validate_in_mappings(
            check.opt_list_param(input_mappings, 'input_mappings')
        )
        # List[OutputMapping]
        self._output_mappings = _validate_out_mappings(
            check.opt_list_param(output_mappings, 'output_mappings')
        )

        self._config_mapping = check.opt_inst_param(config_mapping, 'config_mapping', ConfigMapping)

        self._dependencies = validate_dependency_dict(dependencies)
        dependency_structure, pipeline_solid_dict = create_execution_structure(
            solid_defs, self._dependencies, container_definition=self
        )

        self._solid_dict = pipeline_solid_dict
        self._dependency_structure = dependency_structure

        input_defs = [input_mapping.definition for input_mapping in self._input_mappings]

        output_defs = [output_mapping.definition for output_mapping in self._output_mappings]

        self._solid_defs = solid_defs

        super(CompositeSolidDefinition, self).__init__(
            name=name,
            input_defs=input_defs,
            output_defs=output_defs,
            description=description,
            metadata=metadata,
        )

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
    def depencencies(self):
        return self._dependencies

    def iterate_solid_defs(self):
        yield self
        for outer_solid_def in self._solid_defs:
            for solid_def in outer_solid_def.iterate_solid_defs():
                yield solid_def

    @property
    def solids(self):
        return list(self._solid_dict.values())

    def solid_named(self, name):
        return self._solid_dict[name]

    @property
    def dependency_structure(self):
        return self._dependency_structure

    @property
    def required_resource_keys(self):
        required_resource_keys = set()
        for solid in self.solids:
            required_resource_keys.update(solid.definition.required_resource_keys)

        return required_resource_keys

    @property
    def has_config_mapping(self):
        return self._config_mapping is not None

    @property
    def has_config_entry(self):
        has_solid_config = any([solid.definition.has_config_entry for solid in self.solids])
        return (
            self.has_config_mapping
            or has_solid_config
            or self.has_configurable_inputs
            or self.has_configurable_outputs
        )

    def mapped_input(self, solid_name, input_name):
        for mapping in self._input_mappings:
            if mapping.solid_name == solid_name and mapping.input_name == input_name:
                return mapping
        return None

    def get_output_mapping(self, output_name):
        for mapping in self._output_mappings:
            if mapping.definition.name == output_name:
                return mapping
        return None

    def resolve_output_to_origin(self, output_name):
        mapping = self.get_output_mapping(output_name)
        check.invariant(mapping, 'Can only resolve outputs for valid output names')
        return self.solid_named(mapping.solid_name).definition.resolve_output_to_origin(
            mapping.output_name
        )

    def all_runtime_types(self):
        for tt in self.all_input_output_types():
            yield tt

        for solid_def in self._solid_defs:
            for ttype in solid_def.all_runtime_types():
                yield ttype


def _validate_in_mappings(input_mappings):
    for mapping in input_mappings:
        if isinstance(mapping, InputMapping):
            continue
        elif isinstance(mapping, InputDefinition):
            raise DagsterInvalidDefinitionError(
                "You passed an InputDefinition named '{input_name}' directly "
                "in to input_mappings. Return an InputMapping by calling "
                "mapping_to on the InputDefinition.".format(input_name=mapping.name)
            )
        else:
            raise DagsterInvalidDefinitionError(
                "Received unexpected type '{type}' in output_mappings. "
                "Provide an OutputMapping using InputDefinition(...).mapping_to(...)".format(
                    type=type(mapping)
                )
            )

    return input_mappings


def _validate_out_mappings(output_mappings):
    for mapping in output_mappings:
        if isinstance(mapping, OutputMapping):
            continue
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
