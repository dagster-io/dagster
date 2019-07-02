import os
import uuid

import pytest

from dagster import (
    Bool,
    DependencyDefinition,
    InputDefinition,
    Int,
    List,
    OutputDefinition,
    PipelineDefinition,
    RunConfig,
    SerializationStrategy,
    String,
    check,
    lambda_solid,
)

from dagster.core.events import DagsterEventType

from dagster.core.execution.api import create_execution_plan, execute_plan, scoped_pipeline_context

from dagster.core.storage.type_storage import TypeStoragePlugin

from dagster.core.types.runtime import (
    String as RuntimeString,
    resolve_to_runtime_type,
    RuntimeType,
    Bool as RuntimeBool,
)

from dagster.utils.test import yield_empty_pipeline_context

from dagster_aws.s3.intermediate_store import S3IntermediateStore


class UppercaseSerializationStrategy(SerializationStrategy):  # pylint: disable=no-init
    def serialize(self, value, write_file_obj):
        return write_file_obj.write(bytes(value.upper().encode('utf-8')))

    def deserialize(self, read_file_obj):
        return read_file_obj.read().decode('utf-8').lower()


class LowercaseString(RuntimeType):
    def __init__(self):
        super(LowercaseString, self).__init__(
            'lowercase_string',
            'LowercaseString',
            serialization_strategy=UppercaseSerializationStrategy(),
        )


def aws_credentials_present():
    return os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY')


aws = pytest.mark.skipif(not aws_credentials_present(), reason='Couldn\'t find AWS credentials')

nettest = pytest.mark.nettest


