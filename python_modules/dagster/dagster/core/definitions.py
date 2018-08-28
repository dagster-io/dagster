import copy
import keyword
import re

from dagster import check
from dagster.core import types
from dagster.utils.logging import level_from_string

from .errors import DagsterInvalidDefinitionError
from .graph import SolidGraph

DISALLOWED_NAMES = set(
    [
        'context',
        'meta',
        'arg_dict',
        'dict',
        'input_arg_dict',
        'output_arg_dict',
        'int',
        'str',
        'float',
        'bool',
        'input',
        'output',
        'result',
        'type',
    ] + keyword.kwlist  # just disallow all python keywords
)


def check_valid_name(name):
    check.str_param(name, 'name')
    if name in DISALLOWED_NAMES:
        raise DagsterInvalidDefinitionError('{name} is not allowed'.format(name=name))

    regex = r'^[A-Za-z0-9_]+$'
    if not re.match(regex, name):
        raise DagsterInvalidDefinitionError(
            '{name} must be in regex {regex}'.format(name=name, regex=regex)
        )
    return name


def check_argument_def_dict(argument_def_dict):
    return check.dict_param(
        argument_def_dict,
        'argument_def_dict',
        key_type=str,
        value_type=ArgumentDefinition,
    )


class PipelineContextDefinition:
    def __init__(self, *, argument_def_dict, context_fn, description=None):
        self.argument_def_dict = check_argument_def_dict(argument_def_dict)
        self.context_fn = check.callable_param(context_fn, 'context_fn')
        self.description = description


def _default_pipeline_context_definitions():
    def _default_context_fn(_pipeline, args):
        # This has a circular dependency between execution and definition
        # The likely solution is to move the ExecutionContext to definitions.py
        # -- schrockn (07-28-18)
        import dagster.core.execution
        import dagster.utils.logging

        log_level = level_from_string(args['log_level'])
        context = dagster.core.execution.ExecutionContext(
            loggers=[
                dagster.utils.logging.define_colored_console_logger('dagster', level=log_level)
            ]
        )
        return context

    default_context_def = PipelineContextDefinition(
        argument_def_dict={
            'log_level':
            ArgumentDefinition(dagster_type=types.String, is_optional=True, default_value='ERROR')
        },
        context_fn=_default_context_fn,
    )
    return {'default': default_context_def}


class PipelineDefinition:
    def __init__(self, solids, name=None, description=None, context_definitions=None):
        self.description = check.opt_str_param(description, 'description')
        self.name = check.opt_str_param(name, 'name')

        if context_definitions is None:
            context_definitions = _default_pipeline_context_definitions()

        self.context_definitions = check.dict_param(
            context_definitions,
            'context_definitions',
            key_type=str,
            value_type=PipelineContextDefinition,
        )

        for solid in solids:
            if not isinstance(solid, SolidDefinition) and callable(solid):
                raise DagsterInvalidDefinitionError(
                    '''You have passed a lambda or function {solid} into
                a pipeline that is not a solid. You have likely forgetten to annotate this function
                with an @solid decorator located in dagster.core.decorators
                '''.format(solid=solid.__name__)
                )

        self.solids = check.list_param(solids, 'solids', of_type=SolidDefinition)

        solid_names = set([solid.name for solid in self.solids])
        for solid in solids:
            for input_def in solid.inputs:
                if input_def.depends_on:
                    check.invariant(
                        input_def.depends_on.name in solid_names,
                        f'''The solid {input_def.depends_on.name} was specified 
                        as a dependency, however it does not exist in your 
                        pipeline definition. Only the following exist: 
                        {solid_names}'''
                    )

        self.solid_graph = SolidGraph(solids=solids)

    @property
    def solid_names(self):
        return [solid.name for solid in self.solids]

    @property
    def input_names(self):
        return set([input_def.name for input_def in self.all_inputs])

    def get_input(self, solid_name, input_name):
        for solid in self.solids:
            if solid.name != solid_name:
                continue
            for input_def in solid.inputs:
                if input_def.name == input_name:
                    return input_def
        check.failed('not found')

    @property
    def external_inputs(self):
        for input_def in self.all_inputs:
            if input_def.is_external:
                yield input_def

    @property
    def externally_sourced_solids(self):
        for solid in self.solids:
            for input_def in solid.inputs:
                if input_def.is_external:
                    yield solid
                    break

    def has_solid(self, name):
        check.str_param(name, 'name')
        for solid in self.solids:
            if solid.name == name:
                return True
        return False

    @property
    def all_inputs(self):
        for solid in self.solids:
            for input_def in solid.inputs:
                yield input_def

    def solid_named(self, name):
        check.str_param(name, 'name')
        for solid in self.solids:
            if solid.name == name:
                return solid
        check.failed('Could not find solid named ' + name)

    @property
    def all_depended_on_solids(self):
        for input_def in self.all_inputs:
            if input_def.depends_on:
                yield input_def.depends_on

    @property
    def all_sink_solids(self):
        all_names = set([solid.name for solid in self.solids])
        all_depended_on_names = set([solid.name for solid in self.all_depended_on_solids])
        return all_names.difference(all_depended_on_names)


