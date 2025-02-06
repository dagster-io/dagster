import inspect
from collections.abc import Iterator, Mapping, Sequence, Set
from typing import TYPE_CHECKING, AbstractSet, Any, Callable, Optional, Union, cast  # noqa: UP035

from typing_extensions import TypeAlias, get_args, get_origin

import dagster._check as check
from dagster._annotations import deprecated, deprecated_param, public
from dagster._config.config_schema import UserConfigSchema
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.definition_config_schema import (
    IDefinitionConfigSchema,
    convert_user_facing_definition_config_schema,
)
from dagster._core.definitions.dependency import NodeHandle, NodeInputHandle, NodeOutputHandle
from dagster._core.definitions.hook_definition import HookDefinition
from dagster._core.definitions.inference import infer_output_props
from dagster._core.definitions.input import In, InputDefinition
from dagster._core.definitions.node_definition import NodeDefinition
from dagster._core.definitions.op_invocation import direct_invocation_result
from dagster._core.definitions.output import Out, OutputDefinition
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.resource_requirement import (
    InputManagerRequirement,
    OpDefinitionResourceRequirement,
    OutputManagerRequirement,
    ResourceRequirement,
)
from dagster._core.definitions.result import MaterializeResult, ObserveResult
from dagster._core.definitions.utils import DEFAULT_IO_MANAGER_KEY
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvariantViolationError,
)
from dagster._core.storage.tags import GLOBAL_CONCURRENCY_TAG
from dagster._core.types.dagster_type import DagsterType, DagsterTypeKind
from dagster._utils import IHasInternalInit
from dagster._utils.warnings import normalize_renamed_param, preview_warning

if TYPE_CHECKING:
    from dagster._core.definitions.asset_layer import AssetLayer
    from dagster._core.definitions.composition import PendingNodeInvocation
    from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction

OpComputeFunction: TypeAlias = Callable[..., Any]


