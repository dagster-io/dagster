from typing import Dict

from .input import In
from .output import Out
from .solid_definition import SolidDefinition


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
