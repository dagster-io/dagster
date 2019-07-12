import inspect
from functools import wraps

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError

from .composition import (
    InputMappingNode,
    composite_mapping_from_output,
    enter_composition,
    exit_composition,
)
from .config import ConfigMapping, resolve_config_field
from .events import ExpectationResult, Output, Materialization
from .input import InputDefinition
from .inference import (
    infer_input_definitions_for_lambda_solid,
    infer_input_definitions_for_solid,
    infer_input_definitions_for_composite_solid,
    infer_output_definitions,
    has_explicit_return_type,
)
from .mode import ModeDefinition
from .output import OutputDefinition
from .pipeline import PipelineDefinition
from .preset import PresetDefinition
from .solid import CompositeSolidDefinition, SolidDefinition

if hasattr(inspect, 'signature'):
    funcsigs = inspect
else:
    import funcsigs

# Error messages are long
# pylint: disable=C0301


class _LambdaSolid(object):
    def __init__(self, name=None, input_defs=None, output_def=None, description=None):
        self.name = check.opt_str_param(name, 'name')
        self.input_defs = check.opt_nullable_list_param(input_defs, 'input_defs', InputDefinition)
        self.output_def = check.opt_inst_param(output_def, 'output_def', OutputDefinition)
        self.description = check.opt_str_param(description, 'description')

    def __call__(self, fn):
        check.callable_param(fn, 'fn')

        if not self.name:
            self.name = fn.__name__

        input_defs = (
            self.input_defs
            if self.input_defs is not None
            else infer_input_definitions_for_lambda_solid(self.name, fn)
        )
        output_def = (
            self.output_def
            if self.output_def is not None
            else infer_output_definitions('@lambda_solid', self.name, fn)[0]
        )

        _validate_solid_fn(self.name, fn, input_defs)
        compute_fn = _create_lambda_solid_compute_wrapper(fn, input_defs, output_def)

        return SolidDefinition(
            name=self.name,
            input_defs=input_defs,
            output_defs=[output_def],
            compute_fn=compute_fn,
            description=self.description,
        )


class _Solid(object):
    def __init__(
        self,
        name=None,
        input_defs=None,
        output_defs=None,
        description=None,
        required_resource_keys=None,
        config_field=None,
        metadata=None,
    ):
        self.name = check.opt_str_param(name, 'name')
        self.input_defs = check.opt_nullable_list_param(input_defs, 'input_defs', InputDefinition)
        self.output_defs = check.opt_nullable_list_param(
            output_defs, 'output_defs', OutputDefinition
        )

        self.description = check.opt_str_param(description, 'description')

        # resources will be checked within SolidDefinition
        self.required_resource_keys = required_resource_keys

        # config_field will be checked within SolidDefinition
        self.config_field = config_field

        # metadata will be checked within ISolidDefinition
        self.metadata = metadata

    def __call__(self, fn):
        check.callable_param(fn, 'fn')

        if not self.name:
            self.name = fn.__name__

        input_defs = (
            self.input_defs
            if self.input_defs is not None
            else infer_input_definitions_for_solid(self.name, fn)
        )
        output_defs = (
            self.output_defs
            if self.output_defs is not None
            else infer_output_definitions('@solid', self.name, fn)
        )

        _validate_solid_fn(self.name, fn, input_defs, [('context',)])
        compute_fn = _create_solid_compute_wrapper(fn, input_defs, output_defs)

        return SolidDefinition(
            name=self.name,
            input_defs=input_defs,
            output_defs=output_defs,
            compute_fn=compute_fn,
            config_field=self.config_field,
            description=self.description,
            required_resource_keys=self.required_resource_keys,
            metadata=self.metadata,
        )


