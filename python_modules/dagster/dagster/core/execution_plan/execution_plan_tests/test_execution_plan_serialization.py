from __future__ import unicode_literals
import json
import pytest

from pyrsistent import (
    PClass,
    field,
    PTypeError,
)

from dagster import (
    DependencyDefinition,
    ExpectationDefinition,
    ExpectationResult,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    check,
    lambda_solid,
    types,
)

from dagster.core.execution import (
    StepResult,
    create_execution_plan,
    create_typed_environment,
    execute_plan,
)

from dagster.core.execution_plan.objects import (
    DepMap,
    DepVector,
    ExecutionPlanMeta,
    ExecutionStepMeta,
    StepInput,
    StepInputMeta,
    StepInputMetaVector,
    StepOutputHandle,
    StepOutputMeta,
    StepOutputMetaVector,
    StepTag,
)

from dagster.core.execution_plan.recreate import (
    recreate_execution_steps,
    recreate_execution_plan,
)

# Generic PClass Testing (delete at some point)


class FooBar(PClass):
    foo = field(type=int)
    bar = field(type=int)

    @property
    def added(self):
        return self.foo + self.bar


def test_foobar():
    obj = FooBar(foo=1, bar=2)
    assert obj.foo == 1
    assert obj.bar == 2


def test_typeerror():
    with pytest.raises(PTypeError):
        FooBar(foo='djfkkd', bar=2)


def test_serialize_cycle():
    obj = FooBar(foo=1, bar=2)
    assert obj.serialize() == {'foo': 1, 'bar': 2}
    obj_serialize_cycled = FooBar.create(obj.serialize())
    assert obj_serialize_cycled == obj
    assert obj_serialize_cycled.serialize() == {'foo': 1, 'bar': 2}


def test_derived():
    obj = FooBar(foo=1, bar=2)
    assert obj.added == 3


def test_repr():
    obj = FooBar(foo=1, bar=2)
    print(repr(obj))


# Execution Plan Testing


def json_round_trip(cls, thing):
    return cls.create(json.loads(json.dumps(thing.serialize())))


def test_step_output_meta():
    meta = StepOutputMeta(name='some_output', dagster_type_name='Int')
    assert meta.serialize() == {'name': 'some_output', 'dagster_type_name': 'Int'}
    assert StepOutputMeta.create(meta.serialize()) == meta
    assert json_round_trip(StepOutputMeta, meta) == meta


def test_step_input_meta():
    meta = StepInputMeta(
        name='some_input',
        dagster_type_name='Int',
        prev_output_handle=StepOutputHandle(
            step_key='prev_step',
            output_name='prev_output',
        )
    )
    assert meta.serialize() == {
        'name': 'some_input',
        'dagster_type_name': 'Int',
        'prev_output_handle': {
            'step_key': 'prev_step',
            'output_name': 'prev_output'
        }
    }
    assert StepInputMeta.create(meta.serialize()) == meta
    assert json_round_trip(StepInputMeta, meta) == meta


def test_step_input_failed():
    step_input = StepInput.from_props(
        'some_input', types.Int, StepOutputHandle(
            step_key='prev_step',
            output_name='prev_output',
        )
    )

    with pytest.raises(TypeError):
        assert json_round_trip(StepInput, step_input) == step_input


def test_execution_step_meta(snapshot):
    step_meta = create_stub_meta()

    snapshot.assert_match(step_meta.serialize())
    assert json_round_trip(ExecutionStepMeta, step_meta) == step_meta


def test_execution_plan_meta(snapshot):
    plan_meta = ExecutionPlanMeta(
        step_metas=[create_stub_meta()],
        deps=DepMap({
            'something': DepVector(['something_else'])
        }),
    )

    snapshot.assert_match(plan_meta.serialize())
    assert json_round_trip(ExecutionPlanMeta, plan_meta) == plan_meta


