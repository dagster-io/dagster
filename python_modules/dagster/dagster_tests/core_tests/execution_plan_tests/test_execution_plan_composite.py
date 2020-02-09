from dagster import Field, Int, String, composite_solid, pipeline, solid
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.utils import make_new_run_id


@solid(config={'foo': Field(String)})
def node_a(context):
    return context.solid_config['foo']


@solid(config={'bar': Int})
def node_b(context, input_):
    return input_ * context.solid_config['bar']


@composite_solid
def composite_with_nested_config_solid():
    return node_b(node_a())


@pipeline
def composite_pipeline():
    return composite_with_nested_config_solid()


@composite_solid(
    config_fn=lambda cfg: {
        'node_a': {'config': {'foo': cfg['foo']}},
        'node_b': {'config': {'bar': cfg['bar']}},
    },
    config={'foo': Field(String), 'bar': Int},
)
def composite_with_nested_config_solid_and_config_mapping():
    return node_b(node_a())


@pipeline
def composite_pipeline_with_config_mapping():
    return composite_with_nested_config_solid_and_config_mapping()


def test_execution_plan_for_composite_solid():
    environment_dict = {
        'solids': {
            'composite_with_nested_config_solid': {
                'solids': {'node_a': {'config': {'foo': 'baz'}}, 'node_b': {'config': {'bar': 3}}}
            }
        }
    }
    execution_plan = create_execution_plan(composite_pipeline, environment_dict=environment_dict)
    pipeline_run = PipelineRun.create_empty_run(composite_pipeline.name, make_new_run_id())
    events = execute_plan(
        execution_plan,
        environment_dict=environment_dict,
        pipeline_run=pipeline_run,
        instance=DagsterInstance.ephemeral(),
    )

    assert [e.event_type_value for e in events] == [
        'ENGINE_EVENT',
        'STEP_START',
        'STEP_OUTPUT',
        'STEP_SUCCESS',
        'STEP_START',
        'STEP_INPUT',
        'STEP_OUTPUT',
        'STEP_SUCCESS',
        'ENGINE_EVENT',
    ]


def test_execution_plan_for_composite_solid_with_config_mapping():
    environment_dict = {
        'solids': {
            'composite_with_nested_config_solid_and_config_mapping': {
                'config': {'foo': 'baz', 'bar': 3}
            }
        }
    }
    execution_plan = create_execution_plan(
        composite_pipeline_with_config_mapping, environment_dict=environment_dict
    )
    pipeline_run = PipelineRun.create_empty_run(
        composite_pipeline_with_config_mapping.name, make_new_run_id()
    )

    events = execute_plan(
        execution_plan,
        environment_dict=environment_dict,
        pipeline_run=pipeline_run,
        instance=DagsterInstance.ephemeral(),
    )

    assert [e.event_type_value for e in events] == [
        'ENGINE_EVENT',
        'STEP_START',
        'STEP_OUTPUT',
        'STEP_SUCCESS',
        'STEP_START',
        'STEP_INPUT',
        'STEP_OUTPUT',
        'STEP_SUCCESS',
        'ENGINE_EVENT',
    ]