@deprecated_param(
    param="version", breaking_version="2.0", additional_warn_text="Use `code_version` instead."
)
class OpDefinition(NodeDefinition, IHasInternalInit):
    """Defines an op, the functional unit of user-defined computation.

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
        pool (Optional[str]): A string that identifies the pool that governs this op's execution.


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
    _pool: Optional[str]

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
        pool: Optional[str] = None,
    ):
        from dagster._core.definitions.decorators.op_decorator import (
            DecoratedOpFunction,
            resolve_checked_op_fn_inputs,
        )

        ins = check.opt_mapping_param(ins, "ins")
        input_defs = [
            inp.to_definition(name) for name, inp in sorted(ins.items(), key=lambda inp: inp[0])
        ]  # sort so that input definition order is deterministic

        if isinstance(compute_fn, DecoratedOpFunction):
            resolved_input_defs: Sequence[InputDefinition] = resolve_checked_op_fn_inputs(
                decorator_name="@op",
                fn_name=name,
                compute_fn=cast(DecoratedOpFunction, compute_fn),
                explicit_input_defs=input_defs,
                exclude_nothing=True,
            )
            self._compute_fn = compute_fn
            _validate_context_type_hint(self._compute_fn.decorated_fn)
        else:
            resolved_input_defs = input_defs
            self._compute_fn = check.callable_param(compute_fn, "compute_fn")
            _validate_context_type_hint(self._compute_fn)

        code_version = normalize_renamed_param(
            code_version,
            "code_version",
            version,
            "version",
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
        self._pool = pool
        pool = _validate_pool(pool, tags)

        positional_inputs = (
            self._compute_fn.positional_inputs()
            if isinstance(self._compute_fn, DecoratedOpFunction)
            else None
        )

        super().__init__(
            name=name,
            input_defs=check.sequence_param(resolved_input_defs, "input_defs", InputDefinition),
            output_defs=check.sequence_param(output_defs, "output_defs", OutputDefinition),
            description=description,
            tags=(check.opt_mapping_param(tags, "tags", key_type=str)),
            positional_inputs=positional_inputs,
        )

    def dagster_internal_init(
        *,
        compute_fn: Union[Callable[..., Any], "DecoratedOpFunction"],
        name: str,
        ins: Optional[Mapping[str, In]],
        outs: Optional[Mapping[str, Out]],
        description: Optional[str],
        config_schema: Optional[Union[UserConfigSchema, IDefinitionConfigSchema]],
        required_resource_keys: Optional[AbstractSet[str]],
        tags: Optional[Mapping[str, Any]],
        version: Optional[str],
        retry_policy: Optional[RetryPolicy],
        code_version: Optional[str],
        pool: Optional[str],
    ) -> "OpDefinition":
        return OpDefinition(
            compute_fn=compute_fn,
            name=name,
            ins=ins,
            outs=outs,
            description=description,
            config_schema=config_schema,
            required_resource_keys=required_resource_keys,
            tags=tags,
            version=version,
            retry_policy=retry_policy,
            code_version=code_version,
            pool=pool,
        )

    @property
    def node_type_str(self) -> str:
        return "op"

    @property
    def is_graph_job_op_node(self) -> bool:
        return True

    @public
    @property
    def name(self) -> str:
        """str: The name of this op."""
        return super().name

    @public
    @property
    def ins(self) -> Mapping[str, In]:
        """Mapping[str, In]: A mapping from input name to the In object that represents that input."""
        return {input_def.name: In.from_definition(input_def) for input_def in self.input_defs}

    @public
    @property
    def outs(self) -> Mapping[str, Out]:
        """Mapping[str, Out]: A mapping from output name to the Out object that represents that output."""
        return {output_def.name: Out.from_definition(output_def) for output_def in self.output_defs}

    @property
    def compute_fn(self) -> Union[Callable[..., Any], "DecoratedOpFunction"]:
        return self._compute_fn

    @public
    @property
    def config_schema(self) -> IDefinitionConfigSchema:
        """IDefinitionConfigSchema: The config schema for this op."""
        return self._config_schema

    @public
    @property
    def required_resource_keys(self) -> AbstractSet[str]:
        """AbstractSet[str]: A set of keys for resources that must be provided to this OpDefinition."""
        return frozenset(self._required_resource_keys)

    @public
    @deprecated(breaking_version="2.0", additional_warn_text="Use `code_version` instead.")
    @property
    def version(self) -> Optional[str]:
        """str: Version of the code encapsulated by the op. If set, this is used as a
        default code version for all outputs.
        """
        return self._version

    @public
    @property
    def retry_policy(self) -> Optional[RetryPolicy]:
        """Optional[RetryPolicy]: The RetryPolicy for this op."""
        return self._retry_policy

    @public
    @property
    def tags(self) -> Mapping[str, str]:
        """Mapping[str, str]: The tags for this op."""
        return super().tags

    @public
    def alias(self, name: str) -> "PendingNodeInvocation":
        """Creates a copy of this op with the given name."""
        return super().alias(name)

    @public
    def tag(self, tags: Optional[Mapping[str, str]]) -> "PendingNodeInvocation":
        """Creates a copy of this op with the given tags."""
        return super().tag(tags)

    @public
    def with_hooks(self, hook_defs: AbstractSet[HookDefinition]) -> "PendingNodeInvocation":
        """Creates a copy of this op with the given hook definitions."""
        return super().with_hooks(hook_defs)

    @public
    def with_retry_policy(self, retry_policy: RetryPolicy) -> "PendingNodeInvocation":
        """Creates a copy of this op with the given retry policy."""
        return super().with_retry_policy(retry_policy)

    @property
    def pool(self) -> Optional[str]:
        """Optional[str]: The concurrency pool for this op."""
        return self._pool

    @property
    def pools(self) -> Set[str]:
        """Optional[str]: The concurrency pools for this op node."""
        return {self._pool} if self._pool else set()

    def is_from_decorator(self) -> bool:
        from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction

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

    def iterate_op_defs(self) -> Iterator["OpDefinition"]:
        yield self

    def resolve_output_to_origin(
        self, output_name: str, handle: Optional[NodeHandle]
    ) -> tuple[OutputDefinition, Optional[NodeHandle]]:
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
                and not input_def.has_default_value
                and not input_def.input_manager_key
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

    def with_replaced_properties(
        self,
        name: str,
        ins: Optional[Mapping[str, In]] = None,
        outs: Optional[Mapping[str, Out]] = None,
        config_schema: Optional[IDefinitionConfigSchema] = None,
        description: Optional[str] = None,
    ) -> "OpDefinition":
        return OpDefinition.dagster_internal_init(
            name=name,
            ins={input_def.name: In.from_definition(input_def) for input_def in self.input_defs}
            if ins is None
            else ins,
            outs={
                output_def.name: Out.from_definition(output_def) for output_def in self.output_defs
            }
            if outs is None
            else outs,
            compute_fn=self.compute_fn,
            config_schema=config_schema or self.config_schema,
            description=description or self.description,
            tags=self.tags,
            required_resource_keys=self.required_resource_keys,
            code_version=self._version,
            retry_policy=self.retry_policy,
            version=None,  # code_version replaces version
            pool=self.pool,
        )

    def copy_for_configured(
        self,
        name: str,
        description: Optional[str],
        config_schema: IDefinitionConfigSchema,
    ) -> "OpDefinition":
        return self.with_replaced_properties(
            name=name,
            description=description,
            config_schema=config_schema,
        )

    def get_resource_requirements(
        self,
        handle: Optional[NodeHandle],
        asset_layer: Optional["AssetLayer"],
    ) -> Iterator[ResourceRequirement]:
        node_description = f"{self.node_type_str} '{handle or self.name}'"
        for resource_key in sorted(list(self.required_resource_keys)):
            yield OpDefinitionResourceRequirement(
                key=resource_key, node_description=node_description
            )
        for input_def in self.input_defs:
            if input_def.input_manager_key:
                yield InputManagerRequirement(
                    key=input_def.input_manager_key,
                    node_description=node_description,
                    input_name=input_def.name,
                    root_input=False,
                )
            elif asset_layer and handle:
                input_asset_key = asset_layer.asset_key_for_input(handle, input_def.name)
                if input_asset_key:
                    io_manager_key = (
                        asset_layer.get(input_asset_key).io_manager_key
                        if asset_layer.has(input_asset_key)
                        else DEFAULT_IO_MANAGER_KEY
                    )
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

    def resolve_input_to_destinations(
        self, input_handle: NodeInputHandle
    ) -> Sequence[NodeInputHandle]:
        return [input_handle]

    def resolve_output_to_destinations(
        self, output_name: str, handle: Optional[NodeHandle]
    ) -> Sequence[NodeInputHandle]:
        return []

    def __call__(self, *args, **kwargs) -> Any:
        from dagster._core.definitions.composition import is_in_composition

        if is_in_composition():
            return super().__call__(*args, **kwargs)

        return direct_invocation_result(self, *args, **kwargs)

    def get_op_handles(self, parent: NodeHandle) -> AbstractSet[NodeHandle]:
        return {parent}

    def get_op_output_handles(self, parent: Optional[NodeHandle]) -> AbstractSet[NodeOutputHandle]:
        return {
            NodeOutputHandle(node_handle=parent, output_name=output_def.name)
            for output_def in self.output_defs
        }


def _resolve_output_defs_from_outs(
    compute_fn: Union[Callable[..., Any], "DecoratedOpFunction"],
    outs: Optional[Mapping[str, Out]],
    default_code_version: Optional[str],
) -> Sequence[OutputDefinition]:
    from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction

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
        name = next(iter(outs.keys()))
        only_out = outs[name]
        return [only_out.to_definition(annotation, name, description, default_code_version)]

    # If multiple outputs...

    # Note: we don't provide description when using multiple outputs. Introspection
    # is challenging when faced with multiple outputs.

    # ... and no annotation, use empty for each output annotation
    if annotation == inspect.Parameter.empty:
        return [
            out.to_definition(
                annotation_type=inspect.Parameter.empty,
                name=name,
                description=None,
                code_version=default_code_version,
            )
            for (name, out) in outs.items()
        ]

    # ... or if a single result object type, use None for each output annotation
    if _is_result_object_type(annotation):
        # this can happen for example when there are outputs for checks
        # that get reported via a singular MaterializeResult
        return [
            out.to_definition(
                annotation_type=type(None),
                name=name,
                description=None,
                code_version=default_code_version,
            )
            for (name, out) in outs.items()
        ]

    # ... otherwise we expect to have a tuple with entries...
    if get_origin(annotation) != tuple:
        raise DagsterInvariantViolationError(
            "Expected Tuple annotation for multiple outputs, but received non-tuple annotation."
        )
    subtypes = get_args(annotation)

    # ... if they are all result object entries use None
    if len(subtypes) > 0 and all(_is_result_object_type(t) for t in subtypes):
        # the counts of subtypes and outputs may not align due to checks results
        # being passed via MaterializeResult similar to above.
        return [
            out.to_definition(
                annotation_type=type(None),
                name=name,
                description=None,
                code_version=default_code_version,
            )
            for (name, out) in outs.items()
        ]

    # ... otherwise they should align with outputs
    if len(subtypes) != len(outs):
        raise DagsterInvariantViolationError(
            "Expected Tuple annotation to have number of entries matching the "
            f"number of outputs for more than one output. Expected {len(outs)} "
            f"outputs but annotation has {len(subtypes)}."
        )
    return [
        cur_out.to_definition(
            annotation_type=subtypes[idx],
            name=name,
            description=None,
            code_version=default_code_version,
        )
        for idx, (name, cur_out) in enumerate(outs.items())
    ]


def _validate_context_type_hint(fn):
    from inspect import _empty as EmptyAnnotation

    from dagster._core.decorator_utils import get_function_params
    from dagster._core.definitions.decorators.op_decorator import is_context_provided
    from dagster._core.execution.context.compute import (
        AssetCheckExecutionContext,
        AssetExecutionContext,
        OpExecutionContext,
    )

    params = get_function_params(fn)
    if is_context_provided(params):
        if params[0].annotation not in [
            AssetExecutionContext,
            OpExecutionContext,
            EmptyAnnotation,
            AssetCheckExecutionContext,
        ]:
            raise DagsterInvalidDefinitionError(
                f"Cannot annotate `context` parameter with type {params[0].annotation}. `context`"
                " must be annotated with AssetExecutionContext, AssetCheckExecutionContext, OpExecutionContext, or left blank."
            )


def _is_result_object_type(ttype):
    # Is this type special result object type
    return ttype in (MaterializeResult, ObserveResult, AssetCheckResult)


def _validate_pool(pool, tags):
    check.opt_str_param(pool, "pool")
    tags = check.opt_mapping_param(tags, "tags")
    tag_concurrency_key = tags.get(GLOBAL_CONCURRENCY_TAG)
    if pool and tag_concurrency_key and pool != tag_concurrency_key:
        raise DagsterInvalidDefinitionError(
            f'Pool "{pool}" conflicts with the concurrency key tag "{tag_concurrency_key}".'
        )

    if pool:
        preview_warning("Pools")
        return pool

    return None
