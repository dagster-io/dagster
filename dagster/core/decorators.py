import inspect
from functools import wraps
from dagster import check
from .definitions import (
    SolidDefinition, SourceDefinition, InputDefinition, OutputDefinition, MaterializationDefinition,
    create_no_materialization_output, DagsterInvalidDefinitionError
)


def with_context(fn):
    """Pass context as a first argument to a transform, source or materialization function.
    """
    return WithContext(fn)


class WithContext:
    def __init__(self, fn):
        self.fn = fn

    @property
    def has_context(self):
        return True


class Solid:
    def __init__(self, name=None, inputs=None, output=None):
        self.name = check.opt_str_param(name, 'name')
        self.inputs = check.opt_list_param(inputs, 'inputs', InputDefinition)

        check.opt_inst_param(output, 'output', OutputDefinition)
        if not output:
            output = create_no_materialization_output()
        self.output = output

    def __call__(self, fn):
        if not self.name:
            self.name = fn.__name__
        expect_context = getattr(fn, 'has_context', False)
        if expect_context:
            fn = fn.fn
        validate_transform_fn(self.name, fn, self.inputs, expect_context)
        transform_fn = _create_transform_wrapper(fn, self.inputs, expect_context)
        return SolidDefinition(
            name=self.name, inputs=self.inputs, output=self.output, transform_fn=transform_fn
        )


def solid(*, name=None, inputs=None, output=None):
    return Solid(name=name, inputs=inputs, output=output)


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


def validate_transform_fn(solid_name, transform_fn, inputs, expect_context=False):
    input_names = set(inp.name for inp in inputs)
    used_inputs = set()
    has_kwargs = False

    signature = inspect.signature(transform_fn)
    for param in signature.parameters.values():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            has_kwargs = True
        elif param.kind == inspect.Parameter.VAR_POSITIONAL:
            raise DagsterInvalidDefinitionError(
                f"solid '{solid_name}' transform function has positional vararg parameter '{param.name}'. Transform functions should only have keyword arguments that match input names and optionally a first positional parameter named 'context'."
            )
        else:
            if param.name in ('context', 'context_', '_context') and expect_context:
                pass
            elif param.name not in input_names:
                raise DagsterInvalidDefinitionError(
                    f"solid '{solid_name}' transform function has parameter '{param.name}' that is not one of the solid inputs. Transform functions should only have keyword arguments that match input names and optionally a first positional parameter named 'context'."
                )
            else:
                used_inputs.add(param.name)

    undeclared_inputs = input_names - used_inputs
    if not has_kwargs and undeclared_inputs:
        undeclared_inputs_printed = ", '".join(undeclared_inputs)
        raise DagsterInvalidDefinitionError(
            f"solid '{solid_name}' transform function do not have parameter(s) '{undeclared_inputs_printed}', which are in solid's inputs. Transform functions should only have keyword arguments that match input names and optionally a first positional parameter named 'context'."
        )


class Source:
    def __init__(self, name=None, argument_def_dict=None):
        self.source_type = check.str_param(name, 'name')
        self.argument_def_dict = check.opt_dict_param(argument_def_dict, 'argument_def_dict')

    def __call__(self, fn):
        include_context = getattr(fn, 'has_context', False)
        if include_context:
            fn = fn.fn

        @wraps(fn)
        def source_fn(context, arg_dict):
            if include_context:
                return fn(context, arg_dict)
            else:
                return fn(arg_dict)

        return SourceDefinition(
            source_type=self.source_type,
            source_fn=source_fn,
            argument_def_dict=self.argument_def_dict
        )


def source(*, name=None, argument_def_dict=None):
    return Source(name=name, argument_def_dict=argument_def_dict)


class Materialization:
    def __init__(self, name=None, argument_def_dict=None):
        self.materialization_type = check.str_param(name, 'name')
        self.argument_def_dict = check.opt_dict_param(argument_def_dict, 'argument_def_dict')

    def __call__(self, fn):
        include_context = getattr(fn, 'has_context', False)
        if include_context:
            fn = fn.fn

        @wraps(fn)
        def materialization_fn(context, arg_dict, data):
            if include_context:
                return fn(context, arg_dict, data)
            else:
                return fn(arg_dict, data)

        return MaterializationDefinition(
            materialization_type=self.materialization_type,
            materialization_fn=materialization_fn,
            argument_def_dict=self.argument_def_dict
        )


def materialization(*, name=None, argument_def_dict=None):
    return Materialization(name=name, argument_def_dict=argument_def_dict)