def lambda_solid(name=None, description=None, input_defs=None, output_def=None):
    '''Create a simple solid from the decorated function.

    This shortcut allows the creation of simple solids that do not require
    configuration and whose implementations do not require a context.

    Lambda solids take input_defs and produce a single output. The body of the function
    should return a single value.

    Args:
        name (str): Name of solid.
        description (str): Solid description.
        input_defs (List[InputDefinition]): List of input_defs.
        output_def (OutputDefinition): The output of the solid. Defaults to ``OutputDefinition()``.

    Examples:

        .. code-block:: python

            @lambda_solid
            def hello_world():
                return 'hello'

            @lambda_solid(
                input_defs=[InputDefinition(name='foo', str)],
                output_def=OutputDefinition(str)
            )
            def hello_world(foo):
                # explictly type and name inputs and outputs
                return foo

            @lambda_solid
            def hello_world(foo: str) -> str:
                # same as above inferred from signature
                return foo

    '''
    if callable(name):
        check.invariant(input_defs is None)
        check.invariant(description is None)
        return _LambdaSolid(output_def=output_def)(name)

    return _LambdaSolid(
        name=name, input_defs=input_defs, output_def=output_def, description=description
    )


def solid(
    name=None,
    description=None,
    input_defs=None,
    output_defs=None,
    config_field=None,
    config=None,
    required_resource_keys=None,
    metadata=None,
):
    '''Create a solid with specified parameters from the decorated function.

    This shortcut simplifies the core solid API by exploding arguments into kwargs of the
    compute function and omitting additional parameters when they are not needed. Input
    and output definitions will be inferred from the type signature of the decorated
    function if not explicitly provided.

    The decorated function will be used as the solid's compute function. Unlike in the core API,
        the expectations for the compute function are more flexible, it can:

    1. Return a value. This is returned as an :py:class:`Output` for a single output solid.
    2. Return an :py:class:`Output`. Works like yielding that :py:class:`Output` .
    3. Yield :py:class:`Output` or other event objects. Same as default compute behaviour.

    Args:
        name (str): Name of solid.
        description (str): Description of this solid.
        input_defs (Optiona[List[InputDefinition]]):
            List of input_defs. Inferred from typehints if not provided.
        output_defs (Optional[List[OutputDefinition]]):
            List of output_defs. Inferred from typehints if not provided.
        config (Dict[str, Field]):
            Defines the schema of configuration data provided to the solid via context.
        config_field (Field):
            Used in the rare case of a top level config type other than a dictionary.

            Only one of config or config_field can be provided.
        required_resource_keys (set[str]):
            Set of resource handles required by this solid.

    Examples:

        .. code-block:: python

            @solid
            def hello_world(_context):
                print('hello')

            @solid()
            def hello_world(_context):
                print('hello')

            @solid
            def hello_world(_context):
                return {'foo': 'bar'}

            @solid
            def hello_world(_context):
                return Output(value={'foo': 'bar'})

            @solid
            def hello_world(_context):
                yield Output(value={'foo': 'bar'})

            @solid
            def hello_world(_context, foo):
                return foo

            @solid(
                input_defs=[InputDefinition(name="foo", str)],
                output_defs=[OutputDefinition(str)]
            )
            def hello_world(_context, foo):
                # explictly type and name inputs and outputs
                return foo

            @solid
            def hello_world(_context, foo: str) -> str:
                # same as above inferred from signature
                return foo

            @solid
            def hello_world(context, foo):
                context.log.info('log something')
                return foo

            @solid(
                config={'str_value' : Field(str)}
            )
            def hello_world(context, foo):
                # context.solid_config is a dictionary with 'str_value' key
                return foo + context.solid_config['str_value']

    '''
    # This case is for when decorator is used bare, without arguments. e.g. @solid versus @solid()
    if callable(name):
        check.invariant(input_defs is None)
        check.invariant(output_defs is None)
        check.invariant(description is None)
        check.invariant(config_field is None)
        check.invariant(config is None)
        check.invariant(required_resource_keys is None)
        check.invariant(metadata is None)
        return _Solid()(name)

    return _Solid(
        name=name,
        input_defs=input_defs,
        output_defs=output_defs,
        config_field=resolve_config_field(config_field, config, '@solid'),
        description=description,
        required_resource_keys=required_resource_keys,
        metadata=metadata,
    )


