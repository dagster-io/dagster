from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Dict,
    FrozenSet,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

import dagster._check as check
from dagster.config.config_schema import ConfigSchemaType
from dagster.core.definitions.dependency import NodeHandle
from dagster.core.definitions.policy import RetryPolicy
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvalidInvocationError
from dagster.core.types.dagster_type import DagsterType
from dagster.utils.backcompat import experimental_arg_warning

from ..decorator_utils import get_function_params
from .config import ConfigMapping
from .definition_config_schema import (
    IDefinitionConfigSchema,
    convert_user_facing_definition_config_schema,
)
from .dependency import IDependencyDefinition, NodeHandle, NodeInvocation
from .graph_definition import GraphDefinition
from .input import InputDefinition, InputMapping
from .node_definition import NodeDefinition
from .output import OutputDefinition, OutputMapping
from .solid_invocation import solid_invocation_result

if TYPE_CHECKING:
    from .decorators.solid_decorator import DecoratedSolidFunction


class SolidDefinition(NodeDefinition):
    """
    The definition of a Solid that performs a user-defined computation.

    For more details on what a solid is, refer to the
    `Solid Overview <../../overview/solids-pipelines/solids>`_ .

    End users should prefer the :func:`@solid <solid>` and :func:`@lambda_solid <lambda_solid>`
    decorators. SolidDefinition is generally intended to be used by framework authors.

    Args:
        name (str): Name of the solid. Must be unique within any :py:class:`PipelineDefinition`
            using the solid.
        input_defs (List[InputDefinition]): Inputs of the solid.
        compute_fn (Callable): The core of the solid, the function that does the actual
            computation. The signature of this function is determined by ``input_defs``, and
            optionally, an injected first argument, ``context``, a collection of information provided
            by the system.

            This function will be coerced into a generator or an async generator, which must yield
            one :py:class:`Output` for each of the solid's ``output_defs``, and additionally may
            yield other types of Dagster events, including :py:class:`Materialization` and
            :py:class:`ExpectationResult`.
        output_defs (List[OutputDefinition]): Outputs of the solid.
        config_schema (Optional[ConfigSchema): The schema for the config. If set, Dagster will check
            that config provided for the solid matches this schema and fail if it does not. If not
            set, Dagster will accept any config provided for the solid.
        description (Optional[str]): Human-readable description of the solid.
        tags (Optional[Dict[str, Any]]): Arbitrary metadata for the solid. Frameworks may
            expect and require certain metadata to be attached to a solid. Users should generally
            not set metadata directly. Values that are not strings will be json encoded and must meet
            the criteria that `json.loads(json.dumps(value)) == value`.
        required_resource_keys (Optional[Set[str]]): Set of resources handles required by this
            solid.
        version (Optional[str]): (Experimental) The version of the solid's compute_fn. Two solids should have
            the same version if and only if they deterministically produce the same outputs when
            provided the same inputs.
        retry_policy (Optional[RetryPolicy]): The retry policy for this solid.


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
        name: str,
        input_defs: Sequence[InputDefinition],
        compute_fn: Union[Callable[..., Any], "DecoratedSolidFunction"],
        output_defs: Sequence[OutputDefinition],
        config_schema: Optional[Union[ConfigSchemaType, IDefinitionConfigSchema]] = None,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        required_resource_keys: Optional[AbstractSet[str]] = None,
        version: Optional[str] = None,
        retry_policy: Optional[RetryPolicy] = None,
    ):
        from .decorators.solid_decorator import DecoratedSolidFunction

        if isinstance(compute_fn, DecoratedSolidFunction):
            self._compute_fn: Union[Callable[..., Any], DecoratedSolidFunction] = compute_fn
        else:
            compute_fn = cast(Callable[..., Any], compute_fn)
            self._compute_fn = check.callable_param(compute_fn, "compute_fn")
        self._config_schema = convert_user_facing_definition_config_schema(config_schema)
        self._required_resource_keys = frozenset(
            check.opt_set_param(required_resource_keys, "required_resource_keys", of_type=str)
        )
        self._version = check.opt_str_param(version, "version")
        if version:
            experimental_arg_warning("version", "SolidDefinition.__init__")
        self._retry_policy = check.opt_inst_param(retry_policy, "retry_policy", RetryPolicy)

        positional_inputs = (
            self._compute_fn.positional_inputs()
            if isinstance(self._compute_fn, DecoratedSolidFunction)
            else None
        )

        super(SolidDefinition, self).__init__(
            name=name,
            input_defs=check.list_param(input_defs, "input_defs", InputDefinition),
            output_defs=check.list_param(output_defs, "output_defs", OutputDefinition),
            description=description,
            tags=check.opt_dict_param(tags, "tags", key_type=str),
            positional_inputs=positional_inputs,
        )

    def __call__(self, *args, **kwargs) -> Any:
        from ..execution.context.invocation import UnboundSolidExecutionContext
        from .composition import is_in_composition
        from .decorators.solid_decorator import DecoratedSolidFunction

        if is_in_composition():
            return super(SolidDefinition, self).__call__(*args, **kwargs)
        else:
            node_label = self.node_type_str  # string "solid" for solids, "op" for ops

            if not isinstance(self.compute_fn, DecoratedSolidFunction):
                raise DagsterInvalidInvocationError(
                    f"Attemped to invoke {node_label} that was not constructed using the `@{node_label}` "
                    f"decorator. Only {node_label}s constructed using the `@{node_label}` decorator can be "
                    "directly invoked."
                )
            if self.compute_fn.has_context_arg():
                if len(args) + len(kwargs) == 0:
                    raise DagsterInvalidInvocationError(
                        f"Compute function of {node_label} '{self.name}' has context argument, but no context "
                        "was provided when invoking."
                    )
                if len(args) > 0:
                    if args[0] is not None and not isinstance(
                        args[0], UnboundSolidExecutionContext
                    ):
                        raise DagsterInvalidInvocationError(
                            f"Compute function of {node_label} '{self.name}' has context argument, "
                            "but no context was provided when invoking."
                        )
                    context = args[0]
                    return solid_invocation_result(self, context, *args[1:], **kwargs)
                # Context argument is provided under kwargs
                else:
                    context_param_name = get_function_params(self.compute_fn.decorated_fn)[0].name
                    if context_param_name not in kwargs:
                        raise DagsterInvalidInvocationError(
                            f"Compute function of {node_label} '{self.name}' has context argument "
                            f"'{context_param_name}', but no value for '{context_param_name}' was "
                            f"found when invoking. Provided kwargs: {kwargs}"
                        )
                    context = kwargs[context_param_name]
                    kwargs_sans_context = {
                        kwarg: val
                        for kwarg, val in kwargs.items()
                        if not kwarg == context_param_name
                    }
                    return solid_invocation_result(self, context, *args, **kwargs_sans_context)

            else:
                if len(args) > 0 and isinstance(args[0], UnboundSolidExecutionContext):
                    raise DagsterInvalidInvocationError(
                        f"Compute function of {node_label} '{self.name}' has no context argument, but "
                        "context was provided when invoking."
                    )
                return solid_invocation_result(self, None, *args, **kwargs)

    @property
    def node_type_str(self) -> str:
        return "solid"

    @property
    def is_graph_job_op_node(self) -> bool:
        return False

    @property
    def compute_fn(self) -> Union[Callable[..., Any], "DecoratedSolidFunction"]:
        return self._compute_fn

    @property
    def config_schema(self) -> IDefinitionConfigSchema:
        return self._config_schema

    @property
    def required_resource_keys(self) -> Optional[FrozenSet[str]]:
        return frozenset(self._required_resource_keys)

    @property
    def version(self) -> Optional[str]:
        return self._version

    def all_dagster_types(self) -> Iterator[DagsterType]:
        yield from self.all_input_output_types()

    def iterate_node_defs(self) -> Iterator[NodeDefinition]:
        yield self

    def iterate_solid_defs(self) -> Iterator["SolidDefinition"]:
        yield self

    def resolve_output_to_origin(
        self, output_name: str, handle: NodeHandle
    ) -> Tuple[OutputDefinition, NodeHandle]:
        return self.output_def_named(output_name), handle

    def input_has_default(self, input_name: str) -> InputDefinition:
        return self.input_def_named(input_name).has_default_value

    def default_value_for_input(self, input_name: str) -> InputDefinition:
        return self.input_def_named(input_name).default_value

    def input_supports_dynamic_output_dep(self, input_name: str) -> bool:
        return True

    def copy_for_configured(
        self,
        name: str,
        description: Optional[str],
        config_schema: IDefinitionConfigSchema,
        config_or_config_fn: Any,
    ) -> "SolidDefinition":
        return SolidDefinition(
            name=name,
            input_defs=self.input_defs,
            compute_fn=self.compute_fn,
            output_defs=self.output_defs,
            config_schema=config_schema,
            description=description or self.description,
            tags=self.tags,
            required_resource_keys=self.required_resource_keys,
            version=self.version,
            retry_policy=self.retry_policy,
        )

    @property
    def retry_policy(self) -> Optional[RetryPolicy]:
        return self._retry_policy


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
        dependencies (Optional[Dict[Union[str, NodeInvocation], Dict[str, DependencyDefinition]]]):
            A structure that declares where each solid gets its inputs. The keys at the top
            level dict are either string names of solids or NodeInvocations. The values
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
                    NodeInvocation('add_one', 'adder_1'): {},
                    NodeInvocation('add_one', 'adder_2'): {'num': DependencyDefinition('adder_1')},
                },
                input_mappings=[InputDefinition('num', Int).mapping_to('adder_1', 'num')],
                output_mappings=[OutputDefinition(Int).mapping_from('adder_2')],
            )
    """

    def __init__(
        self,
        name: str,
        solid_defs: List[NodeDefinition],
        input_mappings: Optional[List[InputMapping]] = None,
        output_mappings: Optional[List[OutputMapping]] = None,
        config_mapping: Optional[ConfigMapping] = None,
        dependencies: Optional[
            Dict[Union[str, NodeInvocation], Dict[str, IDependencyDefinition]]
        ] = None,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        positional_inputs: Optional[List[str]] = None,
    ):
        _check_io_managers_on_composite_solid(name, input_mappings, output_mappings)

        super(CompositeSolidDefinition, self).__init__(
            name=name,
            description=description,
            node_defs=solid_defs,
            dependencies=dependencies,
            tags=tags,
            positional_inputs=positional_inputs,
            input_mappings=input_mappings,
            output_mappings=output_mappings,
            config=config_mapping,
        )

    def all_dagster_types(self) -> Iterator[DagsterType]:
        yield from self.all_input_output_types()

        for node_def in self._node_defs:
            yield from node_def.all_dagster_types()

    def copy_for_configured(
        self,
        name: str,
        description: Optional[str],
        config_schema: IDefinitionConfigSchema,
        config_or_config_fn: Any,
    ) -> "CompositeSolidDefinition":
        config_mapping = self._config_mapping
        if config_mapping is None:
            raise DagsterInvalidDefinitionError(
                "Only composite solids utilizing config mapping can be pre-configured. The "
                'composite solid "{graph_name}" does not have a config mapping, and thus has '
                "nothing to be configured.".format(graph_name=self.name)
            )

        return CompositeSolidDefinition(
            name=name,
            solid_defs=self._node_defs,
            input_mappings=self.input_mappings,
            output_mappings=self.output_mappings,
            config_mapping=ConfigMapping(
                config_mapping.config_fn,
                config_schema=config_schema,
                receive_processed_config_values=config_mapping.receive_processed_config_values,
            ),
            dependencies=self.dependencies,
            description=description or self.description,
            tags=self.tags,
            positional_inputs=self.positional_inputs,
        )

    @property
    def node_type_str(self):
        return "composite solid"

    @property
    def is_graph_job_op_node(self) -> bool:
        return False


def _check_io_managers_on_composite_solid(
    name: str,
    input_mappings: Optional[List[InputMapping]],
    output_mappings: Optional[List[OutputMapping]],
):
    # Ban root_manager_key on composite solids
    if input_mappings:
        for input_mapping in input_mappings:
            input_def = input_mapping.definition
            if input_def.root_manager_key:
                raise DagsterInvalidDefinitionError(
                    "Root input manager cannot be set on a composite solid: "
                    f'root_manager_key "{input_def.root_manager_key}" '
                    f'is set on InputDefinition "{input_def.name}" of composite solid "{name}". '
                )
    # Ban io_manager_key on composite solids
    if output_mappings:
        for output_mapping in output_mappings:
            output_def = output_mapping.definition
            if output_def.io_manager_key != "io_manager":
                raise DagsterInvalidDefinitionError(
                    "IO manager cannot be set on a composite solid: "
                    f'io_manager_key "{output_def.io_manager_key}" '
                    f'is set  on OutputtDefinition "{output_def.name}" of composite solid "{name}". '
                )
