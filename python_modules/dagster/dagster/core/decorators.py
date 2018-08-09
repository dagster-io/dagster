import inspect
from functools import wraps
from dagster import check
from .definitions import (
    SolidDefinition,
    SourceDefinition,
    InputDefinition,
    OutputDefinition,
    MaterializationDefinition,
    DagsterInvalidDefinitionError,
)

# Error messages are long
# pylint: disable=C0301


def with_context(fn):
    """Pass context as a first argument to a transform, source or materialization function.
    """
    return _WithContext(fn)


class _WithContext:
    def __init__(self, fn):
        self.fn = fn

    @property
    def has_context(self):
        return True


class _Solid:
    def __init__(self, name=None, inputs=None, output=None, description=None):
        self.name = check.opt_str_param(name, 'name')
        self.inputs = check.opt_list_param(inputs, 'inputs', InputDefinition)

        check.opt_inst_param(output, 'output', OutputDefinition)
        if not output:
            output = OutputDefinition()
        self.output = output
        self.description = check.opt_str_param(description, 'description')

    def __call__(self, fn):
        expect_context = getattr(fn, 'has_context', False)
        if expect_context:
            fn = fn.fn

        if not self.name:
            self.name = fn.__name__

        _validate_transform_fn(self.name, fn, self.inputs, expect_context)
        transform_fn = _create_transform_wrapper(fn, self.inputs, expect_context)
        return SolidDefinition(
            name=self.name,
            inputs=self.inputs,
            output=self.output,
            transform_fn=transform_fn,
            description=self.description,
        )


def solid(*, name=None, inputs=None, output=None, description=None):
    return _Solid(name=name, inputs=inputs, output=output, description=description)


def _create_transform_wrapper(fn, inputs, include_context=False):
    input_names = [input.name for input in inputs]

    @wraps(fn)
    def transform(context, args):
        kwargs = {}
        for input_name in input_names:
            kwargs[input_name] = args[input_name]

        if include_context:
            return fn(context, **kwargs)
        else:
            return fn(**kwargs)

    return transform


class _Source:
    def __init__(self, name=None, argument_def_dict=None, description=None):
        self.source_type = check.opt_str_param(name, 'name')
        self.argument_def_dict = check.opt_dict_param(argument_def_dict, 'argument_def_dict')
        self.description = check.opt_str_param(description, 'description')

    def __call__(self, fn):
        include_context = getattr(fn, 'has_context', False)
        if include_context:
            fn = fn.fn

        if not self.source_type:
            self.source_type = fn.__name__

        _validate_source_fn(fn, self.source_type, self.argument_def_dict, include_context)
        source_fn = _create_source_wrapper(fn, self.argument_def_dict, include_context)

        return SourceDefinition(
            source_type=self.source_type,
            source_fn=source_fn,
            argument_def_dict=self.argument_def_dict,
            description=self.description,
        )


def source(*, name=None, argument_def_dict=None, description=None):
    return _Source(name=name, argument_def_dict=argument_def_dict, description=description)


def _create_source_wrapper(fn, arg_def_dict, include_context=False):
    arg_names = arg_def_dict.keys()

    @wraps(fn)
    def source_fn(context, args):
        kwargs = {}
        for arg in arg_names:
            kwargs[arg] = args[arg]

        if include_context:
            return fn(context, **kwargs)
        else:
            return fn(**kwargs)

    return source_fn


class _Materialization:
    def __init__(self, name=None, argument_def_dict=None, description=None):
        self.name = check.opt_str_param(name, 'name')
        self.argument_def_dict = check.opt_dict_param(argument_def_dict, 'argument_def_dict')
        self.description = check.opt_str_param(description, 'description')

    def __call__(self, fn):
        include_context = getattr(fn, 'has_context', False)
        if include_context:
            fn = fn.fn

        if not self.name:
            self.name = fn.__name__

        _validate_materialization_fn(fn, self.name, self.argument_def_dict, include_context)
        materialization_fn = _create_materialization_wrapper(
            fn, self.argument_def_dict, include_context
        )

        return MaterializationDefinition(
            name=self.name,
            materialization_fn=materialization_fn,
            argument_def_dict=self.argument_def_dict,
            description=self.description,
        )


