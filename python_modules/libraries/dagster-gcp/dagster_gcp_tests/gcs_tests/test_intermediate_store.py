import csv
from collections import OrderedDict
from io import BytesIO

import pytest
from dagster_gcp.gcs.intermediate_store import GCSIntermediateStore
from dagster_gcp.gcs.resources import gcs_resource
from dagster_gcp.gcs.system_storage import gcs_plus_default_storage_defs

from dagster import (
    Bool,
    InputDefinition,
    Int,
    List,
    ModeDefinition,
    OutputDefinition,
    RunConfig,
    SerializationStrategy,
    String,
    check,
    execute_pipeline,
    lambda_solid,
    pipeline,
    usable_as_dagster_type,
)
from dagster.core.events import DagsterEventType
from dagster.core.execution.api import create_execution_plan, execute_plan, scoped_pipeline_context
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.storage.type_storage import TypeStoragePlugin, TypeStoragePluginRegistry
from dagster.core.types.dagster_type import Bool as RuntimeBool
from dagster.core.types.dagster_type import String as RuntimeString
from dagster.core.types.dagster_type import create_any_type, resolve_dagster_type
from dagster.core.utils import make_new_run_id
from dagster.utils.test import yield_empty_pipeline_context


class UppercaseSerializationStrategy(SerializationStrategy):  # pylint: disable=no-init
    def serialize(self, value, write_file_obj):
        return write_file_obj.write(bytes(value.upper().encode('utf-8')))

    def deserialize(self, read_file_obj):
        return read_file_obj.read().decode('utf-8').lower()


LowercaseString = create_any_type(
    'LowercaseString', serialization_strategy=UppercaseSerializationStrategy('uppercase'),
)


nettest = pytest.mark.nettest


def define_inty_pipeline(should_throw=True):
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid(input_defs=[InputDefinition('num', Int)], output_def=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    @lambda_solid
    def user_throw_exception():
        raise Exception('whoops')

    @pipeline(
        mode_defs=[
            ModeDefinition(
                system_storage_defs=gcs_plus_default_storage_defs,
                resource_defs={'gcs': gcs_resource},
            )
        ]
    )
    def basic_external_plan_execution():
        add_one(return_one())
        if should_throw:
            user_throw_exception()

    return basic_external_plan_execution


def get_step_output(step_events, step_key, output_name='result'):
    for step_event in step_events:
        if (
            step_event.event_type == DagsterEventType.STEP_OUTPUT
            and step_event.step_key == step_key
            and step_event.step_output_data.output_name == output_name
        ):
            return step_event
    return None


@nettest
def test_using_gcs_for_subplan(gcs_bucket):
    pipeline_def = define_inty_pipeline()

    environment_dict = {'storage': {'gcs': {'config': {'gcs_bucket': gcs_bucket}}}}

    run_id = make_new_run_id()

    execution_plan = create_execution_plan(
        pipeline_def, environment_dict=environment_dict, run_config=RunConfig(run_id=run_id)
    )

    assert execution_plan.get_step_by_key('return_one.compute')

    step_keys = ['return_one.compute']
    instance = DagsterInstance.ephemeral()
    pipeline_run = PipelineRun.create_empty_run(
        pipeline_def.name, run_id=run_id, environment_dict=environment_dict
    )

    return_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(step_keys),
            environment_dict=environment_dict,
            pipeline_run=pipeline_run,
            instance=instance,
        )
    )

    assert get_step_output(return_one_step_events, 'return_one.compute')
    with scoped_pipeline_context(
        pipeline_def,
        environment_dict,
        pipeline_run,
        instance,
        execution_plan.build_subset_plan(['return_one.compute']),
    ) as context:
        store = GCSIntermediateStore(
            gcs_bucket,
            run_id,
            client=context.scoped_resources_builder.build(
                required_resource_keys={'gcs'},
            ).gcs.client,
        )
        assert store.has_intermediate(context, 'return_one.compute')
        assert store.get_intermediate(context, 'return_one.compute', Int).obj == 1

    add_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(['add_one.compute']),
            environment_dict=environment_dict,
            pipeline_run=pipeline_run,
            instance=instance,
        )
    )

    assert get_step_output(add_one_step_events, 'add_one.compute')
    with scoped_pipeline_context(
        pipeline_def,
        environment_dict,
        pipeline_run,
        instance,
        execution_plan.build_subset_plan(['return_one.compute']),
    ) as context:
        assert store.has_intermediate(context, 'add_one.compute')
        assert store.get_intermediate(context, 'add_one.compute', Int).obj == 2


