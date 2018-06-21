from .definitions import Solid, SourceDefinition, MaterializationDefinition, create_no_materialization_output


def with_context(fn):
    """Pass context as a first argument to a transform, source or materialization function.
    """
    setattr(fn, '__with_context', True)
    return fn


class solid:
    def __init__(self, name=None, inputs=None, output=None):
        self.name = name

        if not inputs:
            inputs = []
        self.inputs = inputs

        if not output:
            output = create_no_materialization_output()
        self.output = output

    def __call__(self, fn):
        if not self.name:
            self.name = fn.__name__
        transform_fn = _create_transform_wrapper(
            fn, self.inputs, getattr(fn, '__with_context', False)
        )
        return Solid(
            name=self.name, inputs=self.inputs, output=self.output, transform_fn=transform_fn
        )


def _create_transform_wrapper(fn, inputs, include_context=False):
    input_names = [input.name for input in inputs]

    # check signature

    def transform(context, args):
        kwargs = {}
        for input_name in input_names:
            kwargs[input_name] = args[input_name]

        if include_context:
            return fn(context, **kwargs)
        else:
            return fn(**kwargs)

    return transform


class source:
    def __init__(self, source_type=None, argument_def_dict=None):
        self.source_type = source_type
        self.argument_def_dict = argument_def_dict

    def __call__(self, fn):
        include_context = getattr(fn, '__with_context', False)

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


def materialization():
    def __init__(self, materialization_type=None, argument_def_dict=None):
        self.materialization_type = materialization_type
        self.argument_def_dict = argument_def_dict

    def __call__(self, fn):
        include_context = getattr(fn, '__with_context', False)

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
