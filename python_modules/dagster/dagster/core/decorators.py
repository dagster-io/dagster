import inspect
from collections import namedtuple
from functools import wraps
from dagster import check
from .definitions import (
    SolidDefinition,
    InputDefinition,
    OutputDefinition,
    DagsterInvalidDefinitionError,
    Result,
    check_argument_def_dict,
)

# Error messages are long
# pylint: disable=C0301


class MultipleResults(namedtuple('_MultipleResults', 'results')):
    def __new__(cls, results):
        return super(MultipleResults, cls).__new__(
            cls,
            check.list_param(results, 'results', Result),
        )


def with_context(fn):
    """Pass context as a first argument to a transform.
    """
    return _WithContext(fn)


class _WithContext:
    def __init__(self, fn):
        self.fn = fn

    @property
    def has_context(self):
        return True


class _Solid:
    def __init__(
        self,
        name=None,
        inputs=None,
        outputs=None,
        description=None,
        config_def=None,
    ):
        self.name = check.opt_str_param(name, 'name')
        self.inputs = check.opt_list_param(inputs, 'inputs', InputDefinition)
        self.outputs = check.opt_list_param(outputs, 'outputs', OutputDefinition)
        self.description = check.opt_str_param(description, 'description')
        if config_def:
            self.config_def = check_argument_def_dict(config_def)
        else:
            self.config_def = {}

    def __call__(self, fn):
        expect_context = getattr(fn, 'has_context', False)
        if expect_context:
            fn = fn.fn

        if not self.name:
            self.name = fn.__name__

        _validate_transform_fn(self.name, fn, self.inputs, expect_context)
        transform_fn = _create_transform_wrapper(fn, self.inputs, self.outputs, expect_context)
        return SolidDefinition(
            name=self.name,
            inputs=self.inputs,
            outputs=self.outputs,
            transform_fn=transform_fn,
            config_def=self.config_def,
            description=self.description,
        )


def solid(*, name=None, inputs=None, outputs=None, description=None):
    return _Solid(name=name, inputs=inputs, outputs=outputs, description=description)


def _create_transform_wrapper(fn, inputs, outputs, include_context=False):
    input_names = [input.name for input in inputs]

    @wraps(fn)
    def transform(context, args, config):
        kwargs = {}
        for input_name in input_names:
            kwargs[input_name] = args[input_name]

        if include_context:
            result = fn(context, **kwargs)
        else:
            result = fn(**kwargs)
        if inspect.isgenerator(result):
            yield from result
        else:
            if isinstance(result, Result):
                yield result
            elif isinstance(result, MultipleResults):
                yield from MultipleResults.results
            elif len(outputs) == 1:
                yield Result(value=result, output_name=outputs[0].name)
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
        super().__init__(**kwargs)
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
                f"solid '{solid_name}' transform function has positional vararg parameter '{e.param}'. Transform functions should only have keyword arguments that match input names and optionally a first positional parameter named 'context'."
            )
        elif e.error_type == FunctionValidationError.TYPES['missing_name']:
            raise DagsterInvalidDefinitionError(
                f"solid '{solid_name}' transform function has parameter '{e.param}' that is not one of the solid inputs. Transform functions should only have keyword arguments that match input names and optionally a first positional parameter named 'context'."
            )
        elif e.error_type == FunctionValidationError.TYPES['missing_positional']:
            raise DagsterInvalidDefinitionError(
                f"solid '{solid_name}' transform function do not have required positional parameter '{e.param}'. Transform functions should only have keyword arguments that match input names and optionally a first positional parameter named 'context'."
            )
        elif e.error_type == FunctionValidationError.TYPES['extra']:
            undeclared_inputs_printed = ", '".join(e.missing_names)
            raise DagsterInvalidDefinitionError(
                f"solid '{solid_name}' transform function do not have parameter(s) '{undeclared_inputs_printed}', which are in solid's inputs. Transform functions should only have keyword arguments that match input names and optionally a first positional parameter named 'context'."
            )
        else:
            raise e


def _validate_decorated_fn(fn, names, expected_positionals):
    used_inputs = set()
    has_kwargs = False

    signature = inspect.signature(fn)
    params = list(signature.parameters.values())

    expected_positional_params = params[0:len(expected_positionals)]
    other_params = params[len(expected_positionals):]

    for expected, actual in zip(expected_positionals, expected_positional_params):
        possible_names = [expected, f'_{expected}', f'{expected}_']
        if (
            actual.kind not in [
                inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.POSITIONAL_ONLY
            ]
        ) or (actual.name not in possible_names):
            raise FunctionValidationError(
                FunctionValidationError.TYPES['missing_positional'], param=expected
            )

    for param in other_params:
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            has_kwargs = True
        elif param.kind == inspect.Parameter.VAR_POSITIONAL:
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
