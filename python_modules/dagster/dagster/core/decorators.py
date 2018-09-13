from collections import namedtuple
from functools import wraps
import inspect

from .definitions import (
    ConfigDefinition,
    DagsterInvalidDefinitionError,
    InputDefinition,
    OutputDefinition,
    Result,
    SolidDefinition,
    check,
)

if hasattr(inspect, 'signature'):
    funcsigs = inspect
else:
    import funcsigs

# Error messages are long
# pylint: disable=C0301


class MultipleResults(namedtuple('_MultipleResults', 'results')):
    '''A shortcut to output multiple results.

    Attributes:
      results (list[Result]): list of :py:class:`Result`

    Example:

    .. code-block:: python

        @solid(outputs=[
            OutputDefinition(name='foo'),
            OutputDefinition(name='bar'),
        ])
        def my_solid():
            return MultipleResults(
                Result('Barb', 'foo'),
                Result('Glarb', 'bar'),
            )


        @solid(outputs=[
            OutputDefinition(name='foo'),
            OutputDefinition(name='bar'),
        ])
        def my_solid_from_dict():
            return MultipleResults.from_dict({
              'foo': 'Barb',
              'bar': 'Glarb',
            })
    '''

    def __new__(cls, *results):
        return super(MultipleResults, cls).__new__(
            cls,
            # XXX(freiksenet): should check.list_param accept tuples from rest?
            check.opt_list_param(list(results), 'results', Result),
        )

    @staticmethod
    def from_dict(result_dict):
        '''Create MultipleResults object from a dictionary. Keys become result names'''
        check.dict_param(result_dict, 'result_dict', key_type=str)
        results = []
        for name, value in result_dict.items():
            results.append(Result(value, name))
        return MultipleResults(*results)


class _LambdaSolid(object):
    def __init__(
        self,
        name=None,
        inputs=None,
        output=None,
        description=None,
    ):
        self.name = check.opt_str_param(name, 'name')
        self.input_defs = check.opt_list_param(inputs, 'inputs', InputDefinition)
        self.output_def = check.inst_param(output, 'output', OutputDefinition)
        self.description = check.opt_str_param(description, 'description')

    def __call__(self, fn):
        check.callable_param(fn, 'fn')

        if not self.name:
            self.name = fn.__name__

        _validate_transform_fn(self.name, fn, self.input_defs)
        transform_fn = _create_lambda_solid_transform_wrapper(fn, self.input_defs, self.output_def)
        return SolidDefinition(
            name=self.name,
            inputs=self.input_defs,
            outputs=[self.output_def],
            transform_fn=transform_fn,
            description=self.description,
        )


class _Solid(object):
    def __init__(
        self,
        name=None,
        inputs=None,
        outputs=None,
        description=None,
        config_def=None,
    ):
        self.name = check.opt_str_param(name, 'name')
        self.input_defs = check.opt_list_param(inputs, 'inputs', InputDefinition)
        outputs = outputs or [OutputDefinition()]
        self.outputs = check.list_param(outputs, 'outputs', OutputDefinition)
        self.description = check.opt_str_param(description, 'description')
        self.config_def = check.opt_inst_param(config_def, 'config_def', ConfigDefinition)

    def __call__(self, fn):
        check.callable_param(fn, 'fn')

        if not self.name:
            self.name = fn.__name__

        _validate_transform_fn(self.name, fn, self.input_defs, ['info'])
        transform_fn = _create_solid_transform_wrapper(fn, self.input_defs, self.outputs)
        return SolidDefinition(
            name=self.name,
            inputs=self.input_defs,
            outputs=self.outputs,
            transform_fn=transform_fn,
            config_def=self.config_def,
            description=self.description,
        )


def lambda_solid(
    name=None,
    inputs=None,
    output=None,
    description=None,
):
    '''(decorator) Create a simple solid

    This shortcut allows the creation of simple solids that do not require
    configuration and whose implementations do not require a context.

    Lambda solids take inputs an and produce an output. The body of the function
    should return a single value.

    Args:
        name (str): Name of solid
        inputs (List[InputDefinition]): List of inputs
        output (OutputDefinition): The output of the solid. Defaults to OutputDefinition()
        description (str): Solid description

    .. code-block:: python

        @lambda_solid
        def hello_world():
            return 'hello'

        @lambda_solid(inputs=[InputDefinition(name="foo")])
        def hello_world(foo):
            return foo

    '''
    output = output or OutputDefinition()

    if callable(name):
        check.invariant(inputs is None)
        check.invariant(description is None)
        return _LambdaSolid(output=output)(name)

    return _LambdaSolid(
        name=name,
        inputs=inputs,
        output=output,
        description=description,
    )