class FancyStringGCSTypeStoragePlugin(TypeStoragePlugin):  # pylint:disable=no-init
    @classmethod
    def compatible_with_storage_def(cls, _):
        # Not needed for these tests
        raise NotImplementedError()

    @classmethod
    def set_object(cls, intermediate_store, obj, context, dagster_type, paths):
        check.inst_param(intermediate_store, 'intermediate_store', GCSIntermediateStore)
        paths.append(obj)
        return intermediate_store.set_object('', context, dagster_type, paths)

    @classmethod
    def get_object(cls, intermediate_store, _context, _dagster_type, paths):
        check.inst_param(intermediate_store, 'intermediate_store', GCSIntermediateStore)
        res = list(
            intermediate_store.object_store.client.list_blobs(
                intermediate_store.object_store.bucket,
                prefix=intermediate_store.key_for_paths(paths),
            )
        )
        return res[0].name.split('/')[-1]


@nettest
def test_gcs_intermediate_store_with_type_storage_plugin(gcs_bucket):
    run_id = make_new_run_id()

    intermediate_store = GCSIntermediateStore(
        run_id=run_id,
        gcs_bucket=gcs_bucket,
        type_storage_plugin_registry=TypeStoragePluginRegistry(
            [(RuntimeString, FancyStringGCSTypeStoragePlugin)]
        ),
    )

    obj_name = 'obj_name'

    with yield_empty_pipeline_context(run_id=run_id) as context:
        try:
            intermediate_store.set_value('hello', context, RuntimeString, [obj_name])

            assert intermediate_store.has_object(context, [obj_name])
            assert intermediate_store.get_value(context, RuntimeString, [obj_name]) == 'hello'

        finally:
            intermediate_store.rm_object(context, [obj_name])


@nettest
def test_gcs_intermediate_store_with_composite_type_storage_plugin(gcs_bucket):
    run_id = make_new_run_id()

    intermediate_store = GCSIntermediateStore(
        run_id=run_id,
        gcs_bucket=gcs_bucket,
        type_storage_plugin_registry=TypeStoragePluginRegistry(
            [(RuntimeString, FancyStringGCSTypeStoragePlugin)]
        ),
    )

    obj_name = 'obj_name'

    with yield_empty_pipeline_context(run_id=run_id) as context:
        with pytest.raises(check.NotImplementedCheckError):
            intermediate_store.set_value(
                ['hello'], context, resolve_dagster_type(List[String]), [obj_name]
            )


@nettest
def test_gcs_intermediate_store_composite_types_with_custom_serializer_for_inner_type(gcs_bucket):
    run_id = make_new_run_id()

    intermediate_store = GCSIntermediateStore(run_id=run_id, gcs_bucket=gcs_bucket)

    obj_name = 'list'

    with yield_empty_pipeline_context(run_id=run_id) as context:
        try:
            intermediate_store.set_object(
                ['foo', 'bar'], context, resolve_dagster_type(List[LowercaseString]), [obj_name],
            )
            assert intermediate_store.has_object(context, [obj_name])
            assert intermediate_store.get_object(
                context, resolve_dagster_type(List[Bool]), [obj_name]
            ).obj == ['foo', 'bar']

        finally:
            intermediate_store.rm_object(context, [obj_name])


@nettest
def test_gcs_intermediate_store_with_custom_serializer(gcs_bucket):
    run_id = make_new_run_id()

    intermediate_store = GCSIntermediateStore(run_id=run_id, gcs_bucket=gcs_bucket)

    obj_name = 'foo'

    with yield_empty_pipeline_context(run_id=run_id) as context:
        try:
            intermediate_store.set_object('foo', context, LowercaseString, [obj_name])

            bucket_obj = intermediate_store.object_store.client.get_bucket(
                intermediate_store.object_store.bucket
            )
            blob = bucket_obj.blob('/'.join([intermediate_store.root] + [obj_name]))
            file_obj = BytesIO()
            blob.download_to_file(file_obj)
            file_obj.seek(0)

            assert file_obj.read().decode('utf-8') == 'FOO'

            assert intermediate_store.has_object(context, [obj_name])
            assert intermediate_store.get_object(context, LowercaseString, [obj_name]).obj == 'foo'
        finally:
            intermediate_store.rm_object(context, [obj_name])


