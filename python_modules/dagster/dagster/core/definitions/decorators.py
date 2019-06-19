import inspect
from collections import namedtuple
from functools import wraps

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError

from . import (
    CompositeSolidDefinition,
    ExpectationResult,
    InputDefinition,
    Materialization,
    ModeDefinition,
    OutputDefinition,
    PipelineDefinition,
    PresetDefinition,
    Result,
    SolidDefinition,
)
from .composition import (
    EmptySolidContext,
    InputMappingNode,
    composite_mapping_from_output,
    enter_composition,
    exit_composition,
)
from .inference import (
    infer_input_definitions_for_lambda_solid,
    infer_input_definitions_for_solid,
    infer_output_definitions,
)
from .config import resolve_config_field

if hasattr(inspect, 'signature'):
    funcsigs = inspect
else:
    import funcsigs

# Error messages are long
# pylint: disable=C0301


class MultipleResults(namedtuple('_MultipleResults', 'results')):
    '''A shortcut to output multiple results.

    When using the :py:func:`@solid <dagster.solid>` API, you may return an instance of
    ``MultipleResults`` from a decorated compute function instead of yielding multiple results.

    Attributes:
      results (list[Result]): list of :py:class:`Result`

    Examples:

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
        '''Create a new ``MultipleResults`` object from a dictionary.

        Keys of the dictionary are unpacked into result names.

        Args:
            result_dict (dict) - The dictionary to unpack.

        Returns:
            (:py:class:`MultipleResults <dagster.MultipleResults>`) A new ``MultipleResults`` object

        '''
        check.dict_param(result_dict, 'result_dict', key_type=str)
        results = []
        for name, value in result_dict.items():
            results.append(Result(value, name))
        return MultipleResults(*results)


class _LambdaSolid(object):
    def __init__(self, name=None, inputs=None, output=None, description=None):
        self.name = check.opt_str_param(name, 'name')
        self.input_defs = check.opt_nullable_list_param(inputs, 'inputs', InputDefinition)
        self.output_def = check.opt_inst_param(output, 'output', OutputDefinition)
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
        compute_fn = _create_lambda_solid_transform_wrapper(fn, input_defs, output_def)

        return SolidDefinition(
            name=self.name,
            inputs=input_defs,
            outputs=[output_def],
            compute_fn=compute_fn,
            description=self.description,
        )


class _Solid(object):
    def __init__(
        self,
        name=None,
        inputs=None,
        outputs=None,
        description=None,
        required_resources=None,
        config_field=None,
    ):
        self.name = check.opt_str_param(name, 'name')
        self.input_defs = check.opt_nullable_list_param(inputs, 'inputs', InputDefinition)
        self.output_defs = check.opt_nullable_list_param(outputs, 'outputs', OutputDefinition)

        self.description = check.opt_str_param(description, 'description')

        # resources will be checked within SolidDefinition
        self.required_resources = required_resources

        # config_field will be checked within SolidDefinition
        self.config_field = config_field

    def __call__(self, fn):
        check.callable_param(fn, 'fn')

        if not self.name:
            self.name = fn.__name__

        input_defs = (
            self.input_defs
            if self.input_defs is not None
            else infer_input_definitions_for_solid('@solid', self.name, fn)
        )
        output_defs = (
            self.output_defs
            if self.output_defs is not None
            else infer_output_definitions('@solid', self.name, fn)
        )

        _validate_solid_fn(self.name, fn, input_defs, [('context',)])
        compute_fn = _create_solid_transform_wrapper(fn, input_defs, output_defs)

        return SolidDefinition(
            name=self.name,
            inputs=input_defs,
            outputs=output_defs,
            compute_fn=compute_fn,
            config_field=self.config_field,
            description=self.description,
            required_resources=self.required_resources,
        )


def lambda_solid(name=None, description=None, inputs=None, output=None):
    '''(decorator) Create a simple solid.

    This shortcut allows the creation of simple solids that do not require
    configuration and whose implementations do not require a context.

    Lambda solids take inputs and produce a single output. The body of the function
    should return a single value.

    Args:
        name (str): Name of solid.
        description (str): Solid description.
        inputs (list[InputDefinition]): List of inputs.
        output (OutputDefinition): The output of the solid. Defaults to ``OutputDefinition()``.

    Examples:

        .. code-block:: python

            @lambda_solid
            def hello_world():
                return 'hello'

            @lambda_solid(inputs=[InputDefinition(name='foo')])
            def hello_world(foo):
                return foo

    '''
    if callable(name):
        check.invariant(inputs is None)
        check.invariant(description is None)
        return _LambdaSolid(output=output)(name)

    return _LambdaSolid(name=name, inputs=inputs, output=output, description=description)


def solid(
    name=None,
    description=None,
    inputs=None,
    outputs=None,
    config_field=None,
    config=None,
    required_resources=None,
):
    '''(decorator) Create a solid with specified parameters.

    This shortcut simplifies the core solid API by exploding arguments into kwargs of the
    compute function and omitting additional parameters when they are not needed.
    Parameters are otherwise as in the core API, :py:class:`SolidDefinition`.

    The decorated function will be used as the solid's compute function. Unlike in the core API,
    the compute function does not have to yield :py:class:`Result` object directly. Several
    simpler alternatives are available:

    1. Return a value. This is returned as a :py:class:`Result` for a single output solid.
    2. Return a :py:class:`Result`. Works like yielding result.
    3. Return an instance of :py:class:`MultipleResults`. Works like yielding several results for
       multiple outputs. Useful for solids that have multiple outputs.
    4. Yield :py:class:`Result`. Same as default compute behaviour.

    Args:
        name (str): Name of solid.
        description (str): Description of this solid.
        inputs (list[InputDefinition]):
            List of inputs. Inferred from typehints if not provided.
        outputs (list[OutputDefinition]):
            List of outputs. Inferred from typehints if not provided.
        config (Dict[str, Field]):
            Defines the schema of configuration data provided to the solid via context.
        config_field (Field):
            Used in the rare case of a top level config type other than a dictionary.

            Only one of config or config_field can be provided.
        resources (set[str]): Set of resource instances required by this solid.

    Examples:

        .. code-block:: python

            @solid
            def hello_world(_context):
                print('hello')

            @solid()
            def hello_world(_context):
                print('hello')

            @solid(outputs=[OutputDefinition()])
            def hello_world(_context):
                return {'foo': 'bar'}

            @solid(outputs=[OutputDefinition()])
            def hello_world(_context):
                return Result(value={'foo': 'bar'})

            @solid(outputs=[OutputDefinition()])
            def hello_world(_context):
                yield Result(value={'foo': 'bar'})

            @solid(outputs=[
                OutputDefinition(name="left"),
                OutputDefinition(name="right"),
            ])
            def hello_world(_context):
                return MultipleResults.from_dict({
                    'left': {'foo': 'left'},
                    'right': {'foo': 'right'},
                })

            @solid(
                inputs=[InputDefinition(name="foo")],
                outputs=[OutputDefinition()]
            )
            def hello_world(_context, foo):
                return foo

            @solid(
                inputs=[InputDefinition(name="foo")],
                outputs=[OutputDefinition()],
            )
            def hello_world(context, foo):
                context.log.info('log something')
                return foo

            @solid(
                inputs=[InputDefinition(name="foo")],
                outputs=[OutputDefinition()],
                config_field=Field(types.Dict({'str_value' : Field(types.String)})),
            )
            def hello_world(context, foo):
                # context.solid_config is a dictionary with 'str_value' key
                return foo + context.solid_config['str_value']

    '''
    # This case is for when decorator is used bare, without arguments. e.g. @solid versus @solid()
    if callable(name):
        check.invariant(inputs is None)
        check.invariant(outputs is None)
        check.invariant(description is None)
        check.invariant(config_field is None)
        check.invariant(config is None)
        check.invariant(required_resources is None)
        return _Solid()(name)

    return _Solid(
        name=name,
        inputs=inputs,
        outputs=outputs,
        config_field=resolve_config_field(config_field, config, '@solid'),
        description=description,
        required_resources=required_resources,
    )


def _create_lambda_solid_transform_wrapper(fn, input_defs, output_def):
    check.callable_param(fn, 'fn')
    check.list_param(input_defs, 'input_defs', of_type=InputDefinition)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    input_names = [
        input_def.name for input_def in input_defs if not input_def.runtime_type.is_nothing
    ]

    @wraps(fn)
    def transform(_context, inputs):
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

    input_names = [
        input_def.name for input_def in input_defs if not input_def.runtime_type.is_nothing
    ]

    @wraps(fn)
    def transform(context, inputs):
        kwargs = {}
        for input_name in input_names:
            kwargs[input_name] = inputs[input_name]

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

            if isinstance(result, Result):
                yield result
            elif isinstance(result, MultipleResults):
                for item in result.results:
                    yield item
            elif len(output_defs) == 1:
                yield Result(value=result, output_name=output_defs[0].name)
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
                        'be a MultipleResults object, or a generator, containing or yielding '
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

    return transform


class FunctionValidationError(Exception):
    TYPES = {'vararg': 1, 'missing_name': 2, 'missing_positional': 3, 'extra': 4}

    def __init__(self, error_type, param=None, missing_names=None, **kwargs):
        super(FunctionValidationError, self).__init__(**kwargs)
        self.error_type = error_type
        self.param = param
        self.missing_names = missing_names


def _validate_solid_fn(solid_name, compute_fn, inputs, expected_positionals=None):
    check.str_param(solid_name, 'solid_name')
    check.callable_param(compute_fn, 'compute_fn')
    check.list_param(inputs, 'inputs', of_type=InputDefinition)
    expected_positionals = check.opt_list_param(
        expected_positionals, 'expected_positionals', of_type=(str, tuple)
    )

    names = set(inp.name for inp in inputs if not inp.runtime_type.is_nothing)
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
            raise DagsterInvalidDefinitionError(
                "solid '{solid_name}' decorated function has parameter '{e.param}' that is not "
                "one of the solid inputs. Solid functions should only have keyword arguments "
                "that match input names and a first positional parameter named 'context'.".format(
                    solid_name=solid_name, e=e
                )
            )
        elif e.error_type == FunctionValidationError.TYPES['missing_positional']:
            raise DagsterInvalidDefinitionError(
                "solid '{solid_name}' decorated function do not have required positional "
                "parameter '{e.param}'. Solid functions should only have keyword arguments "
                "that match input names and a first positional parameter named 'context'.".format(
                    solid_name=solid_name, e=e
                )
            )
        elif e.error_type == FunctionValidationError.TYPES['extra']:
            undeclared_inputs_printed = ", '".join(e.missing_names)
            raise DagsterInvalidDefinitionError(
                "solid '{solid_name}' decorated function do not have parameter(s) "
                "'{undeclared_inputs_printed}', which are in solid's inputs. Solid functions "
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
        self, name=None, inputs=None, outputs=None, description=None, config_mapping_fn=None
    ):
        self.name = check.opt_str_param(name, 'name')
        self.input_defs = check.opt_nullable_list_param(inputs, 'inputs', InputDefinition)
        self.output_defs = check.opt_nullable_list_param(outputs, 'output', OutputDefinition)
        self.description = check.opt_str_param(description, 'description')
        self.config_mapping_fn = check.opt_callable_param(config_mapping_fn, 'config_mapping_fn')

    def __call__(self, fn):
        check.callable_param(fn, 'fn')

        if not self.name:
            self.name = fn.__name__

        input_defs = (
            self.input_defs
            if self.input_defs is not None
            else infer_input_definitions_for_solid('@composite_solid', self.name, fn)
        )
        output_defs = (
            self.output_defs
            if self.output_defs is not None
            else infer_output_definitions('@composite_solid', self.name, fn)
        )

        _validate_solid_fn(self.name, fn, input_defs, [('context',)])

        kwargs = {input_def.name: InputMappingNode(input_def) for input_def in input_defs}

        output = None
        enter_composition(self.name, '@composite_solid')
        try:
            output = fn(EmptySolidContext(), **kwargs)
        finally:
            context = exit_composition(
                composite_mapping_from_output(output, output_defs, self.name)
            )

        check.invariant(
            context.name == self.name,
            'Composition context stack desync: received context for '
            '"{context.name}" expected "{self.name}"'.format(context=context, self=self),
        )

        return CompositeSolidDefinition(
            name=self.name,
            input_mappings=context.input_mappings,
            output_mappings=context.output_mappings,
            dependencies=context.dependencies,
            solid_defs=context.solid_defs,
            description=self.description,
            config_mapping_fn=self.config_mapping_fn,
        )


def composite_solid(name=None, inputs=None, outputs=None, description=None, config_mapping_fn=None):
    ''' (decorator) Create a CompositeSolidDefinition with specified parameters.

    Using this decorator allows you to build up the dependency graph of the composite by writing a
    function that invokes solids and passes the output to other solids.

    Args:
        name (Optional[str])
        description (Optional[str])
        inputs (Optional[List[InputDefinition]]):
            The set of inputs, inferred from typehints if not provided.

            Where these inputs get used in the body of the decorated function create the
            InputMappings for the CompositeSolidDefinition
        outputs (Optional[List[OutputDefinition]]):
            The set of outputs, inferred from typehints if not provided.

            These outputs are combined with the return value of the decorated function to
            create the OutputMappings for the CompositeSolidDefinition.

            A dictionary is returned from the function to map multiple outputs.
        config_mapping_fn (Callable):
            A function to remap configuration for the constituent solids.

    Examples:

        .. code-block:: python

        @lambda_solid
        def add_one(num: int) -> int:
            return num + 1

        @composite_solid
        def add_two(num: int) -> int:
            add_one_1 = add_one.alias('add_one_1')
            add_one_2 = add_one.alias('add_one_2')

            return add_one_2(add_one_1(num))

    '''
    if callable(name):
        check.invariant(inputs is None)
        check.invariant(outputs is None)
        check.invariant(description is None)
        check.invariant(config_mapping_fn is None)
        return _CompositeSolid()(name)

    return _CompositeSolid(
        name=name,
        inputs=inputs,
        outputs=outputs,
        description=description,
        config_mapping_fn=config_mapping_fn,
    )


class _Pipeline:
    def __init__(self, name=None, mode_definitions=None, preset_definitions=None, description=None):
        self.name = check.opt_str_param(name, 'name')
        self.mode_definitions = check.opt_list_param(
            mode_definitions, 'mode_definitions', ModeDefinition
        )
        self.preset_definitions = check.opt_list_param(
            preset_definitions, 'preset_definitions', PresetDefinition
        )
        self.description = check.opt_str_param(description, 'description')

    def __call__(self, fn):
        check.callable_param(fn, 'fn')

        if not self.name:
            self.name = fn.__name__

        enter_composition(self.name, '@pipeline')
        try:
            fn(EmptySolidContext())
        finally:
            context = exit_composition([])

        return PipelineDefinition(
            name=self.name,
            dependencies=context.dependencies,
            solid_defs=context.solid_defs,
            mode_definitions=self.mode_definitions,
            preset_definitions=self.preset_definitions,
            description=self.description,
        )


def pipeline(name=None, description=None, mode_definitions=None, preset_definitions=None):
    ''' (decorator) Create a pipeline with specified parameters.

    Using this decorator allows you to build up the dependency graph of the pipeline by writing a
    function that invokes solids and passes the output to other solids.

    Args:
        name (Optional[str])
        description (Optional[str])
        mode_definitions (Optional[List[ModeDefinition]]):
            The set of modes this pipeline can operate in. Modes can be used for example to vary
            resources and logging implementations for local testing and running in production.
        preset_definitions (Optional[List[PresetDefinition]]):
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
        def add_pipeline(_):
            add_one(mult_two(emit_one()))

    '''
    if callable(name):
        check.invariant(description is None)
        return _Pipeline()(name)

    return _Pipeline(
        name=name,
        mode_definitions=mode_definitions,
        preset_definitions=preset_definitions,
        description=description,
    )
