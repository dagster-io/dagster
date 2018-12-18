import os

from collections import (
    defaultdict,
    namedtuple,
)

from dagster import (
    check,
    config,
)


from dagster.core.definitions import (
    ExecutionGraph,
    ExpectationDefinition,
    InputDefinition,
    OutputDefinition,
    Solid,
    SolidOutputHandle,
    Result,
    ExpectationExecutionInfo,
    TransformExecutionInfo,
)

from dagster.core.errors import (
    DagsterExpectationFailedError,
    DagsterInvariantViolationError,
)

from dagster.core.execution_context import RuntimeExecutionContext

from .objects import (
    ExecutionPlan,
    ExecutionStep,
    StepTag,
    StepInput,
    StepOutput,
    StepOutputHandle,
)

def _yield_transform_results(context, step, conf, inputs):
    gen = step.solid.definition.transform_fn(
        TransformExecutionInfo(context, conf, step.solid.definition),
        inputs,
    )

    if isinstance(gen, Result):
        raise DagsterInvariantViolationError(
            (
                'Transform for solid {solid_name} returned a Result rather than ' +
                'yielding it. The transform_fn of the core SolidDefinition must yield ' +
                'its results'
            ).format(solid_name=step.solid.name)
        )

    if gen is None:
        return

    for result in gen:
        if not isinstance(result, Result):
            raise DagsterInvariantViolationError(
                (
                    'Transform for solid {solid_name} yielded {result} rather an ' +
                    'an instance of the Result class.'
                ).format(
                    result=repr(result),
                    solid_name=step.solid.name,
                )
            )

        context.info(
            'Solid {solid} emitted output "{output}" value {value}'.format(
                solid=step.solid.name,
                output=result.output_name,
                value=repr(result.value),
            )
        )
        yield result

def _execute_core_transform(context, step, conf, inputs):
    '''
    Execute the user-specified transform for the solid. Wrap in an error boundary and do
    all relevant logging and metrics tracking
    '''
    check.inst_param(context, 'context', RuntimeExecutionContext)
    check.inst_param(step, 'step', ExecutionStep)
    check.dict_param(inputs, 'inputs', key_type=str)

    solid = step.solid

    context.debug('Executing core transform for solid {solid}.'.format(solid=solid.name))

    all_results = list(_yield_transform_results(context, step, conf, inputs))

    if len(all_results) != len(solid.definition.output_defs):
        emitted_result_names = set([r.output_name for r in all_results])
        solid_output_names = set([output_def.name for output_def in solid.definition.output_defs])
        omitted_outputs = solid_output_names.difference(emitted_result_names)
        context.info(
            'Solid {solid} did not fire outputs {outputs}'.format(
                solid=solid.name,
                outputs=repr(omitted_outputs),
            )
        )

    return all_results

def get_solid_user_config(execution_info, pipeline_solid):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(pipeline_solid, 'pipeline_solid', Solid)

    name = pipeline_solid.name
    solid_configs = execution_info.environment.solids
    return solid_configs[name].config if name in solid_configs else None

def _create_join_lambda(_context, _step, inputs):
    yield Result(output_name=JOIN_OUTPUT, value=list(inputs.values())[0])


def _create_expectation_lambda(solid, inout_def, expectation_def, internal_output_name):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))
    check.inst_param(expectation_def, 'expectations_def', ExpectationDefinition)
    check.str_param(internal_output_name, 'internal_output_name')

    def _do_expectation(context, step, inputs):
        with context.values(
            {
                inout_def.descriptive_key: inout_def.name,
                'expectation': expectation_def.name
            }
        ):
            value = inputs[EXPECTATION_INPUT]
            info = ExpectationExecutionInfo(context, inout_def, solid, expectation_def)
            expt_result = expectation_def.expectation_fn(info, value)
            if expt_result.success:
                context.debug(
                    'Expectation {key} succeeded on {value}.'.format(
                        key=step.key,
                        value=value,
                    )
                )
                yield Result(output_name=internal_output_name, value=inputs[EXPECTATION_INPUT])
            else:
                context.debug(
                    'Expectation {key} failed on {value}.'.format(key=step.key, value=value)
                )
                raise DagsterExpectationFailedError(info, value)

    return _do_expectation



# This is the state that is built up during the execution plan build process.
# steps is just a list of the steps that have been created
# step_output_map maps logical solid outputs (solid_name, output_name) to particular
# step outputs. This covers the case where a solid maps to multiple steps
# and one wants to be able to attach to the logical output of a solid during execution
StepBuilderState = namedtuple('StepBuilderState', 'steps step_output_map')

