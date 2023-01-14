import inspect
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
)

from typing_extensions import TypeAlias, get_args, get_origin

import dagster._check as check
from dagster._annotations import public
from dagster._config.config_schema import UserConfigSchema
from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.dependency import NodeHandle
from dagster._core.definitions.node_definition import NodeDefinition
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.resource_requirement import (
    InputManagerRequirement,
    OpDefinitionResourceRequirement,
    OutputManagerRequirement,
    ResourceRequirement,
)
from dagster._core.definitions.solid_invocation import op_invocation_result
from dagster._core.errors import DagsterInvalidInvocationError, DagsterInvariantViolationError
from dagster._core.types.dagster_type import DagsterType, DagsterTypeKind
from dagster._utils.backcompat import canonicalize_backcompat_args, deprecation_warning

from .definition_config_schema import (
    IDefinitionConfigSchema,
    convert_user_facing_definition_config_schema,
)
from .hook_definition import HookDefinition
from .inference import infer_output_props
from .input import In, InputDefinition
from .output import Out, OutputDefinition

if TYPE_CHECKING:
    from dagster._core.definitions.asset_layer import AssetLayer

    from .composition import PendingNodeInvocation
    from .decorators.solid_decorator import DecoratedOpFunction

OpComputeFunction: TypeAlias = Callable[..., Any]