def _create_lambda_solid_compute_wrapper(fn, input_defs, output_def):
    check.callable_param(fn, 'fn')
    check.list_param(input_defs, 'input_defs', of_type=InputDefinition)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    input_names = [
        input_def.name for input_def in input_defs if not input_def.runtime_type.is_nothing
    ]

    @wraps(fn)
    def compute(_context, input_defs):
        kwargs = {}
        for input_name in input_names:
            kwargs[input_name] = input_defs[input_name]

        result = fn(**kwargs)
        yield Output(value=result, output_name=output_def.name)

    return compute


def _create_solid_compute_wrapper(fn, input_defs, output_defs):
    check.callable_param(fn, 'fn')
    check.list_param(input_defs, 'input_defs', of_type=InputDefinition)
    check.list_param(output_defs, 'output_defs', of_type=OutputDefinition)

    input_names = [
        input_def.name for input_def in input_defs if not input_def.runtime_type.is_nothing
    ]

    @wraps(fn)
    def compute(context, input_defs):
        kwargs = {}
        for input_name in input_names:
            kwargs[input_name] = input_defs[input_name]

        result = fn(context, **kwargs)

        if inspect.isgenerator(result):
            for item in result:
                yield item
        else:
            if isinstance(result, (Materialization, ExpectationResult)):
                raise DagsterInvariantViolationError(
                    (
                        'Error in solid {solid_name}: If you are returning a Materialization '
                        'or an ExpectationResult from solid you must yield them to avoid '
                        'ambiguity with an implied result from returning a value.'.format(
                            solid_name=context.solid.name
                        )
                    )
                )

            if isinstance(result, Output):
                yield result
            elif len(output_defs) == 1:
                yield Output(value=result, output_name=output_defs[0].name)
            elif result is not None:
                if not output_defs:
                    raise DagsterInvariantViolationError(
                        (
                            'Error in solid {solid_name}: Unexpectedly returned output {result} '
                            'of type {type_}. Solid is explicitly defined to return no '
                            'results.'
                        ).format(solid_name=context.solid.name, result=result, type_=type(result))
                    )

                raise DagsterInvariantViolationError(
                    (
                        'Error in solid {solid_name}: Solid unexpectedly returned '
                        'output {result} of type {type_}. Should '
                        'be a generator, containing or yielding '
                        '{n_results} results: {{{expected_results}}}.'
                    ).format(
                        solid_name=context.solid.name,
                        result=result,
                        type_=type(result),
                        n_results=len(output_defs),
                        expected_results=', '.join(
                            [
                                '\'{result_name}\': {runtime_type}'.format(
                                    result_name=output_def.name,
                                    runtime_type=output_def.runtime_type,
                                )
                                for output_def in output_defs
                            ]
                        ),
                    )
                )

    return compute


class FunctionValidationError(Exception):
    TYPES = {'vararg': 1, 'missing_name': 2, 'missing_positional': 3, 'extra': 4}

    def __init__(self, error_type, param=None, missing_names=None, **kwargs):
        super(FunctionValidationError, self).__init__(**kwargs)
        self.error_type = error_type
        self.param = param
        self.missing_names = missing_names


