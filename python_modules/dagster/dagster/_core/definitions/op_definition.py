import inspect
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    List,
    Mapping,
    Optional,
    Sequence,
    Union,
    cast,
)

from typing_extensions import TypeAlias, get_origin

import dagster._check as check
from dagster._annotations import public
from dagster._config.config_schema import UserConfigSchema
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.errors import DagsterInvariantViolationError
from dagster._utils.backcompat import canonicalize_backcompat_args, deprecation_warning

from .definition_config_schema import IDefinitionConfigSchema
from .hook_definition import HookDefinition
from .inference import infer_output_props
from .input import In, InputDefinition
from .output import Out, OutputDefinition
from .solid_definition import SolidDefinition

if TYPE_CHECKING:
    from .composition import PendingNodeInvocation
    from .decorators.solid_decorator import DecoratedSolidFunction

OpComputeFunction: TypeAlias = Callable[..., Any]


class OpDefinition(SolidDefinition):
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

    def __init__(
        self,
        compute_fn: Union[Callable[..., Any], "DecoratedSolidFunction"],
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
        from .decorators.solid_decorator import (
            DecoratedSolidFunction,
            resolve_checked_solid_fn_inputs,
        )

        ins = check.opt_mapping_param(ins, "ins")
        input_defs = [
            inp.to_definition(name) for name, inp in sorted(ins.items(), key=lambda input: input[0])
        ]  # sort so that input definition order is deterministic

        if isinstance(compute_fn, DecoratedSolidFunction):
            resolved_input_defs: Sequence[InputDefinition] = resolve_checked_solid_fn_inputs(
                decorator_name="@op",
                fn_name=name,
                compute_fn=cast(DecoratedSolidFunction, compute_fn),
                explicit_input_defs=input_defs,
                exclude_nothing=True,
            )
        else:
            resolved_input_defs = input_defs

        code_version = canonicalize_backcompat_args(
            code_version, "code_version", version, "version", "2.0"
        )

        check.opt_mapping_param(outs, "outs")
        output_defs = _resolve_output_defs_from_outs(
            compute_fn=compute_fn, outs=outs, default_code_version=code_version
        )

        super(OpDefinition, self).__init__(
            compute_fn=compute_fn,
            name=name,
            description=description,
            config_schema=config_schema,
            required_resource_keys=required_resource_keys,
            tags=tags,
            version=code_version,
            retry_policy=retry_policy,
            input_defs=resolved_input_defs,
            output_defs=output_defs,
        )

    @property
    def node_type_str(self) -> str:
        return "op"

    @property
    def is_graph_job_op_node(self) -> bool:
        return True

    @public  # type: ignore
    @property
    def ins(self) -> Mapping[str, In]:
        return {input_def.name: In.from_definition(input_def) for input_def in self.input_defs}

    @public  # type: ignore
    @property
    def outs(self) -> Mapping[str, Out]:
        return {output_def.name: Out.from_definition(output_def) for output_def in self.output_defs}

    @public  # type: ignore
    @property
    def required_resource_keys(self) -> AbstractSet[str]:
        return super(OpDefinition, self).required_resource_keys

    @public  # type: ignore
    @property
    def version(self) -> Optional[str]:
        deprecation_warning("`version` property on OpDefinition", "2.0")
        return super(OpDefinition, self).version

    @public  # type: ignore
    @property
    def retry_policy(self) -> Optional[RetryPolicy]:
        return super(OpDefinition, self).retry_policy

    @public  # type: ignore
    @property
    def name(self) -> str:
        return super(OpDefinition, self).name

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


def _resolve_output_defs_from_outs(
    compute_fn: Union[Callable[..., Any], "DecoratedSolidFunction"],
    outs: Optional[Mapping[str, Out]],
    default_code_version: Optional[str],
) -> Sequence[OutputDefinition]:
    from .decorators.solid_decorator import DecoratedSolidFunction

    if isinstance(compute_fn, DecoratedSolidFunction):
        inferred_output_props = infer_output_props(
            cast(DecoratedSolidFunction, compute_fn).decorated_fn
        )
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
    if annotation != inspect.Parameter.empty and not len(annotation.__args__) == len(outs):
        raise DagsterInvariantViolationError(
            "Expected Tuple annotation to have number of entries matching the "
            f"number of outputs for more than one output. Expected {len(outs)} "
            f"outputs but annotation has {len(annotation.__args__)}."
        )
    for idx, (name, cur_out) in enumerate(outs.items()):
        annotation_type = (
            annotation.__args__[idx]
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