EXPECTATION_VALUE_OUTPUT = 'expectation_value'
JOIN_OUTPUT = 'join_output'
EXPECTATION_INPUT = 'expectation_input'
SERIALIZE_INPUT = 'serialize_input'
SERIALIZE_OUTPUT = 'serialize_output'
INPUT_THUNK_OUTPUT = 'input_thunk_output'


class StepOutputMap(dict):
    def __getitem__(self, key):
        check.inst_param(key, 'key', SolidOutputHandle)
        return dict.__getitem__(self, key)

    def __setitem__(self, key, val):
        check.inst_param(key, 'key', SolidOutputHandle)
        check.inst_param(val, 'val', StepOutputHandle)
        return dict.__setitem__(self, key, val)


class ExecutionPlanInfo(namedtuple('_ExecutionPlanInfo', 'context execution_graph environment')):
    def __new__(cls, context, execution_graph, environment):
        return super(ExecutionPlanInfo, cls).__new__(
            cls,
            check.inst_param(context, 'context', RuntimeExecutionContext),
            check.inst_param(execution_graph, 'execution_graph', ExecutionGraph),
            check.inst_param(environment, 'environment', config.Environment),
        )

    @property
    def pipeline(self):
        return self.execution_graph.pipeline

    @property
    def serialize_intermediates(self):
        return self.environment.execution.serialize_intermediates


def create_expectation_step(
    solid,
    expectation_def,
    key,
    tag,
    prev_step_output_handle,
    inout_def,
):

    check.inst_param(solid, 'solid', Solid)
    check.inst_param(expectation_def, 'input_expct_def', ExpectationDefinition)
    check.inst_param(prev_step_output_handle, 'prev_step_output_handle', StepOutputHandle)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))

    value_type = inout_def.dagster_type

    return ExecutionStep(
        key=key,
        step_inputs=[
            StepInput(
                name=EXPECTATION_INPUT,
                dagster_type=value_type,
                prev_output_handle=prev_step_output_handle,
            )
        ],
        step_outputs=[
            StepOutput(name=EXPECTATION_VALUE_OUTPUT, dagster_type=value_type),
        ],
        compute_fn=_create_expectation_lambda(
            solid,
            inout_def,
            expectation_def,
            EXPECTATION_VALUE_OUTPUT,
        ),
        tag=tag,
        solid=solid,
    )


ExecutionSubPlan = namedtuple(
    'ExecutionSubPlan',
    'steps terminal_step_output_handle',
)


def create_expectations_subplan(solid, inout_def, prev_step_output_handle, tag):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))
    check.inst_param(prev_step_output_handle, 'prev_step_output_handle', StepOutputHandle)
    check.inst_param(tag, 'tag', StepTag)

    steps = []
    input_expect_steps = []
    for expectation_def in inout_def.expectations:
        expect_step = create_expectation_step(
            solid=solid,
            expectation_def=expectation_def,
            key='{solid.name}.{inout_def.name}.expectation.{expectation_def.name}'.format(
                solid=solid,
                inout_def=inout_def,
                expectation_def=expectation_def,
            ),
            tag=tag,
            prev_step_output_handle=prev_step_output_handle,
            inout_def=inout_def,
        )
        input_expect_steps.append(expect_step)
        steps.append(expect_step)

    join_step = _create_join_step(
        solid,
        '{solid}.{desc_key}.{name}.expectations.join'.format(
            solid=solid.name,
            desc_key=inout_def.descriptive_key,
            name=inout_def.name,
        ),
        input_expect_steps,
        EXPECTATION_VALUE_OUTPUT,
    )

    output_name = join_step.step_outputs[0].name
    return ExecutionSubPlan(
        steps + [join_step],
        StepOutputHandle(join_step, output_name),
    )


def create_execution_plan_core(execution_info):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)

    execution_graph = execution_info.execution_graph

    state = StepBuilderState(
        steps=[],
        step_output_map=StepOutputMap(),
    )

    for pipeline_solid in execution_graph.topological_solids:
        step_inputs = create_step_inputs(execution_info, state, pipeline_solid)

        solid_transform_step = create_transform_step(
            pipeline_solid,
            step_inputs,
            get_solid_user_config(execution_info, pipeline_solid),
        )

        state.steps.append(solid_transform_step)

        for output_def in pipeline_solid.definition.output_defs:
            subplan = create_subplan_for_output(
                execution_info,
                pipeline_solid,
                solid_transform_step,
                output_def,
            )
            state.steps.extend(subplan.steps)

            output_handle = pipeline_solid.output_handle(output_def.name)
            state.step_output_map[output_handle] = subplan.terminal_step_output_handle

    return create_execution_plan_from_steps(state.steps)