def define_inty_pipeline():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid(input_defs=[InputDefinition('num', Int)], output_def=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    @lambda_solid
    def user_throw_exception():
        raise Exception('whoops')

    pipeline = PipelineDefinition(
        name='basic_external_plan_execution',
        solid_defs=[return_one, add_one, user_throw_exception],
        dependencies={'add_one': {'num': DependencyDefinition('return_one')}},
    )
    return pipeline


def get_step_output(step_events, step_key, output_name='result'):
    for step_event in step_events:
        if (
            step_event.event_type == DagsterEventType.STEP_OUTPUT
            and step_event.step_key == step_key
            and step_event.step_output_data.output_name == output_name
        ):
            return step_event
    return None


@aws
@nettest
def test_using_s3_for_subplan(s3_bucket):
    pipeline = define_inty_pipeline()

    environment_dict = {'storage': {'s3': {'s3_bucket': s3_bucket}}}

    execution_plan = create_execution_plan(pipeline, environment_dict=environment_dict)

    assert execution_plan.get_step_by_key('return_one.compute')

    step_keys = ['return_one.compute']

    run_id = str(uuid.uuid4())

    store = S3IntermediateStore(s3_bucket, run_id)

    try:
        return_one_step_events = list(
            execute_plan(
                execution_plan,
                environment_dict=environment_dict,
                run_config=RunConfig(run_id=run_id),
                step_keys_to_execute=step_keys,
            )
        )

        assert get_step_output(return_one_step_events, 'return_one.compute')
        with scoped_pipeline_context(
            pipeline, environment_dict, RunConfig(run_id=run_id)
        ) as context:
            assert store.has_intermediate(context, 'return_one.compute')
            assert store.get_intermediate(context, 'return_one.compute', Int) == 1

        add_one_step_events = list(
            execute_plan(
                execution_plan,
                environment_dict=environment_dict,
                run_config=RunConfig(run_id=run_id),
                step_keys_to_execute=['add_one.compute'],
            )
        )

        assert get_step_output(add_one_step_events, 'add_one.compute')
        with scoped_pipeline_context(
            pipeline, environment_dict, RunConfig(run_id=run_id)
        ) as context:
            assert store.has_intermediate(context, 'add_one.compute')
            assert store.get_intermediate(context, 'add_one.compute', Int) == 2
    finally:
        with scoped_pipeline_context(
            pipeline, environment_dict, RunConfig(run_id=run_id)
        ) as context:
            store.rm_intermediate(context, 'return_one.compute')
            store.rm_intermediate(context, 'add_one.compute')


class FancyStringS3TypeStoragePlugin(TypeStoragePlugin):  # pylint:disable=no-init
    @classmethod
    def compatible_with_storage_def(cls, _):
        # Not needed for these tests
        raise NotImplementedError()

    @classmethod
    def set_object(cls, intermediate_store, obj, context, runtime_type, paths):
        check.inst_param(intermediate_store, 'intermediate_store', S3IntermediateStore)
        paths.append(obj)
        return intermediate_store.set_object('', context, runtime_type, paths)

    @classmethod
    def get_object(cls, intermediate_store, _context, _runtime_type, paths):
        check.inst_param(intermediate_store, 'intermediate_store', S3IntermediateStore)
        res = intermediate_store.object_store.s3.list_objects(
            Bucket=intermediate_store.object_store.bucket,
            Prefix=intermediate_store.key_for_paths(paths),
        )
        return res['Contents'][0]['Key'].split('/')[-1]


@aws
@nettest
def test_s3_intermediate_store_with_type_storage_plugin():
    run_id = str(uuid.uuid4())

    # FIXME need a dedicated test bucket
    intermediate_store = S3IntermediateStore(
        run_id=run_id,
        s3_bucket='dagster-airflow-scratch',
        type_storage_plugin_registry={RuntimeString.inst(): FancyStringS3TypeStoragePlugin},
    )

    with yield_empty_pipeline_context(run_id=run_id) as context:
        try:
            intermediate_store.set_value('hello', context, RuntimeString.inst(), ['obj_name'])

            assert intermediate_store.has_object(context, ['obj_name'])
            assert (
                intermediate_store.get_value(context, RuntimeString.inst(), ['obj_name']) == 'hello'
            )

        finally:
            intermediate_store.rm_object(context, ['obj_name'])


@aws
@nettest
def test_s3_intermediate_store_with_composite_type_storage_plugin():
    run_id = str(uuid.uuid4())

    # FIXME need a dedicated test bucket
    intermediate_store = S3IntermediateStore(
        run_id=run_id,
        s3_bucket='dagster-airflow-scratch',
        type_storage_plugin_registry={RuntimeString.inst(): FancyStringS3TypeStoragePlugin},
    )

    with yield_empty_pipeline_context(run_id=run_id) as context:
        with pytest.raises(check.NotImplementedCheckError):
            intermediate_store.set_value(
                ['hello'], context, resolve_to_runtime_type(List[String]), ['obj_name']
            )


@aws
@nettest
def test_s3_intermediate_store_composite_types_with_custom_serializer_for_inner_type():
    run_id = str(uuid.uuid4())

    intermediate_store = S3IntermediateStore(run_id=run_id, s3_bucket='dagster-airflow-scratch')
    with yield_empty_pipeline_context(run_id=run_id) as context:
        try:
            intermediate_store.set_object(
                ['foo', 'bar'],
                context,
                resolve_to_runtime_type(List[LowercaseString]).inst(),
                ['list'],
            )
            assert intermediate_store.has_object(context, ['list'])
            assert intermediate_store.get_object(
                context, resolve_to_runtime_type(List[Bool]).inst(), ['list']
            ) == ['foo', 'bar']

        finally:
            intermediate_store.rm_object(context, ['foo'])


@aws
@nettest
def test_s3_intermediate_store_with_custom_serializer():
    run_id = str(uuid.uuid4())

    # FIXME need a dedicated test bucket
    intermediate_store = S3IntermediateStore(run_id=run_id, s3_bucket='dagster-airflow-scratch')

    with yield_empty_pipeline_context(run_id=run_id) as context:
        try:
            intermediate_store.set_object('foo', context, LowercaseString.inst(), ['foo'])

            assert (
                intermediate_store.object_store.s3.get_object(
                    Bucket=intermediate_store.object_store.bucket,
                    Key='/'.join([intermediate_store.root] + ['foo']),
                )['Body']
                .read()
                .decode('utf-8')
                == 'FOO'
            )

            assert intermediate_store.has_object(context, ['foo'])
            assert intermediate_store.get_object(context, LowercaseString.inst(), ['foo']) == 'foo'
        finally:
            intermediate_store.rm_object(context, ['foo'])


@aws
@nettest
def test_s3_intermediate_store():
    run_id = str(uuid.uuid4())

    # FIXME need a dedicated test bucket
    intermediate_store = S3IntermediateStore(run_id=run_id, s3_bucket='dagster-airflow-scratch')
    assert intermediate_store.root == '/'.join(['dagster', 'runs', run_id, 'files'])

    with yield_empty_pipeline_context(run_id=run_id) as context:
        try:
            intermediate_store.set_object(True, context, RuntimeBool.inst(), ['true'])

            assert intermediate_store.has_object(context, ['true'])
            assert intermediate_store.get_object(context, RuntimeBool.inst(), ['true']) is True
            assert intermediate_store.uri_for_paths(['true']).startswith('s3://')

        finally:
            intermediate_store.rm_object(context, ['true'])