class OpDefinition(NodeDefinition):
    """
    Defines an op, the functional unit of user-defined computation.

    For more details on what a op is, refer to the
    `Ops Overview <../../concepts/ops-jobs-graphs/ops>`_ .

    End users should prefer the :func:`@op <op>` decorator. OpDefinition is generally intended to be
    used by framework authors or for programatically generated ops.

    Args:
        name (str): Name of the op. Must be unique within any :py:class:`GraphDefinition` or
            :py:class:`JobDefinition` that contains the op.
        input_defs (List[InputDefinition]): Inputs of the op.
        compute_fn (Callable): The core of the op, the function that performs the actual
            computation. The signature of this function is determined by ``input_defs``, and
            optionally, an injected first argument, ``context``, a collection of information
            provided by the system.

            This function will be coerced into a generator or an async generator, which must yield
            one :py:class:`Output` for each of the op's ``output_defs``, and additionally may
            yield other types of Dagster events, including :py:class:`AssetMaterialization` and
            :py:class:`ExpectationResult`.
        output_defs (List[OutputDefinition]): Outputs of the op.
        config_schema (Optional[ConfigSchema): The schema for the config. If set, Dagster will check
            that the config provided for the op matches this schema and will fail if it does not. If
            not set, Dagster will accept any config provided for the op.
        description (Optional[str]): Human-readable description of the op.
        tags (Optional[Dict[str, Any]]): Arbitrary metadata for the op. Frameworks may
            expect and require certain metadata to be attached to a op. Users should generally
            not set metadata directly. Values that are not strings will be json encoded and must meet
            the criteria that `json.loads(json.dumps(value)) == value`.
        required_resource_keys (Optional[Set[str]]): Set of resources handles required by this op.
        code_version (Optional[str]): (Experimental) Version of the code encapsulated by the op. If set,
            this is used as a default code version for all outputs.
        retry_policy (Optional[RetryPolicy]): The retry policy for this op.


    Examples:
        .. code-block:: python

            def _add_one(_context, inputs):
                yield Output(inputs["num"] + 1)

            OpDefinition(
                name="add_one",
                ins={"num": In(int)},
                outs={"result": Out(int)},
                compute_fn=_add_one,
            )
    """

    _compute_fn: Union[Callable[..., Any], "DecoratedOpFunction"]
    _config_schema: IDefinitionConfigSchema
    _required_resource_keys: AbstractSet[str]
    _version: Optional[str]
    _retry_policy: Optional[RetryPolicy]

    def __init__(
        self,
        compute_fn: Union[Callable[..., Any], "DecoratedOpFunction"],
        name: str,
        ins: Optional[Mapping[str, In]] = None,
        outs: Optional[Mapping[str, Out]] = None,
        description: Optional[str] = None,
        config_schema: Optional[Union[UserConfigSchema, IDefinitionConfigSchema]] = None,
        required_resource_keys: Optional[AbstractSet[str]] = None,
        tags: Optional[Mapping[str, Any]] = None,
        version: Optional[str] = None,
        retry_policy: Optional[RetryPolicy] = None,
        code_version: Optional[str] = None,
    ):
        from .decorators.solid_decorator import DecoratedOpFunction, resolve_checked_solid_fn_inputs

        ins = check.opt_mapping_param(ins, "ins")
        input_defs = [
            inp.to_definition(name) for name, inp in sorted(ins.items(), key=lambda input: input[0])
        ]  # sort so that input definition order is deterministic

        if isinstance(compute_fn, DecoratedOpFunction):
            resolved_input_defs: Sequence[InputDefinition] = resolve_checked_solid_fn_inputs(
                decorator_name="@op",
                fn_name=name,
                compute_fn=cast(DecoratedOpFunction, compute_fn),
                explicit_input_defs=input_defs,
                exclude_nothing=True,
            )
            self._compute_fn = compute_fn
        else:
            resolved_input_defs = input_defs
            self._compute_fn = check.callable_param(compute_fn, "compute_fn")

        code_version = canonicalize_backcompat_args(
            code_version, "code_version", version, "version", "2.0"
        )
        self._version = code_version

        check.opt_mapping_param(outs, "outs")
        output_defs = _resolve_output_defs_from_outs(
            compute_fn=compute_fn, outs=outs, default_code_version=code_version
        )

        self._config_schema = convert_user_facing_definition_config_schema(config_schema)
        self._required_resource_keys = frozenset(
            check.opt_set_param(required_resource_keys, "required_resource_keys", of_type=str)
        )
        self._retry_policy = check.opt_inst_param(retry_policy, "retry_policy", RetryPolicy)

        positional_inputs = (
            self._compute_fn.positional_inputs()
            if isinstance(self._compute_fn, DecoratedOpFunction)
            else None
        )

        super(OpDefinition, self).__init__(
            name=name,
            input_defs=check.sequence_param(resolved_input_defs, "input_defs", InputDefinition),
            output_defs=check.sequence_param(output_defs, "output_defs", OutputDefinition),
            description=description,
            tags=check.opt_mapping_param(tags, "tags", key_type=str),
            positional_inputs=positional_inputs,
        )

    @property
    def node_type_str(self) -> str:
        return "op"

    @property
    def is_graph_job_op_node(self) -> bool:
        return True

    @public  # type: ignore
    @property
    def name(self) -> str:
        return super(OpDefinition, self).name

    @public  # type: ignore
    @property
    def ins(self) -> Mapping[str, In]:
        return {input_def.name: In.from_definition(input_def) for input_def in self.input_defs}

    @public  # type: ignore
    @property
    def outs(self) -> Mapping[str, Out]:
        return {output_def.name: Out.from_definition(output_def) for output_def in self.output_defs}

    @property
    def compute_fn(self) -> Union[Callable[..., Any], "DecoratedOpFunction"]:
        return self._compute_fn

    @public  # type: ignore
    @property
    def config_schema(self) -> IDefinitionConfigSchema:
        return self._config_schema

    @public  # type: ignore
    @property
    def required_resource_keys(self) -> AbstractSet[str]:
        return frozenset(self._required_resource_keys)

    @public  # type: ignore
    @property
    def version(self) -> Optional[str]:
        deprecation_warning("`version` property on OpDefinition", "2.0")
        return self._version

    @public  # type: ignore
    @property
    def retry_policy(self) -> Optional[RetryPolicy]:
        return self._retry_policy

    @public  # type: ignore
    @property
    def tags(self) -> Mapping[str, str]:
        return super(OpDefinition, self).tags

    @public
    def alias(self, name: str) -> "PendingNodeInvocation":
        return super(OpDefinition, self).alias(name)

    @public
    def tag(self, tags: Optional[Mapping[str, str]]) -> "PendingNodeInvocation":
        return super(OpDefinition, self).tag(tags)

    @public
    def with_hooks(self, hook_defs: AbstractSet[HookDefinition]) -> "PendingNodeInvocation":
        return super(OpDefinition, self).with_hooks(hook_defs)

    @public
    def with_retry_policy(self, retry_policy: RetryPolicy) -> "PendingNodeInvocation":
        return super(OpDefinition, self).with_retry_policy(retry_policy)

    def is_from_decorator(self) -> bool:
        from .decorators.solid_decorator import DecoratedOpFunction

        return isinstance(self._compute_fn, DecoratedOpFunction)

    def get_output_annotation(self) -> Any:
        if not self.is_from_decorator():
            raise DagsterInvalidInvocationError(
                f"Attempted to get output annotation for {self.node_type_str} '{self.name}', "
                "which was not constructed from a decorated function."
            )
        return cast("DecoratedOpFunction", self.compute_fn).get_output_annotation()

    def all_dagster_types(self) -> Iterator[DagsterType]:
        yield from self.all_input_output_types()

    def iterate_node_defs(self) -> Iterator[NodeDefinition]:
        yield self

    def iterate_solid_defs(self) -> Iterator["OpDefinition"]:
        yield self

    T_Handle = TypeVar("T_Handle", bound=Optional[NodeHandle])

    def resolve_output_to_origin(
        self, output_name: str, handle: T_Handle
    ) -> Tuple[OutputDefinition, T_Handle]:
        return self.output_def_named(output_name), handle

    def resolve_output_to_origin_op_def(self, output_name: str) -> "OpDefinition":
        return self

    def get_inputs_must_be_resolved_top_level(
        self, asset_layer: "AssetLayer", handle: Optional[NodeHandle] = None
    ) -> Sequence[InputDefinition]:
        handle = cast(NodeHandle, check.inst_param(handle, "handle", NodeHandle))
        unresolveable_input_defs = []
        for input_def in self.input_defs:
            if (
                not input_def.dagster_type.loader
                and not input_def.dagster_type.kind == DagsterTypeKind.NOTHING
                and not input_def.root_manager_key
                and not input_def.has_default_value
            ):
                input_asset_key = asset_layer.asset_key_for_input(handle, input_def.name)
                # If input_asset_key is present, this input can be resolved
                # by a source asset, so input does not need to be resolved
                # at the top level.
                if input_asset_key:
                    continue
                unresolveable_input_defs.append(input_def)
        return unresolveable_input_defs

    def input_has_default(self, input_name: str) -> bool:
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
    ) -> "OpDefinition":
        return OpDefinition(
            name=name,
            ins={input_def.name: In.from_definition(input_def) for input_def in self.input_defs},
            outs={
                output_def.name: Out.from_definition(output_def) for output_def in self.output_defs
            },
            compute_fn=self.compute_fn,
            config_schema=config_schema,
            description=description or self.description,
            tags=self.tags,
            required_resource_keys=self.required_resource_keys,
            code_version=self.version,
            retry_policy=self.retry_policy,
        )

    def get_resource_requirements(
        self,
        outer_context: Optional[object] = None,
    ) -> Iterator[ResourceRequirement]:
        # Outer requiree in this context is the outer-calling node handle. If not provided, then just use the solid name.
        outer_context = cast(Optional[Tuple[NodeHandle, Optional["AssetLayer"]]], outer_context)
        if not outer_context:
            handle = None
            asset_layer = None
        else:
            handle, asset_layer = outer_context
        node_description = f"{self.node_type_str} '{handle or self.name}'"
        for resource_key in sorted(list(self.required_resource_keys)):
            yield OpDefinitionResourceRequirement(
                key=resource_key, node_description=node_description
            )
        for input_def in self.input_defs:
            if input_def.root_manager_key:
                yield InputManagerRequirement(
                    key=input_def.root_manager_key,
                    node_description=node_description,
                    input_name=input_def.name,
                    root_input=True,
                )
            elif input_def.input_manager_key:
                yield InputManagerRequirement(
                    key=input_def.input_manager_key,
                    node_description=node_description,
                    input_name=input_def.name,
                    root_input=False,
                )
            elif asset_layer and handle:
                input_asset_key = asset_layer.asset_key_for_input(handle, input_def.name)
                if input_asset_key:
                    io_manager_key = asset_layer.io_manager_key_for_asset(input_asset_key)
                    yield InputManagerRequirement(
                        key=io_manager_key,
                        node_description=node_description,
                        input_name=input_def.name,
                        root_input=False,
                    )

        for output_def in self.output_defs:
            yield OutputManagerRequirement(
                key=output_def.io_manager_key,
                node_description=node_description,
                output_name=output_def.name,
            )

    def __call__(self, *args, **kwargs) -> Any:
        from ..execution.context.invocation import UnboundOpExecutionContext
        from .composition import is_in_composition
        from .decorators.solid_decorator import DecoratedOpFunction

        if is_in_composition():
            return super(OpDefinition, self).__call__(*args, **kwargs)
        else:
            node_label = self.node_type_str  # string "solid" for solids, "op" for ops

            if not isinstance(self.compute_fn, DecoratedOpFunction):
                raise DagsterInvalidInvocationError(
                    f"Attemped to invoke {node_label} that was not constructed using the"
                    f" `@{node_label}` decorator. Only {node_label}s constructed using the"
                    f" `@{node_label}` decorator can be directly invoked."
                )
            if self.compute_fn.has_context_arg():
                if len(args) + len(kwargs) == 0:
                    raise DagsterInvalidInvocationError(
                        f"Compute function of {node_label} '{self.name}' has context argument, but"
                        " no context was provided when invoking."
                    )
                if len(args) > 0:
                    if args[0] is not None and not isinstance(args[0], UnboundOpExecutionContext):
                        raise DagsterInvalidInvocationError(
                            f"Compute function of {node_label} '{self.name}' has context argument, "
                            "but no context was provided when invoking."
                        )
                    context = args[0]
                    return op_invocation_result(self, context, *args[1:], **kwargs)
                # Context argument is provided under kwargs
                else:
                    context_param_name = get_function_params(self.compute_fn.decorated_fn)[0].name
                    if context_param_name not in kwargs:
                        raise DagsterInvalidInvocationError(
                            f"Compute function of {node_label} '{self.name}' has context argument "
                            f"'{context_param_name}', but no value for '{context_param_name}' was "
                            f"found when invoking. Provided kwargs: {kwargs}"
                        )
                    context = cast(UnboundOpExecutionContext, kwargs[context_param_name])
                    kwargs_sans_context = {
                        kwarg: val
                        for kwarg, val in kwargs.items()
                        if not kwarg == context_param_name
                    }
                    return op_invocation_result(self, context, *args, **kwargs_sans_context)

            else:
                if len(args) > 0 and isinstance(args[0], UnboundOpExecutionContext):
                    raise DagsterInvalidInvocationError(
                        f"Compute function of {node_label} '{self.name}' has no context argument,"
                        " but context was provided when invoking."
                    )
                return op_invocation_result(self, None, *args, **kwargs)