def create_execution_plan_from_steps(steps):
    check.list_param(steps, 'steps', of_type=ExecutionStep)

    step_dict = {step.key: step for step in steps}

    deps = defaultdict()

    seen_keys = set()

    for step in steps:

        if step.key in seen_keys:
            keys = [s.key for s in steps]
            check.failed(
                'Duplicated key {key}. Full list: {key_list}.'.format(key=step.key, key_list=keys)
            )

        seen_keys.add(step.key)

        deps[step.key] = set()
        for step_input in step.step_inputs:
            deps[step.key].add(step_input.prev_output_handle.step.key)

    return ExecutionPlan(step_dict, deps)


def create_subplan_for_input(execution_info, solid, prev_step_output_handle, input_def):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(prev_step_output_handle, 'prev_step_output_handle', StepOutputHandle)
    check.inst_param(input_def, 'input_def', InputDefinition)

    if execution_info.environment.expectations.evaluate and input_def.expectations:
        return create_expectations_subplan(
            solid,
            input_def,
            prev_step_output_handle,
            tag=StepTag.INPUT_EXPECTATION,
        )
    else:
        return ExecutionSubPlan(
            steps=[],
            terminal_step_output_handle=prev_step_output_handle,
        )


def _decorate_with_expectations(execution_info, solid, transform_step, output_def):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(transform_step, 'transform_step', ExecutionStep)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    if execution_info.environment.expectations.evaluate and output_def.expectations:
        return create_expectations_subplan(
            solid,
            output_def,
            StepOutputHandle(transform_step, output_def.name),
            tag=StepTag.OUTPUT_EXPECTATION
        )
    else:
        return ExecutionSubPlan(
            steps=[],
            terminal_step_output_handle=StepOutputHandle(
                transform_step,
                output_def.name,
            ),
        )


def _decorate_with_serialization(execution_info, solid, output_def, subplan):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(output_def, 'output_def', OutputDefinition)
    check.inst_param(subplan, 'subplan', ExecutionSubPlan)

    if execution_info.serialize_intermediates:
        serialize_step = _create_serialization_step(solid, output_def, subplan)
        return ExecutionSubPlan(
            steps=subplan.steps + [serialize_step],
            terminal_step_output_handle=StepOutputHandle(
                serialize_step,
                SERIALIZE_OUTPUT,
            )
        )
    else:
        return subplan


def create_subplan_for_output(execution_info, solid, solid_transform_step, output_def):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(solid_transform_step, 'solid_transform_step', ExecutionStep)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    subplan = _decorate_with_expectations(execution_info, solid, solid_transform_step, output_def)

    return _decorate_with_serialization(execution_info, solid, output_def, subplan)


def _create_serialization_lambda(solid, output_def):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    def fn(context, _step, inputs):
        value = inputs[SERIALIZE_INPUT]
        path = '/tmp/dagster/runs/{run_id}/{solid_name}/outputs/{output_name}'.format(
            run_id=context.run_id,
            solid_name=solid.name,
            output_name=output_def.name,
        )

        if not os.path.exists(path):
            os.makedirs(path)

        output_def.dagster_type.serialize_value(path, value)

        context.info('Serialized output to {path}'.format(path=path))

        yield Result(value, SERIALIZE_OUTPUT)

    return fn


def _create_join_step(solid, step_key, prev_steps, prev_output_name):
    check.inst_param(solid, 'solid', Solid)
    check.str_param(step_key, 'step_key')
    check.list_param(prev_steps, 'prev_steps', of_type=ExecutionStep)
    check.invariant(len(prev_steps) > 0)
    check.str_param(prev_output_name, 'output_name')

    step_inputs = []
    seen_dagster_type = None
    for prev_step in prev_steps:
        prev_step_output = prev_step.step_output_named(prev_output_name)

        if seen_dagster_type is None:
            seen_dagster_type = prev_step_output.dagster_type
        else:
            check.invariant(seen_dagster_type == prev_step_output.dagster_type)

        output_handle = StepOutputHandle(prev_step, prev_output_name)

        step_inputs.append(StepInput(prev_step.key, prev_step_output.dagster_type, output_handle))

    return ExecutionStep(
        key=step_key,
        step_inputs=step_inputs,
        step_outputs=[StepOutput(JOIN_OUTPUT, seen_dagster_type)],
        compute_fn=_create_join_lambda,
        tag=StepTag.JOIN,
        solid=solid,
    )