def materialization(*, name=None, argument_def_dict=None, description=None):
    return _Materialization(
        name=name,
        argument_def_dict=argument_def_dict,
        description=description,
    )


def _create_materialization_wrapper(fn, arg_def_dict, include_context=False):
    arg_names = arg_def_dict.keys()

    @wraps(fn)
    def materialization_fn(context, args, data):
        kwargs = {}
        for arg in arg_names:
            kwargs[arg] = args[arg]

        if include_context:
            return fn(context, data, **kwargs)
        else:
            return fn(data, **kwargs)

    return materialization_fn


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


def _validate_source_fn(fn, source_name, arg_def_dict, expect_context=False):
    names = set(arg_def_dict.keys())
    if expect_context:
        expected_positionals = ('context', )
    else:
        expected_positionals = ()
    try:
        _validate_decorated_fn(fn, names, expected_positionals)
    except FunctionValidationError as e:
        if e.error_type == FunctionValidationError.TYPES['vararg']:
            raise DagsterInvalidDefinitionError(
                f"source '{source_name}' source function has positional vararg parameter '{e.param}'. Source functions should only have keyword arguments that match argument definition names and optionally a first positional parameter named 'context'."
            )
        elif e.error_type == FunctionValidationError.TYPES['missing_name']:
            raise DagsterInvalidDefinitionError(
                f"source '{source_name}' source function has parameter '{e.param}' that is not one of the source arguments. Source functions should only have keyword arguments that match argument definition names and optionally a first positional parameter named 'context'."
            )
        elif e.error_type == FunctionValidationError.TYPES['missing_positional']:
            raise DagsterInvalidDefinitionError(
                f"source '{source_name}' transform function do not have required positional argument '{e.param}'. Source functions should only have keyword arguments that match argument definition names and optionally a first positional parameter named 'context"
            )
        elif e.error_type == FunctionValidationError.TYPES['extra']:
            undeclared_inputs_printed = ", '".join(e.missing_names)
            raise DagsterInvalidDefinitionError(
                f"source '{source_name}' transform function do not have parameter(s) '{undeclared_inputs_printed}', which are in source's argument definitions.  Source functions should only have keyword arguments that match argument definition names and optionally a first positional parameter named 'context'"
            )
        else:
            raise e


def _validate_materialization_fn(fn, materialization_name, arg_def_dict, expect_context=False):
    names = set(arg_def_dict.keys())
    if expect_context:
        expected_positionals = ('context', 'data')
    else:
        expected_positionals = ('data', )
    try:
        _validate_decorated_fn(fn, names, expected_positionals)
    except FunctionValidationError as e:
        if e.error_type == FunctionValidationError.TYPES['vararg']:
            raise DagsterInvalidDefinitionError(
                f"materialization '{materialization_name}' materialization function has positional vararg parameter '{e.param}'. Materialization functions should only have keyword arguments that match argument definition names, positional parameter 'data' and optionally a first positional parameter named 'context'."
            )
        elif e.error_type == FunctionValidationError.TYPES['missing_name']:
            raise DagsterInvalidDefinitionError(
                f"materialization '{materialization_name}' transform function has parameter '{e.param}' that is not one of the materialization's argument definitions. Materialization functions should only have keyword arguments that match argument definition names, positional parameter 'data' and optionally a first positional parameter named 'context'."
            )
        elif e.error_type == FunctionValidationError.TYPES['missing_positional']:
            raise DagsterInvalidDefinitionError(
                f"materialization '{materialization_name}' materialization function do not have parameter {e.param}'. Materialization functions should only have keyword arguments that match argument definition names, positional parameter 'data' and optionally a first positional parameter named 'context'."
            )
        elif e.error_type == FunctionValidationError.TYPES['extra']:
            undeclared_inputs_printed = ", '".join(e.missing_names)
            raise DagsterInvalidDefinitionError(
                f"materialization '{materialization_name}' materialization function do not have parameter(s) '{undeclared_inputs_printed}', which are in materialization's argument definitinio. Materialization functions should only have keyword arguments that match argument definition names, positional parameter 'data' and optionally a first positional parameter named 'context'."
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