def solid(
    name=None,
    inputs=None,
    outputs=None,
    config_def=None,
    description=None,
):
    '''(decorator) Create a solid with specified parameters.

    This shortcut simplifies core solid API by exploding arguments into kwargs of the
    transform function and omitting additional parameters when they are not needed.
    Parameters are otherwise as per :py:class:`SolidDefinition`.

    Decorated function is the transform function itself. Instead of having to yield
    result objects, transform support multiple simpler output types.

    1. Return a value. This is returned as a :py:class:`Result` for a single output solid.
    2. Return a :py:class:`Result`. Works like yielding result.
    3. Return a :py:class:`MultipleResults`. Works like yielding several results for
       multiple outputs. Useful for solids that have multiple outputs.
    4. Yield :py:class:`Result`. Same as default transform behaviour.

    Args:
        name (str): Name of solid
        inputs (List[InputDefinition]): List of inputs
        outputs (List[OutputDefinition]): List of outputs
        config_def (ConfigDefinition):
            The configuration for this solid.
        description (str): Description of this solid.

    Examples:

    .. code-block:: python

        @solid
        def hello_world(info):
            print('hello')

        @solid()
        def hello_world(info):
            print('hello')

        @solid(outputs=[OutputDefinition()])
        def hello_world(info):
            return {'foo': 'bar'}

        @solid(outputs=[OutputDefinition()])
        def hello_world(info):
            return Result(value={'foo': 'bar'})

        @solid(outputs=[OutputDefinition()])
        def hello_world(info):
            yield Result(value={'foo': 'bar'})

        @solid(outputs=[
            OutputDefinition(name="left"),
            OutputDefinition(name="right"),
        ])
        def hello_world(info):
            return MultipleResults.from_dict({
                'left': {'foo': 'left'},
                'right': {'foo': 'right'},
            })

        @solid(
            inputs=[InputDefinition(name="foo")],
            outputs=[OutputDefinition()]
        )
        def hello_world(info, foo):
            return foo

        @solid(
            inputs=[InputDefinition(name="foo")],
            outputs=[OutputDefinition()],
        )
        def hello_world(info, foo):
            info.context.info('log something')
            return foo

        @solid(
            inputs=[InputDefinition(name="foo")],
            outputs=[OutputDefinition()],
            config_def=ConfigDefinition(types.ConfigDictionary({'str_value' : Field(types.String)})),
        )
        def hello_world(info, foo):
            # info.config is a dictionary with 'str_value' key
            return foo + info.config['str_value']

    '''
    if callable(name):
        check.invariant(inputs is None)
        check.invariant(outputs is None)
        check.invariant(description is None)
        check.invariant(config_def is None)
        return _Solid()(name)

    return _Solid(
        name=name,
        inputs=inputs,
        outputs=outputs,
        config_def=config_def,
        description=description,
    )


def _create_lambda_solid_transform_wrapper(fn, input_defs, output_def):
    check.callable_param(fn, 'fn')
    check.list_param(input_defs, 'input_defs', of_type=InputDefinition)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    input_names = [input_def.name for input_def in input_defs]

    @wraps(fn)
    def transform(_info, inputs):
        kwargs = {}
        for input_name in input_names:
            kwargs[input_name] = inputs[input_name]

        result = fn(**kwargs)
        yield Result(value=result, output_name=output_def.name)

    return transform


def _create_solid_transform_wrapper(fn, input_defs, output_defs):
    check.callable_param(fn, 'fn')
    check.list_param(input_defs, 'input_defs', of_type=InputDefinition)
    check.list_param(output_defs, 'output_defs', of_type=OutputDefinition)

    input_names = [input_def.name for input_def in input_defs]

    @wraps(fn)
    def transform(info, inputs):
        kwargs = {}
        for input_name in input_names:
            kwargs[input_name] = inputs[input_name]

        result = fn(info, **kwargs)

        if inspect.isgenerator(result):
            for item in result:
                yield item
        else:
            if isinstance(result, Result):
                yield result
            elif isinstance(result, MultipleResults):
                for item in result.results:
                    yield item
            elif len(output_defs) == 1:
                yield Result(value=result, output_name=output_defs[0].name)
            elif result is not None:
                # XXX(freiksenet)
                raise Exception('Output for a solid without an output.')

    return transform