class ExpectationResult:
    def __init__(self, success, solid=None, message=None, result_context=None):
        self.success = check.bool_param(success, 'success')
        self.solid = check.opt_inst_param(solid, SolidDefinition, 'solid')
        self.message = check.opt_str_param(message, 'message')
        self.result_context = check.opt_dict_param(result_context, 'result_context')

    def copy(self):
        return copy.deepcopy(self)


class ExpectationDefinition:
    def __init__(self, name, expectation_fn, description=None):
        self.name = check_valid_name(name)
        self.expectation_fn = check.callable_param(expectation_fn, 'expectation_fn')
        self.description = check.opt_str_param(description, 'description')


class SourceDefinition:
    '''
    name: name of the source

    source_fn: callable
         The input function defines exactly what happens when the source is invoked.

         def simplified_read_csv_example(context, arg_dict):
             context.info('I am in an input.') # use context for logging
             return pd.read_csv(arg_dict['path'])

    argument_def_dict: { str: DagsterType }
         Define the arguments expected by this source . A dictionary that maps a string
         (argument name) to an argument type (defined in dagster.core.types) Continuing
         the above example, the csv signature would be:

         argument_def_dict = {'path' : dagster.core.types.Path }

    '''

    def __init__(self, source_type, source_fn, argument_def_dict, description=None):
        check.callable_param(source_fn, 'source_fn')
        self.source_type = check_valid_name(source_type)
        self.source_fn = check.callable_param(source_fn, 'source_fn')
        self.argument_def_dict = check_argument_def_dict(argument_def_dict)
        self.description = check.opt_str_param(description, 'description')


class InputDefinition:
    '''
    An InputDefinition instances represents an argument to a transform defined within a solid.

    - name: Name of input

    - sources: A list of possible sources for the input. For example, an input which is passed
    to the transform as a pandas dataframe could have any number of different source types
    (CSV, Parquet etc). Some inputs have zero sources, and can only be created by
    execute a dependant solid.

    - depends_on: (Optional). This input depends on another solid in the context of a
    a pipeline.

    - input_callback: (Optional) Called on the source result. Gets execution context and result.
    Can be used to validate the result, log stats etc.
    '''

    def __init__(
        self,
        name,
        dagster_type=None,
        sources=None,
        depends_on=None,
        expectations=None,
        input_callback=None,
        description=None
    ):
        self.name = check_valid_name(name)

        if sources is None and dagster_type is not None:
            sources = dagster_type.default_sources

        self.sources = check.opt_list_param(sources, 'sources', of_type=SourceDefinition)
        self.depends_on = check.opt_inst_param(depends_on, 'depends_on', SolidDefinition)

        self.dagster_type = check.opt_inst_param(
            dagster_type, 'dagster_type', types.DagsterType, types.Any
        )

        self.expectations = check.opt_list_param(
            expectations, 'expectations', of_type=ExpectationDefinition
        )
        self.input_callback = check.opt_callable_param(input_callback, 'input_callback')
        self.description = check.opt_str_param(description, 'description')

    @property
    def is_external(self):
        return self.depends_on is None

    def source_of_type(self, source_type):
        check.str_param(source_type, 'source_type')
        for source in self.sources:
            if source.source_type == source_type:
                return source

        check.failed(
            'Source {source_type} not found in input {input_name}.'.format(
                source_type=source_type,
                input_name=self.name,
            )
        )


