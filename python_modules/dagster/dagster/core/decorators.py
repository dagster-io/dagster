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

from .types import Any

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

        @transform(outputs=[
            OutputDefinition(name='foo'),
            OutputDefinition(name='bar'),
        ])
        def my_solid():
            return MultipleResults([
                Result('Barb', 'foo'),
                Result('Glarb', 'bar'),
            ])


        @transform(outputs=[
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


def with_context(fn):
    '''(decorator) Pass context as a first argument to a transform.

    Example:

    .. code-block:: python

        @transform()
        @with_context
        def my_solid(context):
            pass
    '''
    return _WithContext(fn)


class _WithContext(object):
    def __init__(self, fn):
        self.fn = fn

    @property
    def has_context(self):
        return True


DecoratorData = namedtuple('DecoratorData', 'name input_defs output_defs config_def description')


def create_decorator_data(
    name=None,
    inputs=None,
    outputs=None,
    output=None,
    description=None,
    config_def=None,
):
    check.opt_inst_param(config_def, 'config_def', ConfigDefinition)

    if output is not None and outputs is None:
        output_defs = [check.opt_inst_param(output, 'output', OutputDefinition)]
    else:
        output_defs = check.opt_list_param(outputs, 'outputs', OutputDefinition)

    return DecoratorData(
        name=check.opt_str_param(name, 'name'),
        input_defs=check.opt_list_param(inputs, 'inputs', InputDefinition),
        output_defs=output_defs,
        description=check.opt_str_param(description, 'description'),
        config_def=check.opt_inst_param(config_def, 'config_def', ConfigDefinition),
    )


def solid(name=None, inputs=None, output=None, outputs=None, description=None, config_def=None):
    if callable(name):
        check.invariant(inputs is None)
        check.invariant(output is None)
        check.invariant(outputs is None)
        check.invariant(description is None)
        check.invariant(config_def is None)
        return _SolidDecoratorFunctor()(name)
    else:
        return _SolidDecoratorFunctor(
            name=name,
            inputs=inputs,
            output=output,
            outputs=outputs,
            description=description,
            config_def=config_def,
        )


class _SolidDecoratorFunctor(object):
    def __init__(
        self,
        name=None,
        inputs=None,
        outputs=None,
        output=None,
        description=None,
        config_def=None,
    ):
        check.opt_inst_param(config_def, 'config_def', ConfigDefinition)

        self.decorator_data = create_decorator_data(
            name,
            inputs,
            outputs,
            output,
            description,
            config_def,
        )

    def __call__(self, fn):
        name = self.decorator_data.name if self.decorator_data.name else fn.__name__
        transform_fn = _create_solid_fn_wrapper(fn, self.decorator_data.output_defs)

        return SolidDefinition(
            name=name,
            inputs=self.decorator_data.input_defs,
            outputs=self.decorator_data.output_defs,
            transform_fn=transform_fn,
            config_def=self.decorator_data.config_def,
            description=self.decorator_data.description,
        )


class _TransformDecoratorFunctor(object):
    def __init__(
        self,
        name=None,
        inputs=None,
        outputs=None,
        output=None,
        description=None,
        config_def=None,
    ):
        self.decorator_data = create_decorator_data(
            name,
            inputs,
            outputs,
            output,
            description,
            config_def,
        )

    def __call__(self, fn):
        expect_context = getattr(fn, 'has_context', False)
        if expect_context:
            fn = check.inst(fn, _WithContext).fn

        name = self.decorator_data.name if self.decorator_data.name else fn.__name__

        _validate_transform_fn(name, fn, self.decorator_data.input_defs, expect_context)
        transform_fn = _create_transform_fn_wrapper(
            fn,
            self.decorator_data.input_defs,
            self.decorator_data.output_defs,
            expect_context,
        )
        return SolidDefinition(
            name=name,
            inputs=self.decorator_data.input_defs,
            outputs=self.decorator_data.output_defs,
            transform_fn=transform_fn,
            config_def=self.decorator_data.config_def,
            description=self.decorator_data.description,
        )


def transform(name=None, inputs=None, output=None, outputs=None, description=None):
    '''(decorator) Create a transform-flavored solid with specified parameters.

    This shortcut simplifies core solid API by exploding arguments into kwargs of the
    transform function and omitting additional parameters when they are not needed.
    Parameters are otherwise as per :py:class:`SolidDefinition`. By using
    :py:function:`with_context` one can request context object to be passed too.

    Decorated function is the transform function itself. Instead of having to yield
    result objects, transform support multiple simpler output types.

    1. Return a value. This is returned as a :py:class:`Result` for a single output solid.
    2. Return a :py:class:`Result`. Works like yielding result.
    3. Return a :py:class:`MultipleResults`. Works like yielding several results for
       multiple outputs. Useful for solids that have multiple outputs.
    4. Yield :py:class:`Result`. Same as default transform behaviour.

    Examples:

    .. code-block:: python

        @transform(outputs=[OutputDefinition()])
        def hello_world():
            return {'foo': 'bar'}

        @transform(output=OutputDefinition())
        def hello_world():
            return Result(value={'foo': 'bar'})

        @transform(output=OutputDefinition())
        def hello_world():
            yield Result(value={'foo': 'bar'})

        @transform(outputs=[
            OutputDefinition(name="left"),
            OutputDefinition(name="right"),
        ])
        def hello_world():
            return MultipleResults.from_dict({
                'left': {'foo': 'left'},
                'right': {'foo': 'right'},
            })

        @transform(
            inputs=[InputDefinition(name="foo_to_foo")],
            outputs=[OutputDefinition()]
        )
        def hello_world(foo_to_foo):
            return foo_to_foo

        @transform(
            inputs=[InputDefinition(name="foo_to_foo")],
            outputs=[OutputDefinition()]
        )
        @with_context
        def hello_world(context, foo_to_foo):
            return foo_to_foo
    '''
    if callable(name):
        return _TransformDecoratorFunctor()(name)
    else:
        return _TransformDecoratorFunctor(
            name=name,
            inputs=inputs,
            output=output,
            outputs=outputs,
            description=description,
        )


def _yield_results(transform_output, output_defs):
    if inspect.isgenerator(transform_output):
        for item in transform_output:
            yield item
    else:
        if isinstance(transform_output, Result):
            yield transform_output
        elif isinstance(transform_output, MultipleResults):
            for item in transform_output.results:
                yield item
        elif len(output_defs) == 1:
            yield Result(value=transform_output, output_name=output_defs[0].name)
        elif transform_output is not None:
            # XXX(freiksenet)
            raise Exception('Output for a solid without an output.')


def _create_solid_fn_wrapper(fn, output_defs):
    check.callable_param(fn, 'fn')
    check.list_param(output_defs, 'output_defs', OutputDefinition)

    @wraps(fn)
    def _transform(context, inputs, conf):
        transform_output = fn(context, inputs, conf)

        for item in _yield_results(transform_output, output_defs):
            yield item

    return _transform


def _create_transform_fn_wrapper(fn, input_defs, output_defs, include_context=False):
    check.callable_param(fn, 'fn')
    check.list_param(input_defs, 'input_defs', InputDefinition)
    check.list_param(output_defs, 'output_defs', OutputDefinition)
    check.bool_param(include_context, 'include_context')

    input_names = [input_def.name for input_def in input_defs]

    @wraps(fn)
    def _transform(context, inputs, _conf):
        kwargs = {}
        for input_name in input_names:
            kwargs[input_name] = inputs[input_name]

        if include_context:
            transform_output = fn(context, **kwargs)
        else:
            transform_output = fn(**kwargs)

        for item in _yield_results(transform_output, output_defs):
            yield item

    return _transform


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


def _validate_transform_fn(solid_name, transform_fn, inputs, expect_context=False):
    names = set(inp.name for inp in inputs)
    if expect_context:
        expected_positionals = ('context', )
    else:
        expected_positionals = ()
    try:
        _validate_decorated_fn(transform_fn, names, expected_positionals)
    except FunctionValidationError as e:
        if e.error_type == FunctionValidationError.TYPES['vararg']:
            raise DagsterInvalidDefinitionError(
                "solid '{solid_name}' transform function has positional vararg parameter '{e.param}'. Transform functions should only have keyword arguments that match input names and optionally a first positional parameter named 'context'.".
                format(solid_name=solid_name, e=e)
            )
        elif e.error_type == FunctionValidationError.TYPES['missing_name']:
            raise DagsterInvalidDefinitionError(
                "solid '{solid_name}' transform function has parameter '{e.param}' that is not one of the solid inputs. Transform functions should only have keyword arguments that match input names and optionally a first positional parameter named 'context'.".
                format(solid_name=solid_name, e=e)
            )
        elif e.error_type == FunctionValidationError.TYPES['missing_positional']:
            raise DagsterInvalidDefinitionError(
                "solid '{solid_name}' transform function do not have required positional parameter '{e.param}'. Transform functions should only have keyword arguments that match input names and optionally a first positional parameter named 'context'.".
                format(solid_name=solid_name, e=e)
            )
        elif e.error_type == FunctionValidationError.TYPES['extra']:
            undeclared_inputs_printed = ", '".join(e.missing_names)
            raise DagsterInvalidDefinitionError(
                "solid '{solid_name}' transform function do not have parameter(s) '{undeclared_inputs_printed}', which are in solid's inputs. Transform functions should only have keyword arguments that match input names and optionally a first positional parameter named 'context'.".
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
            expected, '_{expected}'.format(expected=expected),
            '{expected}_'.format(expected=expected)
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