def create_stub_meta():
    return ExecutionStepMeta(
        key='step_key',
        step_input_metas=StepInputMetaVector(
            [
                StepInputMeta(
                    name='input_one',
                    dagster_type_name='Int',
                    prev_output_handle=StepOutputHandle(
                        step_key='prev_step',
                        output_name='some_output',
                    )
                )
            ]
        ),
        step_output_metas=StepOutputMetaVector(
            [
                StepOutputMeta(
                    name='output_one',
                    dagster_type_name='String',
                ),
            ]
        ),
        tag=StepTag.TRANSFORM,
        solid_name='some_solid',
    )


def test_basic_pipeline_execution_plan_serialization(snapshot):
    @lambda_solid(output=OutputDefinition(types.Int))
    def return_one():
        return 1

    @lambda_solid(
        inputs=[InputDefinition('num', dagster_type=types.Int)],
        output=OutputDefinition(types.Int),
    )
    def add_one(num):
        return num + 1

    pipeline_def = PipelineDefinition(
        name='basic_plan_serialization',
        solids=[return_one, add_one],
        dependencies={
            'add_one': {
                'num': DependencyDefinition('return_one'),
            },
        },
    )

    typed_environment = create_typed_environment(pipeline_def)

    execution_plan = create_execution_plan(pipeline_def, typed_environment)

    snapshot.assert_match(execution_plan.meta.serialize())

    assert_plan_recreation_matches(pipeline_def)

    results = execute_plan(pipeline_def, execution_plan)
    assert len(results) == 2

    execution_plan_data = execution_plan.meta.serialize()

    recreated_plan = recreate_execution_plan(pipeline_def, typed_environment, execution_plan_data)
    results_from_recreated = execute_plan(pipeline_def, recreated_plan)
    assert len(results_from_recreated) == 2

    assert results_from_recreated[0].step.key == 'return_one.transform'
    assert results_from_recreated[0].success
    assert results_from_recreated[0].success_data.value == 1
    assert results_from_recreated[1].success
    assert results_from_recreated[1].success_data.value == 2

    assert_result_list_equivalent(results, results_from_recreated)


def assert_result_list_equivalent(left, right):
    check.list_param(left, 'left', of_type=StepResult)
    check.list_param(right, 'right', of_type=StepResult)
    assert len(left) == len(right)

    for left_result, right_result in zip(left, right):
        assert left_result.step.meta == right_result.step.meta
        assert left_result.success == right_result.success
        assert left_result.tag == right_result.tag
        assert left_result.success_data == right_result.success_data
        assert left_result.failure_data == right_result.failure_data


def test_execution_plan_with_expectations(snapshot):
    @lambda_solid(output=OutputDefinition(types.Int))
    def return_one():
        return 1

    @lambda_solid(
        inputs=[
            InputDefinition(
                'num',
                dagster_type=types.Int,
                expectations=[
                    ExpectationDefinition(
                        name='positive',
                        expectation_fn=lambda _info, value: ExpectationResult(value > 0)
                    )
                ]
            )
        ],
        output=OutputDefinition(types.Int),
    )
    def add_one(num):
        return num + 1

    pipeline_def = PipelineDefinition(
        name='basic_plan_with_expectations',
        solids=[return_one, add_one],
        dependencies={
            'add_one': {
                'num': DependencyDefinition('return_one'),
            },
        },
    )

    typed_environment = create_typed_environment(pipeline_def)
    execution_plan = create_execution_plan(pipeline_def, typed_environment)
    snapshot.assert_match(execution_plan.meta.serialize())

    # assert_plan_recreation_matches(pipeline_def)


def assert_plan_recreation_matches(pipeline_def, environment_config=None):
    typed_environment = create_typed_environment(pipeline_def, environment_config)
    execution_plan = create_execution_plan(pipeline_def, typed_environment)
    execution_plan_data = execution_plan.meta.serialize()
    recreated_plan = recreate_execution_plan(pipeline_def, typed_environment, execution_plan_data)

    results = execute_plan(pipeline_def, execution_plan, environment_config)
    recreated_results = execute_plan(pipeline_def, recreated_plan, environment_config)

    assert_result_list_equivalent(results, recreated_results)