class FunctionValidationError(Exception):
    TYPES = {
        'vararg': 1,
        'missing_name': 2,
        'missing_positional': 3,
        'extra': 4,
    }

    def __init__(self, error_type, param=None, missing_names=None, **kwargs):
        super(FunctionValidationError, self).__init__(**kwargs)
        self.error_type = error_type
        self.param = param
        self.missing_names = missing_names


def _validate_transform_fn(solid_name, transform_fn, inputs, expected_positionals=None):
    check.str_param(solid_name, 'solid_name')
    check.callable_param(transform_fn, 'transform_fn')
    check.list_param(inputs, 'inputs', of_type=InputDefinition)
    expected_positionals = check.opt_list_param(
        expected_positionals,
        'expected_positionals',
        of_type=str,
    )

    names = set(inp.name for inp in inputs)
    # Currently being super strict about naming. Might be a good idea to relax. Starting strict.
    try:
        _validate_decorated_fn(transform_fn, names, expected_positionals)
    except FunctionValidationError as e:
        if e.error_type == FunctionValidationError.TYPES['vararg']:
            raise DagsterInvalidDefinitionError(
                "solid '{solid_name}' transform function has positional vararg parameter '{e.param}'. Transform functions should only have keyword arguments that match input names and a first positional parameter named 'info'.".
                format(solid_name=solid_name, e=e)
            )
        elif e.error_type == FunctionValidationError.TYPES['missing_name']:
            raise DagsterInvalidDefinitionError(
                "solid '{solid_name}' transform function has parameter '{e.param}' that is not one of the solid inputs. Transform functions should only have keyword arguments that match input names and a first positional parameter named 'info'.".
                format(solid_name=solid_name, e=e)
            )
        elif e.error_type == FunctionValidationError.TYPES['missing_positional']:
            raise DagsterInvalidDefinitionError(
                "solid '{solid_name}' transform function do not have required positional parameter '{e.param}'. Transform functions should only have keyword arguments that match input names and a first positional parameter named 'info'.".
                format(solid_name=solid_name, e=e)
            )
        elif e.error_type == FunctionValidationError.TYPES['extra']:
            undeclared_inputs_printed = ", '".join(e.missing_names)
            raise DagsterInvalidDefinitionError(
                "solid '{solid_name}' transform function do not have parameter(s) '{undeclared_inputs_printed}', which are in solid's inputs. Transform functions should only have keyword arguments that match input names and a first positional parameter named 'info'.".
                format(solid_name=solid_name, undeclared_inputs_printed=undeclared_inputs_printed)
            )
        else:
            raise e


def _validate_decorated_fn(fn, names, expected_positionals):
    used_inputs = set()
    has_kwargs = False

    signature = funcsigs.signature(fn)
    params = list(signature.parameters.values())

    expected_positional_params = params[0:len(expected_positionals)]
    other_params = params[len(expected_positionals):]

    for expected, actual in zip(expected_positionals, expected_positional_params):
        possible_names = [
            '_',
            expected,
            '_{expected}'.format(expected=expected),
            '{expected}_'.format(expected=expected),
        ]
        if (
            actual.kind not in [
                funcsigs.Parameter.POSITIONAL_OR_KEYWORD, funcsigs.Parameter.POSITIONAL_ONLY
            ]
        ) or (actual.name not in possible_names):
            raise FunctionValidationError(
                FunctionValidationError.TYPES['missing_positional'], param=expected
            )

    for param in other_params:
        if param.kind == funcsigs.Parameter.VAR_KEYWORD:
            has_kwargs = True
        elif param.kind == funcsigs.Parameter.VAR_POSITIONAL:
            raise FunctionValidationError(error_type=FunctionValidationError.TYPES['vararg'])

        else:
            if param.name not in names:
                raise FunctionValidationError(
                    FunctionValidationError.TYPES['missing_name'], param=param.name
                )
            else:
                used_inputs.add(param.name)

    undeclared_inputs = names - used_inputs
    if not has_kwargs and undeclared_inputs:
        raise FunctionValidationError(
            FunctionValidationError.TYPES['extra'], missing_names=undeclared_inputs
        )
