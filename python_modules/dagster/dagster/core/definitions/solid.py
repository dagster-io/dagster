from dagster import check
from dagster.config.field_utils import check_user_facing_opt_config_param
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.utils.backcompat import experimental_arg_warning, rename_warning

from .graph import GraphDefinition
from .i_solid_definition import ISolidDefinition
from .input import InputDefinition
from .output import OutputDefinition


class SolidDefinition(ISolidDefinition):
    """
    The definition of a Solid that performs a user-defined computation.

    For more details on what a solid is, refer to the
    `Solid Guide <../../learn/guides/solid/solid>`_ .

    End users should prefer the :func:`@solid <solid>` and :func:`@lambda_solid <lambda_solid>`
    decorators. SolidDefinition is generally intended to be used by framework authors.

    Args:
        name (str): Name of the solid. Must be unique within any :py:class:`PipelineDefinition`
            using the solid.
        input_defs (List[InputDefinition]): Inputs of the solid.
        compute_fn (Callable): The core of the solid, the function that does the actual
            computation. The signature of this function is determined by ``input_defs``, with
            an additional injected first argument, ``context``, a collection of information provided
            by the system.

            This function must return a generator, which must yield one :py:class:`Output` for each
            of the solid's ``output_defs``, and additionally may yield other types of Dagster
            events, including :py:class:`Materialization` and :py:class:`ExpectationResult`.
        output_defs (List[OutputDefinition]): Outputs of the solid.
        config_schema (Optional[ConfigSchema): The schema for the config. Configuration data
            available in `init_context.solid_config`.
        description (Optional[str]): Human-readable description of the solid.
        tags (Optional[Dict[str, Any]]): Arbitrary metadata for the solid. Frameworks may
            expect and require certain metadata to be attached to a solid. Users should generally
            not set metadata directly. Values that are not strings will be json encoded and must meet
            the criteria that `json.loads(json.dumps(value)) == value`.
        required_resource_keys (Optional[Set[str]]): Set of resources handles required by this
            solid.
        positional_inputs (Optional[List[str]]): The positional order of the input names if it
            differs from the order of the input definitions.
        version (Optional[str]): (Experimental) The version of the solid's compute_fn. Two solids should have
            the same version if and only if they deterministically produce the same outputs when
            provided the same inputs.
        _configured_config_mapping_fn: This argument is for internal use only. Users should not
            specify this field. To preconfigure a resource, use the :py:func:`configured` API.


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
    """

    def __init__(
        self,
        name,
        input_defs,
        compute_fn,
        output_defs,
        config_schema=None,
        description=None,
        tags=None,
        required_resource_keys=None,
        positional_inputs=None,
        version=None,
        _configured_config_mapping_fn=None,
    ):
        self._compute_fn = check.callable_param(compute_fn, "compute_fn")
        self._config_schema = check_user_facing_opt_config_param(config_schema, "config_schema")
        self._required_resource_keys = frozenset(
            check.opt_set_param(required_resource_keys, "required_resource_keys", of_type=str)
        )
        self.__configured_config_mapping_fn = check.opt_callable_param(
            _configured_config_mapping_fn, "config_mapping_fn"
        )
        self._version = check.opt_str_param(version, "version")
        if version:
            experimental_arg_warning("version", "SolidDefinition.__init__")

        super(SolidDefinition, self).__init__(
            name=name,
            input_defs=check.list_param(input_defs, "input_defs", InputDefinition),
            output_defs=check.list_param(output_defs, "output_defs", OutputDefinition),
            description=description,
            tags=check.opt_dict_param(tags, "tags", key_type=str),
            positional_inputs=positional_inputs,
        )

    @property
    def compute_fn(self):
        return self._compute_fn

    @property
    def config_field(self):
        rename_warning("config_schema", "config_field", "0.9.0")
        return self._config_schema

    @property
    def config_schema(self):
        return self._config_schema

    @property
    def required_resource_keys(self):
        return frozenset(self._required_resource_keys)

    @property
    def has_config_entry(self):
        return self._config_schema or self.has_configurable_inputs or self.has_configurable_outputs

    @property
    def version(self):
        return self._version

    def all_dagster_types(self):
        for tt in self.all_input_output_types():
            yield tt

    def iterate_solid_defs(self):
        yield self

    def resolve_output_to_origin(self, output_name, handle):
        return self.output_def_named(output_name), handle

    def input_has_default(self, input_name):
        return self.input_def_named(input_name).has_default_value

    def default_value_for_input(self, input_name):
        return self.input_def_named(input_name).default_value

    @property
    def _configured_config_mapping_fn(self):
        return self.__configured_config_mapping_fn

    def configured(self, config_or_config_fn, config_schema=None, **kwargs):
        """
        Returns a new :py:class:`SolidDefinition` that bundles this definition with the specified
        config or config function.

        Args:
            config_or_config_fn (Union[Any, Callable[[Any], Any]]): Either (1) Run configuration
                that fully satisfies this solid's config schema or (2) A function that accepts run
                configuration and returns run configuration that fully satisfies this solid's
                config schema.  In the latter case, config_schema must be specified.  When
                passing a function, it's easiest to use :py:func:`configured`.
            config_schema (ConfigSchema): If config_or_config_fn is a function, the config schema
                that its input must satisfy.
            name (str): Name of the new (configured) solid. Must be unique within any
                :py:class:`PipelineDefinition` using the solid.

        Returns (SolidDefinition): A configured version of this solid definition.
        """

        fn_name = config_or_config_fn.__name__ if callable(config_or_config_fn) else None
        name = kwargs.get("name", fn_name)
        if not name:
            raise DagsterInvalidDefinitionError(
                'Missing string param "name" while attempting to configure the solid '
                '"{solid_name}". When configuring a solid, you must specify a name for the '
                "resulting solid definition as a keyword param or use `configured` in decorator "
                "form. For examples, visit https://docs.dagster.io/overview/configuration#configured.".format(
                    solid_name=self.name
                )
            )

        wrapped_config_mapping_fn = self._get_wrapped_config_mapping_fn(
            config_or_config_fn, config_schema
        )

        return SolidDefinition(
            name=name,
            input_defs=self.input_defs,
            compute_fn=self.compute_fn,
            output_defs=self.output_defs,
            config_schema=config_schema,
            description=kwargs.get("description", self.description),
            tags=self.tags,
            required_resource_keys=self.required_resource_keys,
            positional_inputs=self.positional_inputs,
            version=self.version,
            _configured_config_mapping_fn=wrapped_config_mapping_fn,
        )