@nettest
def test_gcs_pipeline_with_custom_prefix(gcs_bucket):
    run_id = make_new_run_id()
    gcs_prefix = 'custom_prefix'

    pipe = define_inty_pipeline(should_throw=False)
    environment_dict = {
        'storage': {'gcs': {'config': {'gcs_bucket': gcs_bucket, 'gcs_prefix': gcs_prefix}}}
    }

    pipeline_run = PipelineRun.create_empty_run(
        pipe.name, run_id=run_id, environment_dict=environment_dict
    )
    instance = DagsterInstance.ephemeral()

    result = execute_pipeline(
        pipe, environment_dict=environment_dict, run_config=RunConfig(run_id=run_id),
    )
    assert result.success

    execution_plan = create_execution_plan(pipe, environment_dict, run_config=pipeline_run)
    with scoped_pipeline_context(
        pipe, environment_dict, pipeline_run, instance, execution_plan
    ) as context:
        store = GCSIntermediateStore(
            run_id=run_id,
            gcs_bucket=gcs_bucket,
            gcs_prefix=gcs_prefix,
            client=context.scoped_resources_builder.build(
                required_resource_keys={'gcs'},
            ).gcs.client,
        )
        assert store.root == '/'.join(['custom_prefix', 'storage', run_id])
        assert store.get_intermediate(context, 'return_one.compute', Int).obj == 1
        assert store.get_intermediate(context, 'add_one.compute', Int).obj == 2


@nettest
def test_gcs_intermediate_store_with_custom_prefix(gcs_bucket):
    run_id = make_new_run_id()

    intermediate_store = GCSIntermediateStore(
        run_id=run_id, gcs_bucket=gcs_bucket, gcs_prefix='custom_prefix'
    )
    assert intermediate_store.root == '/'.join(['custom_prefix', 'storage', run_id])

    obj_name = 'true'

    try:
        with yield_empty_pipeline_context(run_id=run_id) as context:

            intermediate_store.set_object(True, context, RuntimeBool, [obj_name])

            assert intermediate_store.has_object(context, [obj_name])
            assert intermediate_store.uri_for_paths([obj_name]).startswith(
                'gs://%s/custom_prefix' % gcs_bucket
            )

    finally:
        intermediate_store.rm_object(context, [obj_name])


@nettest
def test_gcs_intermediate_store(gcs_bucket):
    run_id = make_new_run_id()
    run_id_2 = make_new_run_id()

    intermediate_store = GCSIntermediateStore(run_id=run_id, gcs_bucket=gcs_bucket)
    assert intermediate_store.root == '/'.join(['dagster', 'storage', run_id])

    intermediate_store_2 = GCSIntermediateStore(run_id=run_id_2, gcs_bucket=gcs_bucket)
    assert intermediate_store_2.root == '/'.join(['dagster', 'storage', run_id_2])

    obj_name = 'true'

    try:
        with yield_empty_pipeline_context(run_id=run_id) as context:

            intermediate_store.set_object(True, context, RuntimeBool, [obj_name])

            assert intermediate_store.has_object(context, [obj_name])
            assert intermediate_store.get_object(context, RuntimeBool, [obj_name]).obj is True
            assert intermediate_store.uri_for_paths([obj_name]).startswith('gs://')

            intermediate_store_2.copy_object_from_prev_run(context, run_id, [obj_name])
            assert intermediate_store_2.has_object(context, [obj_name])
            assert intermediate_store_2.get_object(context, RuntimeBool, [obj_name]).obj is True
    finally:
        intermediate_store.rm_object(context, [obj_name])
        intermediate_store_2.rm_object(context, [obj_name])


class CsvSerializationStrategy(SerializationStrategy):
    def __init__(self):
        super(CsvSerializationStrategy, self).__init__(
            "csv_strategy", read_mode="r", write_mode="w"
        )

    def serialize(self, value, write_file_obj):
        fieldnames = value[0]
        writer = csv.DictWriter(write_file_obj, fieldnames)
        writer.writeheader()
        writer.writerows(value)

    def deserialize(self, read_file_obj):
        reader = csv.DictReader(read_file_obj)
        return LessSimpleDataFrame([row for row in reader])


@usable_as_dagster_type(
    name="LessSimpleDataFrame",
    description=("A naive representation of a data frame, e.g., as returned by " "csv.DictReader."),
    serialization_strategy=CsvSerializationStrategy(),
)
class LessSimpleDataFrame(list):
    pass


def test_custom_read_write_mode(gcs_bucket):
    run_id = make_new_run_id()
    intermediate_store = GCSIntermediateStore(run_id=run_id, gcs_bucket=gcs_bucket)
    data_frame = [OrderedDict({'foo': '1', 'bar': '1'}), OrderedDict({'foo': '2', 'bar': '2'})]

    obj_name = 'data_frame'

    try:
        with yield_empty_pipeline_context(run_id=run_id) as context:
            intermediate_store.set_object(
                data_frame, context, resolve_dagster_type(LessSimpleDataFrame), [obj_name]
            )

            assert intermediate_store.has_object(context, [obj_name])
            assert (
                intermediate_store.get_object(
                    context, resolve_dagster_type(LessSimpleDataFrame), [obj_name]
                ).obj
                == data_frame
            )
            assert intermediate_store.uri_for_paths([obj_name]).startswith('gs://')

    finally:
        intermediate_store.rm_object(context, [obj_name])