def create_transform_step(solid, step_inputs, conf):
    check.inst_param(solid, 'solid', Solid)
    check.list_param(step_inputs, 'step_inputs', of_type=StepInput)

    return ExecutionStep(
        key='{solid.name}.transform'.format(solid=solid),
        step_inputs=step_inputs,
        step_outputs=[
            StepOutput(name=output_def.name, dagster_type=output_def.dagster_type)
            for output_def in solid.definition.output_defs
        ],
        compute_fn=lambda context, step, inputs: _execute_core_transform(
            context,
            step,
            conf,
            inputs,
        ),
        tag=StepTag.TRANSFORM,
        solid=solid,
    )

def create_input_thunk_execution_step(solid, input_def, value):
    def _fn(_context, _step, _inputs):
        yield Result(value, INPUT_THUNK_OUTPUT)

    return ExecutionStep(
        key='input_thunk.' + solid.name + '.' + input_def.name,
        step_inputs=[],
        step_outputs=[StepOutput(
            name=INPUT_THUNK_OUTPUT,
            dagster_type=input_def.dagster_type,
        )],
        compute_fn=_fn,
        tag=StepTag.INPUT_THUNK,
        solid=solid,
    )


def create_step_inputs(info, state, pipeline_solid):
    check.inst_param(info, 'info', ExecutionPlanInfo)
    check.inst_param(state, 'state', StepBuilderState)
    check.inst_param(pipeline_solid, 'pipeline_solid', Solid)

    step_inputs = []

    topo_solid = pipeline_solid.definition
    dependency_structure = info.execution_graph.dependency_structure

    for input_def in topo_solid.input_defs:
        input_handle = pipeline_solid.input_handle(input_def.name)

        solid_config = info.environment.solids.get(topo_solid.name)
        if solid_config and input_def.name in solid_config.inputs:

            if dependency_structure.has_dep(input_handle):
                raise DagsterInvariantViolationError(
                    (
                        'In pipeline {pipeline_name} solid {solid_name}, input {input_name} '
                        'you have specified an input via config while also specifying '
                        'a dependency. Either remove the dependency, specify a subdag '
                        'to execute, or remove the inputs specification in the environment.'
                    ).format(
                        pipeline_name=info.execution_graph.pipeline.name,
                        solid_name=pipeline_solid.name,
                        input_name=input_def.name,
                    )
                )

            input_thunk = create_input_thunk_execution_step(
                pipeline_solid,
                input_def,
                solid_config.inputs[input_def.name],
            )

            state.steps.append(input_thunk)
            prev_step_output_handle = StepOutputHandle(input_thunk, INPUT_THUNK_OUTPUT)
        elif dependency_structure.has_dep(input_handle):
            solid_output_handle = dependency_structure.get_dep(input_handle)
            prev_step_output_handle = state.step_output_map[solid_output_handle]
        else:
            raise DagsterInvariantViolationError(
                (
                    'In pipeline {pipeline_name} solid {solid_name}, input {input_name} '
                    'must get a value either (a) from a dependency or (b) from the '
                    'inputs section of its configuration.'
                ).format(
                    pipeline_name=info.execution_graph.pipeline.name,
                    solid_name=pipeline_solid.name,
                    input_name=input_def.name,
                )
            )

        subplan = create_subplan_for_input(
            info,
            pipeline_solid,
            prev_step_output_handle,
            input_def,
        )

        state.steps.extend(subplan.steps)
        step_inputs.append(
            StepInput(
                input_def.name,
                input_def.dagster_type,
                subplan.terminal_step_output_handle,
            )
        )

    return step_inputs


def _create_serialization_step(solid, output_def, prev_subplan):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(output_def, 'output_def', OutputDefinition)
    check.inst_param(prev_subplan, 'prev_subplan', ExecutionSubPlan)

    return ExecutionStep(
        key='serialize.' + solid.name + '.' + output_def.name,
        step_inputs=[
            StepInput(
                name=SERIALIZE_INPUT,
                dagster_type=output_def.dagster_type,
                prev_output_handle=prev_subplan.terminal_step_output_handle,
            )
        ],
        step_outputs=[StepOutput(
            name=SERIALIZE_OUTPUT,
            dagster_type=output_def.dagster_type,
        )],
        compute_fn=_create_serialization_lambda(solid, output_def),
        tag=StepTag.SERIALIZE,
        solid=solid,
    )