def _validate_solid_fn(
    solid_name, compute_fn, input_defs, expected_positionals=None, exclude_nothing=True
):
    check.str_param(solid_name, 'solid_name')
    check.callable_param(compute_fn, 'compute_fn')
    check.list_param(input_defs, 'input_defs', of_type=InputDefinition)
    expected_positionals = check.opt_list_param(
        expected_positionals, 'expected_positionals', of_type=(str, tuple)
    )
    if exclude_nothing:
        names = set(inp.name for inp in input_defs if not inp.runtime_type.is_nothing)
        nothing_names = set(inp.name for inp in input_defs if inp.runtime_type.is_nothing)
    else:
        names = set(inp.name for inp in input_defs)
        nothing_names = set()

    # Currently being super strict about naming. Might be a good idea to relax. Starting strict.
    try:
        _validate_decorated_fn(compute_fn, names, expected_positionals)
    except FunctionValidationError as e:
        if e.error_type == FunctionValidationError.TYPES['vararg']:
            raise DagsterInvalidDefinitionError(
                "solid '{solid_name}' decorated function has positional vararg parameter "
                "'{e.param}'. Solid functions should only have keyword arguments that match "
                "input names and a first positional parameter named 'context'.".format(
                    solid_name=solid_name, e=e
                )
            )
        elif e.error_type == FunctionValidationError.TYPES['missing_name']:
            if e.param in nothing_names:
                raise DagsterInvalidDefinitionError(
                    "solid '{solid_name}' decorated function has parameter '{e.param}' that is "
                    "one of the solid input_defs of type 'Nothing' which should not be included since "
                    "no data will be passed for it. ".format(solid_name=solid_name, e=e)
                )
            else:
                raise DagsterInvalidDefinitionError(
                    "solid '{solid_name}' decorated function has parameter '{e.param}' that is not "
                    "one of the solid input_defs. Solid functions should only have keyword arguments "
                    "that match input names and a first positional parameter named 'context'.".format(
                        solid_name=solid_name, e=e
                    )
                )
        elif e.error_type == FunctionValidationError.TYPES['missing_positional']:
            raise DagsterInvalidDefinitionError(
                "solid '{solid_name}' decorated function does not have required positional "
                "parameter '{e.param}'. Solid functions should only have keyword arguments "
                "that match input names and a first positional parameter named 'context'.".format(
                    solid_name=solid_name, e=e
                )
            )
        elif e.error_type == FunctionValidationError.TYPES['extra']:
            undeclared_inputs_printed = ", '".join(e.missing_names)
            raise DagsterInvalidDefinitionError(
                "solid '{solid_name}' decorated function does not have parameter(s) "
                "'{undeclared_inputs_printed}', which are in solid's input_defs. Solid functions "
                "should only have keyword arguments that match input names and a first positional "
                "parameter named 'context'.".format(
                    solid_name=solid_name, undeclared_inputs_printed=undeclared_inputs_printed
                )
            )
        else:
            raise e


