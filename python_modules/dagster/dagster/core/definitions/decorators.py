import inspect
from functools import wraps

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError

from ..decorator_utils import (
    InvalidDecoratedFunctionInfo,
    split_function_parameters,
    validate_decorated_fn_non_positionals,
    validate_decorated_fn_positionals,
)
from ..scheduler import Scheduler, SchedulerHandle
from .composition import (
    InputMappingNode,
    composite_mapping_from_output,
    enter_composition,
    exit_composition,
)
from .config import ConfigMapping, resolve_config_field
from .events import ExpectationResult, Materialization, Output
from .inference import (
    has_explicit_return_type,
    infer_input_definitions_for_composite_solid,
    infer_input_definitions_for_lambda_solid,
    infer_input_definitions_for_solid,
    infer_output_definitions,
)
from .input import InputDefinition
from .mode import ModeDefinition
from .output import OutputDefinition
from .pipeline import PipelineDefinition
from .preset import PresetDefinition
from .schedule import ScheduleDefinition
from .solid import CompositeSolidDefinition, SolidDefinition

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

        validate_solid_fn('@lambda_solid', self.name, fn, input_defs)
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
        step_metadata_fn=None,
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

        self.step_metadata_fn = check.opt_callable_param(step_metadata_fn, 'step_metadata_fn')

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

        validate_solid_fn('@solid', self.name, fn, input_defs, ['context'])
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
            step_metadata_fn=self.step_metadata_fn,
        )


class _SchedulerHandle(object):
    def __init__(self, scheduler_type):
        self.scheduler_type = check.subclass_param(scheduler_type, 'scheduler_type', Scheduler)

    def __call__(self, fn):
        check.callable_param(fn, 'fn')

        schedule_defs = fn()
        for schedule_def in schedule_defs:
            if not isinstance(schedule_def, ScheduleDefinition):
                raise DagsterInvariantViolationError(
                    '{fn_name} must return a list of ScheduleDefinitions'.format(
                        fn_name=fn.__name__
                    )
                )

        def handle_fn(artifacts_dir, repository_name):
            return SchedulerHandle(
                scheduler_type=self.scheduler_type,
                schedule_defs=schedule_defs,
                artifacts_dir=artifacts_dir,
                repository_name=repository_name,
            )

        return handle_fn


def schedules(scheduler):
    '''Create a scheduler with a :py:class:`~dagster.core.scheduler.Scheduler` implementation and
    set of :py:class:`ScheduleDefinition` instances.

    Decorate a function that returns a list of :py:class:`ScheduleDefinition`. The decorator has
    an argument that takes a :py:class:`~dagster.core.scheduler.Scheduler` implementation, such as
    :py:func:`~dagster_cron.SystemCronScheduler`.

    Args:
        scheduler (Scheduler): The scheduler implementation to use.

    Examples:

    .. code-block:: python

        from dagster_cron import SystemCronScheduler

        @schedules(scheduler=SystemCronScheduler)
        def define_scheduler():
            hello_world_schedule = ScheduleDefinition(
                name='hello_world_schedule',
                cron_string='* * * * *'
            )

            return [hello_world_schedule]
    '''
    return _SchedulerHandle(scheduler)


