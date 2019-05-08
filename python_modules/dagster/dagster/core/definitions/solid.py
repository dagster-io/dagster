from abc import ABCMeta

import six

from dagster import check
from dagster.core.types.field_utils import check_user_facing_opt_field_param
from dagster.utils import frozendict

from .input import InputDefinition
from .output import OutputDefinition
from .utils import check_valid_name


class ISolidDefinition(six.with_metaclass(ABCMeta)):
    def __init__(self, name, input_dict, output_dict, description=None, metadata=None):
        self.name = check_valid_name(name)
        self.description = check.opt_str_param(description, 'description')
        self.metadata = check.opt_dict_param(metadata, 'metadata', key_type=str)
        self.input_dict = frozendict(input_dict)
        self.output_dict = frozendict(output_dict)

    def has_input(self, name):
        check.str_param(name, 'name')
        return name in self.input_dict

    def input_def_named(self, name):
        check.str_param(name, 'name')
        return self.input_dict[name]

    def has_output(self, name):
        check.str_param(name, 'name')
        return name in self.output_dict

    def output_def_named(self, name):
        check.str_param(name, 'name')
        return self.output_dict[name]


class SolidDefinition(ISolidDefinition):
    '''A solid (a name extracted from the acronym of "software-structured data" (SSD)) represents
    a unit of computation within a data pipeline.

    As its core, a solid is a function. It accepts inputs (which are values produced from
    other solids) and configuration, and produces outputs. These solids are composed as a
    directed, acyclic graph (DAG) within a pipeline to form a computation that produces
    data assets.

    Solids should be implemented as idempotent, parameterizable, non-destructive functions.
    Data computations with these properties are much easier to test, reason about, and operate.

    The inputs and outputs are gradually, optionally typed by the dagster type system. Types
    can be user-defined and can represent entities as varied as scalars, dataframe, database
    tables, and so forth. They can represent pure in-memory objects, or handles to assets
    on disk or in external resources.

    A solid is a generalized abstraction that could take many forms.

    End users should prefer the @solid and @lambda_solid decorator. SolidDefinition
    is generally used by framework authors.

    Args:
        name (str): Name of the solid.
        inputs (List[InputDefinition]): Inputs of the solid.

        transform_fn (Callable[[SystemTransformExecutionContext, ], Iterable[Union[Result,
            Materialization]]]): The core of the solid, the function that does the actual
            computation. The arguments passed to this function after context are deteremined by
            ``inputs``.

            This function yields :py:class:`Result` according to ``outputs`` or
            :py:class:`Materialization`.

        outputs (List[OutputDefinition]): Outputs of the solid.
        config_field (Optional[Field]): How the solid configured.
        description (Optional[str]): Description of the solid.
        metadata (Optional[Dict[Any, Any]]):
            Arbitrary metadata for the solid. Some frameworks expect and require
            certain metadata to be attached to a solid.
        resources (Optional[Set[str]]): List of resources handles required by this solid.

    Examples:
        .. code-block:: python

            def _add_one(_context, inputs):
                yield Result(inputs["num"] + 1)

            SolidDefinition(
                name="add_one",
                inputs=[InputDefinition("num", Int)],
                outputs=[OutputDefinition(Int)], # default name ("result")
                transform_fn=_add_one,
            )
    '''

    def __init__(
        self,
        name,
        inputs,
        transform_fn,
        outputs,
        config_field=None,
        description=None,
        metadata=None,
        resources=None,
        step_metadata_fn=None,
    ):
        self.name = check_valid_name(name)
        self.transform_fn = check.callable_param(transform_fn, 'transform_fn')
        self.description = check.opt_str_param(description, 'description')
        self.config_field = check_user_facing_opt_field_param(
            config_field,
            'config_field',
            'of a SolidDefinition or @solid named "{name}"'.format(name=name),
        )
        self.metadata = check.opt_dict_param(metadata, 'metadata', key_type=str)
        self.resources = check.opt_set_param(resources, 'resources', of_type=str)
        self.step_metadata_fn = step_metadata_fn

        input_dict = {inp.name: inp for inp in check.list_param(inputs, 'inputs', InputDefinition)}
        output_dict = {
            output.name: output for output in check.list_param(outputs, 'outputs', OutputDefinition)
        }

        super(SolidDefinition, self).__init__(name, input_dict, output_dict, description, metadata)


class CompositeSolidDefinition(ISolidDefinition):
    def __init__(self, name, description=None, metadata=None):

        super(CompositeSolidDefinition, self).__init__(name, {}, {}, description, metadata)
