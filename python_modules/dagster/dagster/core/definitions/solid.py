from dagster import check

from dagster.core.types.field import Field

from .input import InputDefinition

from .output import OutputDefinition

from .utils import check_valid_name


class SolidDefinition(object):
    '''A solid (a name extracted from the acronym of "software-structured data" (SSD)) represents
    a unit of computation within a data pipeline.

    As its core, a solid is a function. It accepts inputs (which are values produced from
    other solids) and configuration, and produces outputs. These solids are composed as a
    directed, acyclic graph (DAG) within a pipeline to form a computation that produces
    data assets.

    Solids should be implemented as idempotent, parameterizable, non-destructive functions.
    Data computations with these properties are much easier to test, reason about, and operate.

    The inputs and outputs are gradually, optionally typed by the dagster type system. Types
    can be user-defined and can represent entites as varied as scalars, dataframe, database
    tables, and so forth. They can represent pure in-memory objects, or handles to assets
    on disk or in external resources.

    A solid is a generalized abstraction that could take many forms.

    Example:

        .. code-block:: python

            def _read_csv(info, inputs):
                yield Result(pandas.read_csv(info.config['path']))

            SolidDefinition(
                name='read_csv',
                inputs=[],
                config_field=Field(types.Dict({'path' => types.Path})),
                outputs=[OutputDefinition()] # default name ('result') and any typed
                transform_fn
            )

    Attributes:
        name (str): Name of the solid.
        input_defs (List[InputDefinition]): Inputs of the solid.
        transform_fn (callable):
            Callable with the signature
            (
                info: TransformExecutionInfo,
                inputs: Dict[str, Any],
            ) : Iterable<Result>
        outputs_defs (List[OutputDefinition]): Outputs of the solid.
        config_field (Field): How the solid configured.
        description (str): Description of the solid.
        metadata (dict):
            Arbitrary metadata for the solid. Some frameworks expect and require
            certain metadata to be attached to a solid.
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
    ):
        self.name = check_valid_name(name)
        self.input_defs = check.list_param(inputs, 'inputs', InputDefinition)
        self.transform_fn = check.callable_param(transform_fn, 'transform_fn')
        self.output_defs = check.list_param(outputs, 'outputs', OutputDefinition)
        self.description = check.opt_str_param(description, 'description')
        self.config_field = check.opt_inst_param(config_field, 'config_field', Field)
        self.metadata = check.opt_dict_param(metadata, 'metadata', key_type=str)
        self._input_dict = {inp.name: inp for inp in inputs}
        self._output_dict = {output.name: output for output in outputs}

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