def lambda_solid(name=None, description=None, input_defs=None, output_def=None):
    '''Create a simple solid from the decorated function.

    This shortcut allows the creation of simple solids that do not require
    configuration and whose implementations do not require a
    :py:class:`context <SystemComputeExecutionContext>`.

    Lambda solids take any number of inputs and produce a single output.

    Inputs can be defined using :class:`InputDefinition` and passed to the ``input_defs`` argument
    of this decorator, or inferred from the type signature of the decorated function.

    The single output can be defined using :class:`OutputDefinition` and passed as the
    ``output_def`` argument of this decorator, or its type can be inferred from the type signature
    of the decorated function.

    The body of the decorated function should return a single value, which will be yielded as the
    solid's output.

    Args:
        name (str): Name of solid.
        description (str): Solid description.
        input_defs (List[InputDefinition]): List of input_defs.
        output_def (OutputDefinition): The output of the solid. Defaults to
            :class:`OutputDefinition() <OutputDefinition>`.

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
    step_metadata_fn=None,
):
    '''Create a solid with the specified parameters from the decorated function.

    This shortcut simplifies the core :class:`SolidDefinition` API by exploding arguments into
    kwargs of the decorated compute function and omitting additional parameters when they are not
    needed.

    Input and output definitions will be inferred from the type signature of the decorated function
    if not explicitly provided.

    The decorated function will be used as the solid's compute function. The signature of the
    decorated function is more flexible than that of the ``compute_fn`` in the core API; it may:

    1. Return a value. This value will be wrapped in an :py:class:`Output` and yielded by the
        compute function.
    2. Return an :py:class:`Output`. This output will be yielded by the compute function.
    3. Yield :py:class:`Output` or other `event objects <events>`_. Same as default compute
        behaviour.

    Note that options 1) and 2) are incompatible with yielding other events -- if you would like
    to decorate a function that yields events, it must also wrap its eventual output in an
    :py:class:`Output` and yield it.

    Args:
        name (str): Name of solid. Must be unique within any :py:class:`PipelineDefinition`
            using the solid.
        description (str): Human-readable description of this solid.
        input_defs (Optional[List[InputDefinition]]):
            List of input definitions. Inferred from typehints if not provided.
        output_defs (Optional[List[OutputDefinition]]):
            List of output definitions. Inferred from typehints if not provided.
        config (Optional[Dict[str, Field]]):
            Defines the schema of the configuration dict provided to the solid via context.
        config_field (Optional[Field]): Used in the rare case when a solid's top level config type
            is other than a dictionary.

            A :class:`DagsterInvalidDefinitionError` will be raised if both ``config`` and
            ``config_field`` are set.
        required_resource_keys (Optional[Set[str]]): Set of resource handles required by this solid.
        metadata (Optional[Dict[Any, Any]]): Arbitrary metadata for the solid. Frameworks may
            expect and require certain metadata to be attached to a solid. Users should generally
            not set metadata directly.

    Examples:

        .. code-block:: python

            @solid
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
        check.invariant(step_metadata_fn is None)
        return _Solid()(name)

    return _Solid(
        name=name,
        input_defs=input_defs,
        output_defs=output_defs,
        config_field=resolve_config_field(config_field, config, '@solid'),
        description=description,
        required_resource_keys=required_resource_keys,
        metadata=metadata,
        step_metadata_fn=step_metadata_fn,
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


def validate_solid_fn(
    decorator_name, fn_name, compute_fn, input_defs, expected_positionals=None, exclude_nothing=True
):
    check.str_param(decorator_name, 'decorator_name')
    check.str_param(fn_name, 'fn_name')
    check.callable_param(compute_fn, 'compute_fn')
    check.list_param(input_defs, 'input_defs', of_type=InputDefinition)
    expected_positionals = check.opt_list_param(
        expected_positionals, 'expected_positionals', of_type=str
    )
    if exclude_nothing:
        names = set(inp.name for inp in input_defs if not inp.runtime_type.is_nothing)
        nothing_names = set(inp.name for inp in input_defs if inp.runtime_type.is_nothing)
    else:
        names = set(inp.name for inp in input_defs)
        nothing_names = set()

    # Currently being super strict about naming. Might be a good idea to relax. Starting strict.
    fn_positionals, fn_non_positionals = split_function_parameters(compute_fn, expected_positionals)

    # Validate Positional Parameters
    missing_positional = validate_decorated_fn_positionals(fn_positionals, expected_positionals)
    if missing_positional:
        raise DagsterInvalidDefinitionError(
            "{decorator_name} '{solid_name}' decorated function does not have required positional "
            "parameter '{missing_param}'. Solid functions should only have keyword arguments "
            "that match input names and a first positional parameter named 'context'.".format(
                decorator_name=decorator_name, solid_name=fn_name, missing_param=missing_positional
            )
        )

    # Validate non positional parameters
    invalid_function_info = validate_decorated_fn_non_positionals(names, fn_non_positionals)
    if invalid_function_info:
        if invalid_function_info.error_type == InvalidDecoratedFunctionInfo.TYPES['vararg']:
            raise DagsterInvalidDefinitionError(
                "{decorator_name} '{solid_name}' decorated function has positional vararg parameter "
                "'{param}'. Solid functions should only have keyword arguments that match "
                "input names and a first positional parameter named 'context'.".format(
                    decorator_name=decorator_name,
                    solid_name=fn_name,
                    param=invalid_function_info.param,
                )
            )
        elif invalid_function_info.error_type == InvalidDecoratedFunctionInfo.TYPES['missing_name']:
            if invalid_function_info.param in nothing_names:
                raise DagsterInvalidDefinitionError(
                    "{decorator_name} '{solid_name}' decorated function has parameter '{param}' that is "
                    "one of the solid input_defs of type 'Nothing' which should not be included since "
                    "no data will be passed for it. ".format(
                        decorator_name=decorator_name,
                        solid_name=fn_name,
                        param=invalid_function_info.param,
                    )
                )
            else:
                raise DagsterInvalidDefinitionError(
                    "{decorator_name} '{solid_name}' decorated function has parameter '{param}' that is not "
                    "one of the solid input_defs. Solid functions should only have keyword arguments "
                    "that match input names and a first positional parameter named 'context'.".format(
                        decorator_name=decorator_name,
                        solid_name=fn_name,
                        param=invalid_function_info.param,
                    )
                )
        elif invalid_function_info.error_type == InvalidDecoratedFunctionInfo.TYPES['extra']:
            undeclared_inputs_printed = ", '".join(invalid_function_info.missing_names)
            raise DagsterInvalidDefinitionError(
                "{decorator_name} '{solid_name}' decorated function does not have parameter(s) "
                "'{undeclared_inputs_printed}', which are in solid's input_defs. Solid functions "
                "should only have keyword arguments that match input names and a first positional "
                "parameter named 'context'.".format(
                    decorator_name=decorator_name,
                    solid_name=fn_name,
                    undeclared_inputs_printed=undeclared_inputs_printed,
                )
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

        validate_solid_fn('@composite_solid', self.name, fn, input_defs, exclude_nothing=False)

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
            mappings = [
                mapping
                for mapping in context.input_mappings
                if mapping.definition.name == defn.name
            ]

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
                '@composite_solid \'{solid_name}\' defines a configuration function {config_fn} '
                'but does not define a configuration schema. If you intend this composite to take '
                'no config, you must explicitly specify config={{}}.'.format(
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
    '''Create a composite solid with the specified parameters from the decorated composition
    function.

    Using this decorator allows you to build up the dependency graph of the composite by writing a
    function that invokes solids and passes the output to other solids. This is similar to the use
    of the :py:func:`@pipeline <pipeline>` decorator, with the additional ability to remap inputs,
    outputs, and config across the composite boundary.

    Args:
        name (Optional[str]): Name for the new composite solid. Must be unique within any
            :py:class:`PipelineDefinition` using the solid.
        description (Optional[str]): Human-readable description of the new composite solid.
        input_defs (Optional[List[InputDefinition]]): Input definitions for the composite solid.
            If not provided explicitly, these will be inferred from typehints.

            Uses of these inputs in the body of the decorated composition function will be used to
            infer the appropriate set of :py:class:`InputMappings <InputMapping>` passed to the
            underlying :py:class:`CompositeSolidDefinition`.
        output_defs (Optional[List[OutputDefinition]]): Output definitions for the composite solid.
            If not provided explicitly, these will be inferred from typehints.

            Uses of these outputs in the body of the decorated composition function, as well as the
            return value of the decorated function, will be used to infer the appropriate set of
            :py:class:`OutputMappings <OutputMapping>` for the underlying
            :py:class:`CompositeSolidDefinition`.

            To map multiple outputs, return a dictionary from the composition function.
        config (Optional[Dict[str, Field]]):
            Defines the schema of the configuration dict provided to the composite solid via context.
            If you specify ``config``, you must also specify ``config_fn``.
        config_fn (Callable[[ConfigMappingContext, dict], dict]): By specifying a config mapping
            function, you can override the configuration for the child solids contained within this
            composite solid.

            Config mappings require the configuration field to be specified as ``config``, which
            will be exposed as the configuration field for the composite solid, as well as a
            configuration mapping function, ``config_fn``, which maps the config provided to the
            composite solid to the config that will be provided to the child solids.

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


class _Pipeline(object):
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
    '''Create a pipeline with the specified parameters from the decorated composition function.

    Using this decorator allows you to build up the dependency graph of the pipeline by writing a
    function that invokes solids and passes the output to other solids.

    Args:
        name (Optional[str]): The name of the pipeline. Must be unique within any
            :py:class:`RepositoryDefinition` containing the pipeline.
        description (Optional[str]): A human-readable description of the pipeline.
        mode_defs (Optional[List[ModeDefinition]]): The set of modes in which this pipeline can
            operate. Modes are used to attach resources, custom loggers, custom system storage
            options, and custom executors to a pipeline. Modes can be used, e.g., to vary
            available resource and logging implementations between local test and production runs.
        preset_defs (Optional[List[PresetDefinition]]): A set of preset collections of configuration
            options that may be used to execute a pipeline. A preset consists of an environment
            dict, an optional subset of solids to execute, and a mode selection. Presets can be used
            to ship common combinations of options to pipeline end users in Python code, and can
            be selected by tools like Dagit.

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