class MaterializationDefinition:
    '''
    materialization_fn: callable

        This function defines the actual output.

        The first function argument is the result of the transform function. It can be
        named anything.

        You must specify an argument with the name "arg_dict". It will be the dictionary
        of arguments specified by the caller of the solid

        def materialization_fn(context, args, value):
            pass

    argument_def_dict: { str: DagsterType }
        Define the arguments expected by this materialization. A dictionary that maps a string
        (argument name) to an argument type (defined in dagster.core.types).

        e.g.:

        argument_def_dict = { 'path' : dagster.core.types.Path }
    '''

    def __init__(self, name, materialization_fn, argument_def_dict=None, description=None):
        self.name = check_valid_name(name)
        self.materialization_fn = check.callable_param(materialization_fn, 'materialization_fn')
        self.argument_def_dict = check_argument_def_dict(argument_def_dict)
        self.description = check.opt_str_param(description, 'description')


class OutputDefinition:
    # runtime type info
    def __init__(
        self,
        dagster_type=None,
        materializations=None,
        expectations=None,
        output_callback=None,
        description=None
    ):

        self.dagster_type = check.opt_inst_param(
            dagster_type, 'dagster_type', types.DagsterType, types.Any
        )

        if materializations is None and dagster_type is not None:
            materializations = dagster_type.default_materializations

        self.materializations = check.opt_list_param(
            materializations, 'materializations', of_type=MaterializationDefinition
        )

        self.expectations = check.opt_list_param(
            expectations, 'expectations', of_type=ExpectationDefinition
        )
        self.output_callback = check.opt_callable_param(output_callback, 'output_callback')
        self.description = check.opt_str_param(description, 'description')

    def materialization_of_type(self, name):
        for materialization in self.materializations:
            if materialization.name == name:
                return materialization

        check.failed('Did not find materialization {type}'.format(type=name))


# One or more inputs
# The core computation in the native kernel abstraction
# The output
class SolidDefinition:
    def __init__(self, name, inputs, transform_fn, output, description=None):
        self.name = check_valid_name(name)
        self.inputs = check.list_param(inputs, 'inputs', InputDefinition)
        self.output = check.inst_param(output, 'output', OutputDefinition)
        self.transform_fn = check.callable_param(transform_fn, 'transform')
        self.description = check.opt_str_param(description, 'description')

    # Notes to self

    # Input Definitions
    #   - DematerializationDefinitions
    #       - Arguments
    #       - Compute (args) => Value
    #   - Expectations
    #   - Dependency

    # Transform Definition
    #   - Function (inputs) => Value
    #   - Runtime Types (Inputs and Outputs)

    # Output Definition
    #   - MaterializationDefinitions
    #       - Arguments
    #       - Compute (value, args) => Result
    #   - Expectations

    @property
    def input_names(self):
        return [inp.name for inp in self.inputs]

    def has_input(self, name):
        check.str_param(name, 'name')
        for input_def in self.inputs:
            if input_def.name == name:
                return True
        return False

    def input_def_named(self, name):
        check.str_param(name, 'name')
        for input_def in self.inputs:
            if input_def.name == name:
                return input_def

        check.failed('input {name} not found'.format(name=name))


class __ArgumentValueSentinel:
    pass


NO_DEFAULT_PROVIDED = __ArgumentValueSentinel


class ArgumentDefinition:
    def __init__(
        self, dagster_type, default_value=NO_DEFAULT_PROVIDED, is_optional=False, description=None
    ):
        if not is_optional:
            check.param_invariant(
                default_value == NO_DEFAULT_PROVIDED,
                'default_value',
                'required arguments should not specify default values',
            )

        self.dagster_type = check.inst_param(dagster_type, 'dagster_type', types.DagsterType)
        self.description = check.opt_str_param(description, 'description')
        self.is_optional = check.bool_param(is_optional, 'is_optional')
        self.default_value = default_value

    @property
    def default_provided(self):
        return self.default_value != NO_DEFAULT_PROVIDED