def _validate_decorated_fn(fn, names, expected_positionals):
    used_inputs = set()
    has_kwargs = False

    signature = funcsigs.signature(fn)
    params = list(signature.parameters.values())

    expected_positional_params = params[0 : len(expected_positionals)]
    other_params = params[len(expected_positionals) :]

    if len(expected_positional_params) < len(expected_positionals):
        raise FunctionValidationError(
            FunctionValidationError.TYPES['missing_positional'],
            param=(
                expected_positionals[0]
                if isinstance(expected_positionals[0], str)
                else expected_positionals[0][0]  # tuple
            ),
        )

    for expected_names, actual in zip(expected_positionals, expected_positional_params):
        possible_names = []
        for expected in expected_names:
            possible_names.extend(
                [
                    '_',
                    expected,
                    '_{expected}'.format(expected=expected),
                    '{expected}_'.format(expected=expected),
                ]
            )

        if (
            actual.kind
            not in [funcsigs.Parameter.POSITIONAL_OR_KEYWORD, funcsigs.Parameter.POSITIONAL_ONLY]
        ) or (actual.name not in possible_names):
            raise FunctionValidationError(
                FunctionValidationError.TYPES['missing_positional'], param=expected_names
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


class _CompositeSolid(object):
    def __init__(
        self,
        name=None,
        input_defs=None,
        output_defs=None,
        description=None,
        config=None,
        config_fn=None,
    ):
        self.name = check.opt_str_param(name, 'name')
        self.input_defs = check.opt_nullable_list_param(input_defs, 'input_defs', InputDefinition)
        self.output_defs = check.opt_nullable_list_param(output_defs, 'output', OutputDefinition)
        self.description = check.opt_str_param(description, 'description')

        check.opt_dict_param(config, 'config')  # don't want to assign dict below if config is None
        self.config = config
        self.config_fn = check.opt_callable_param(config_fn, 'config_fn')

    def __call__(self, fn):
        check.callable_param(fn, 'fn')

        if not self.name:
            self.name = fn.__name__

        input_defs = (
            self.input_defs
            if self.input_defs is not None
            else infer_input_definitions_for_composite_solid(self.name, fn)
        )

        explicit_outputs = False
        if self.output_defs is not None:
            explicit_outputs = True
            output_defs = self.output_defs
        else:
            explicit_outputs = has_explicit_return_type(fn)
            output_defs = infer_output_definitions('@composite_solid', self.name, fn)

        _validate_solid_fn(self.name, fn, input_defs, exclude_nothing=False)

        kwargs = {input_def.name: InputMappingNode(input_def) for input_def in input_defs}

        output = None
        mapping = None
        enter_composition(self.name, '@composite_solid')
        try:
            output = fn(**kwargs)
            mapping = composite_mapping_from_output(output, output_defs, self.name)
        finally:
            context = exit_composition(mapping)

        check.invariant(
            context.name == self.name,
            'Composition context stack desync: received context for '
            '"{context.name}" expected "{self.name}"'.format(context=context, self=self),
        )

        # line up mappings in definition order
        input_mappings = []
        for defn in input_defs:
            mappings = context.input_mapping_dict.get(defn.name, [])
            if len(mappings) == 0:
                raise DagsterInvalidDefinitionError(
                    "@composite_solid '{solid_name}' has unmapped input '{input_name}'. "
                    "Remove it or pass it to the appropriate solid invocation.".format(
                        solid_name=self.name, input_name=defn.name
                    )
                )

            input_mappings += mappings

        output_mappings = []
        for defn in output_defs:
            mapping = context.output_mapping_dict.get(defn.name)
            if mapping is None:
                # if we inferred output_defs we will be flexible and either take a mapping or not
                if not explicit_outputs:
                    continue

                raise DagsterInvalidDefinitionError(
                    "@composite_solid '{solid_name}' has unmapped output '{output_name}'. "
                    "Remove it or return a value from the appropriate solid invocation.".format(
                        solid_name=self.name, output_name=defn.name
                    )
                )
            output_mappings.append(mapping)

        config_mapping = _get_validated_config_mapping(self.name, self.config, self.config_fn)

        return CompositeSolidDefinition(
            name=self.name,
            input_mappings=input_mappings,
            output_mappings=output_mappings,
            dependencies=context.dependencies,
            solid_defs=context.solid_defs,
            description=self.description,
            config_mapping=config_mapping,
        )


def _get_validated_config_mapping(name, config, config_fn):
    '''Config mapping must set composite config and config_fn or neither.
    '''

    if config_fn is None and config is None:
        return None
    elif config_fn is not None and config is not None:
        return ConfigMapping(config_fn=config_fn, config=config)
    else:
        if config_fn is not None:
            raise DagsterInvalidDefinitionError(
                "@composite_solid '{solid_name}' defines a configuration function {config_fn} but "
                "does not define a configuration schema.".format(
                    solid_name=name, config_fn=config_fn.__name__
                )
            )
        else:
            raise DagsterInvalidDefinitionError(
                "@composite_solid '{solid_name}' defines a configuration schema but does not "
                "define a configuration function.".format(solid_name=name)
            )


def composite_solid(
    name=None, input_defs=None, output_defs=None, description=None, config=None, config_fn=None
):
    '''Create a composite solid with specified parameters from the decorated
    `composition function <../../learn/tutorial/composition_functions.html>`_ .

    Using this decorator allows you to build up the dependency graph of the composite by writing a
    function that invokes solids and passes the output to other solids.

    Args:
        name (Optional[str])
        description (Optional[str])
        input_defs (Optional[List[InputDefinition]]):
            The set of input_defs, inferred from typehints if not provided.

            Where these input_defs get used in the body of the decorated function create the
            InputMappings for the CompositeSolidDefinition
        output_defs (Optional[List[OutputDefinition]]):
            The set of output_defs, inferred from typehints if not provided.

            These output_defs are combined with the return value of the decorated function to
            create the OutputMappings for the CompositeSolidDefinition.

            A dictionary is returned from the function to map multiple output_defs.
        config/config_fn:
            By specifying a config mapping, you can override the configuration for child solids
            contained within this composite solid. Config mappings require both a configuration
            field to be specified, which is exposed as the configuration for this composite solid,
            and a configuration mapping function, which maps the parent configuration of this solid
            into a configuration that is applied to any child solids.

    Examples:

        .. code-block:: python

            @lambda_solid
            def add_one(num: int) -> int:
                return num + 1

            @composite_solid
            def add_two(num: int) -> int:
                adder_1 = add_one.alias('adder_1')
                adder_2 = add_one.alias('adder_2')

                return adder_2(adder_1(num))

    '''
    if callable(name):
        check.invariant(input_defs is None)
        check.invariant(output_defs is None)
        check.invariant(description is None)
        check.invariant(config is None)
        check.invariant(config_fn is None)
        return _CompositeSolid()(name)

    return _CompositeSolid(
        name=name,
        input_defs=input_defs,
        output_defs=output_defs,
        description=description,
        config=config,
        config_fn=config_fn,
    )


class _Pipeline:
    def __init__(self, name=None, mode_defs=None, preset_defs=None, description=None):
        self.name = check.opt_str_param(name, 'name')
        self.mode_definitions = check.opt_list_param(mode_defs, 'mode_defs', ModeDefinition)
        self.preset_definitions = check.opt_list_param(preset_defs, 'preset_defs', PresetDefinition)
        self.description = check.opt_str_param(description, 'description')

    def __call__(self, fn):
        check.callable_param(fn, 'fn')

        if not self.name:
            self.name = fn.__name__

        enter_composition(self.name, '@pipeline')
        try:
            fn()
        finally:
            context = exit_composition()

        return PipelineDefinition(
            name=self.name,
            dependencies=context.dependencies,
            solid_defs=context.solid_defs,
            mode_defs=self.mode_definitions,
            preset_defs=self.preset_definitions,
            description=self.description,
        )


def pipeline(name=None, description=None, mode_defs=None, preset_defs=None):
    '''Create a pipeline with specified parameters from the decorated
    `composition function <../../learn/tutorial/composition_functions.html>`_ .

    Using this decorator allows you to build up the dependency graph of the pipeline by writing a
    function that invokes solids and passes the output to other solids.

    Args:
        name (Optional[str])
        description (Optional[str])
        mode_defs (Optional[List[ModeDefinition]]):
            The set of modes this pipeline can operate in. Modes can be used for example to vary
            resources and logging implementations for local testing and running in production.
        preset_defs (Optional[List[PresetDefinition]]):
            Given the different ways a pipeline may execute, presets give you a way to provide
            specific valid collections of configuration.

    Examples:

        .. code-block:: python

            @lambda_solid
            def emit_one() -> int:
                return 1

            @lambda_solid
            def add_one(num: int) -> int:
                return num + 1

            @lambda_solid
            def mult_two(num: int) -> int:
                return num * 2

            @pipeline
            def add_pipeline():
                add_one(mult_two(emit_one()))

    '''
    if callable(name):
        check.invariant(description is None)
        return _Pipeline()(name)

    return _Pipeline(
        name=name, mode_defs=mode_defs, preset_defs=preset_defs, description=description
    )