class CompositeSolidDefinition(GraphDefinition):
    """The core unit of composition and abstraction, composite solids allow you to
    define a solid from a graph of solids.

    In the same way you would refactor a block of code in to a function to deduplicate, organize,
    or manage complexity - you can refactor solids in a pipeline in to a composite solid.

    Args:
        name (str): The name of this composite solid. Must be unique within any
            :py:class:`PipelineDefinition` using the solid.
        solid_defs (List[Union[SolidDefinition, CompositeSolidDefinition]]): The set of solid
            definitions used in this composite solid. Composites may be arbitrarily nested.
        input_mappings (Optional[List[InputMapping]]): Define the inputs to the composite solid,
            and how they map to the inputs of its constituent solids.
        output_mappings (Optional[List[OutputMapping]]): Define the outputs of the composite solid,
            and how they map from the outputs of its constituent solids.
        config_mapping (Optional[ConfigMapping]): By specifying a config mapping, you can override
            the configuration for the child solids contained within this composite solid. Config
            mappings require both a configuration field to be specified, which is exposed as the
            configuration for the composite solid, and a configuration mapping function, which
            is called to map the configuration of the composite solid into the configuration that
            is applied to any child solids.
        dependencies (Optional[Dict[Union[str, SolidInvocation], Dict[str, DependencyDefinition]]]):
            A structure that declares where each solid gets its inputs. The keys at the top
            level dict are either string names of solids or SolidInvocations. The values
            are dicts that map input names to DependencyDefinitions.
        description (Optional[str]): Human readable description of this composite solid.
        tags (Optional[Dict[str, Any]]): Arbitrary metadata for the solid. Frameworks may
            expect and require certain metadata to be attached to a solid. Users should generally
            not set metadata directly. Values that are not strings will be json encoded and must meet
            the criteria that `json.loads(json.dumps(value)) == value`.
            may expect and require certain metadata to be attached to a solid.
        positional_inputs (Optional[List[str]]): The positional order of the inputs if it
            differs from the order of the input mappings

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
    """

    def __init__(
        self,
        name,
        solid_defs,
        input_mappings=None,
        output_mappings=None,
        config_mapping=None,
        dependencies=None,
        description=None,
        tags=None,
        positional_inputs=None,
        _configured_config_mapping_fn=None,
        _configured_config_schema=None,
    ):
        super(CompositeSolidDefinition, self).__init__(
            name=name,
            description=description,
            solid_defs=solid_defs,
            dependencies=dependencies,
            tags=tags,
            positional_inputs=positional_inputs,
            input_mappings=input_mappings,
            output_mappings=output_mappings,
            config_mapping=config_mapping,
            _configured_config_mapping_fn=_configured_config_mapping_fn,
            _configured_config_schema=_configured_config_schema,
        )

    def all_dagster_types(self):
        for tt in self.all_input_output_types():
            yield tt

        for solid_def in self._solid_defs:
            for ttype in solid_def.all_dagster_types():
                yield ttype

    def construct_configured_copy(
        self,
        new_name,
        new_description,
        new_configured_config_schema,
        new_configured_config_mapping_fn,
    ):
        return CompositeSolidDefinition(
            name=new_name,
            solid_defs=self._solid_defs,
            input_mappings=self.input_mappings,
            output_mappings=self.output_mappings,
            config_mapping=self.config_mapping,
            dependencies=self.dependencies,
            description=new_description,
            tags=self.tags,
            positional_inputs=self.positional_inputs,
            _configured_config_schema=new_configured_config_schema,
            _configured_config_mapping_fn=new_configured_config_mapping_fn,
        )
