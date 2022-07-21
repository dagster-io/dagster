from typing import (
    Dict,
    Mapping,
    Optional,
    Union,
    List,
    TYPE_CHECKING,
    cast,
    Callable,
    Any,
    AbstractSet,
    Sequence,
)

from .input import In
from .output import Out
from .solid_definition import SolidDefinition
from .output import OutputDefinition
from .input import InputDefinition
from ...seven.typing import get_origin
from dagster.config.config_schema import UserConfigSchema
from .definition_config_schema import IDefinitionConfigSchema


import dagster._check as check
from dagster.core.errors import DagsterInvariantViolationError
from .inference import InferredOutputProps, infer_output_props
from dagster.core.definitions.policy import RetryPolicy


if TYPE_CHECKING:
    from .decorators.solid_decorator import DecoratedSolidFunction


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
        version (Optional[str]): (Experimental) The version of the op's compute_fn. Two ops should
            have the same version if and only if they deterministically produce the same outputs
            when provided the same inputs.
        retry_policy (Optional[RetryPolicy]): The retry policy for this op.


    Examples:
        .. code-block:: python

            def _add_one(_context, inputs):
                yield Output(inputs["num"] + 1)

            OpDefinition(
                name="add_one",
                input_defs=[InputDefinition("num", Int)],
                output_defs=[OutputDefinition(Int)], # default name ("result")
                compute_fn=_add_one,
            )
    """

    def __init__(
        self,
        compute_fn: Union[Callable[..., Any], "DecoratedSolidFunction"],
        name: str,
        description: Optional[str],
        ins: Optional[Mapping[str, In]],
        out: Optional[Union[Out, Mapping[str, Out]]],
        config_schema: Optional[Union[UserConfigSchema, IDefinitionConfigSchema]] = None,
        required_resource_keys: Optional[AbstractSet[str]] = None,
        tags: Optional[Mapping[str, Any]] = None,
        version: Optional[str] = None,
        retry_policy: Optional[RetryPolicy] = None,
        input_defs: Optional[Sequence[InputDefinition]] = None,
        output_defs: Optional[Sequence[OutputDefinition]] = None,
    ):
        from .decorators.solid_decorator import (
            resolve_checked_solid_fn_inputs,
            DecoratedSolidFunction,
        )

        self._ins = ins
        self._out = out

        if input_defs is not None and ins is not None:
            check.failed("Values cannot be provided for both the 'input_defs' and 'ins' arguments")

        if output_defs is not None and out is not None:
            check.failed("Values cannot be provided for both the 'output_defs' and 'out' arguments")

        if ins is not None:
            input_defs = [
                inp.to_definition(name)
                for name, inp in sorted(ins.items(), key=lambda input: input[0])
            ]  # sort so that input definition order is deterministic
        else:
            input_defs = check.opt_list_param(input_defs, "input_defs", of_type=InputDefinition)

        if isinstance(compute_fn, DecoratedSolidFunction):
            resolved_input_defs = resolve_checked_solid_fn_inputs(
                decorator_name="@op",
                fn_name=name,
                compute_fn=cast(DecoratedSolidFunction, compute_fn),
                explicit_input_defs=input_defs,
                exclude_nothing=True,
            )
        else:
            resolved_input_defs = input_defs

        if isinstance(compute_fn, DecoratedSolidFunction):
            inferred_out = infer_output_props(cast(DecoratedSolidFunction, compute_fn).decorated_fn)
        else:
            inferred_out = None

        if out is not None:
            resolved_output_defs: Optional[
                Sequence[OutputDefinition]
            ] = _resolve_output_defs_from_outs(
                inferred_out=cast(InferredOutputProps, inferred_out), out=out
            )
        else:
            resolved_output_defs = output_defs

        if resolved_output_defs is None:
            if inferred_out:
                resolved_output_defs = [
                    OutputDefinition.create_from_inferred(cast(InferredOutputProps, inferred_out))
                ]
            else:
                raise DagsterInvariantViolationError(
                    "Error when constructing OpDefinition: an Out must be explicitly provided when constructing an OpDefinition, but none were provided."
                )
        elif len(resolved_output_defs) == 1:
            if inferred_out:
                resolved_output_defs = [resolved_output_defs[0].combine_with_inferred(inferred_out)]
            else:
                raise DagsterInvariantViolationError(
                    "Error when constructing OpDefinition: an Out must be explicitly provided when constructing an OpDefinition, but none were provided."
                )

        super(OpDefinition, self).__init__(
            compute_fn=compute_fn,
            name=name,
            description=description,
            config_schema=config_schema,
            required_resource_keys=required_resource_keys,
            tags=tags,
            version=version,
            retry_policy=retry_policy,
            input_defs=resolved_input_defs,
            output_defs=resolved_output_defs,
        )

    @property
    def node_type_str(self) -> str:
        return "op"

    @property
    def is_graph_job_op_node(self) -> bool:
        return True

    @property
    def ins(self) -> Dict[str, In]:
        return {input_def.name: In.from_definition(input_def) for input_def in self.input_defs}

    @property
    def outs(self) -> Dict[str, Out]:
        return {output_def.name: Out.from_definition(output_def) for output_def in self.output_defs}


def _resolve_output_defs_from_outs(
    inferred_out: Optional[InferredOutputProps], out: Union[Out, Mapping[str, Out]]
) -> Optional[Sequence[OutputDefinition]]:
    annotation = inferred_out.annotation if inferred_out else None
    if isinstance(out, Out):
        return [out.to_definition(annotation, name=None)]
    else:
        check.mapping_param(out, "out", key_type=str, value_type=Out)

        # If only a single entry has been provided to the out dict, then slurp the
        # annotation into the entry.
        if len(out) == 1:
            name = list(out.keys())[0]
            only_out = out[name]
            return [only_out.to_definition(annotation, name)]

        output_defs = []

        # Introspection on type annotations is experimental, so checking
        # metaclass is the best we can do.
        if annotation and not get_origin(annotation) == tuple:
            raise DagsterInvariantViolationError(
                "Expected Tuple annotation for multiple outputs, but received non-tuple annotation."
            )
        if annotation and not len(annotation.__args__) == len(out):
            raise DagsterInvariantViolationError(
                "Expected Tuple annotation to have number of entries matching the "
                f"number of outputs for more than one output. Expected {len(out)} "
                f"outputs but annotation has {len(annotation.__args__)}."
            )
        for idx, (name, cur_out) in enumerate(out.items()):
            annotation_type = annotation.__args__[idx] if annotation else None
            output_defs.append(cur_out.to_definition(annotation_type, name=name))

        return output_defs