def _resolve_output_defs_from_outs(
    compute_fn: Union[Callable[..., Any], "DecoratedOpFunction"],
    outs: Optional[Mapping[str, Out]],
    default_code_version: Optional[str],
) -> Sequence[OutputDefinition]:
    from .decorators.solid_decorator import DecoratedOpFunction

    if isinstance(compute_fn, DecoratedOpFunction):
        inferred_output_props = infer_output_props(compute_fn.decorated_fn)
        annotation = inferred_output_props.annotation
        description = inferred_output_props.description
    else:
        inferred_output_props = None
        annotation = inspect.Parameter.empty
        description = None

    if outs is None:
        return [OutputDefinition.create_from_inferred(inferred_output_props, default_code_version)]

    # If only a single entry has been provided to the out dict, then slurp the
    # annotation into the entry.
    if len(outs) == 1:
        name = list(outs.keys())[0]
        only_out = outs[name]
        return [only_out.to_definition(annotation, name, description, default_code_version)]

    output_defs: List[OutputDefinition] = []

    # Introspection on type annotations is experimental, so checking
    # metaclass is the best we can do.
    if annotation != inspect.Parameter.empty and not get_origin(annotation) == tuple:
        raise DagsterInvariantViolationError(
            "Expected Tuple annotation for multiple outputs, but received non-tuple annotation."
        )
    if annotation != inspect.Parameter.empty and not len(get_args(annotation)) == len(outs):
        raise DagsterInvariantViolationError(
            "Expected Tuple annotation to have number of entries matching the "
            f"number of outputs for more than one output. Expected {len(outs)} "
            f"outputs but annotation has {len(get_args(annotation))}."
        )
    for idx, (name, cur_out) in enumerate(outs.items()):
        annotation_type = (
            get_args(annotation)[idx]
            if annotation != inspect.Parameter.empty
            else inspect.Parameter.empty
        )
        # Don't provide description when using multiple outputs. Introspection
        # is challenging when faced with multiple inputs.
        output_defs.append(
            cur_out.to_definition(
                annotation_type, name=name, description=None, code_version=default_code_version
            )
        )

    return output_defs
