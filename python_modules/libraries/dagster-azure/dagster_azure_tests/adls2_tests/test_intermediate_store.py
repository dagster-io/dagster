import csv
import os
from collections import OrderedDict

import pytest
from dagster_azure.adls2 import (
    ADLS2IntermediateStore,
    adls2_plus_default_storage_defs,
    adls2_resource,
    create_adls2_client,
)
from dagster_azure.blob import create_blob_client

from dagster import (
    Bool,
    InputDefinition,
    Int,
    List,
    ModeDefinition,
    OutputDefinition,
    PipelineRun,
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
from dagster.core.execution.plan.objects import StepOutputHandle
from dagster.core.instance import DagsterInstance
from dagster.core.storage.intermediates_manager import ObjectStoreIntermediateStorage
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
                system_storage_defs=adls2_plus_default_storage_defs,
                resource_defs={'adls2': adls2_resource},
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


def get_azure_credential():
    try:
        return {'key': os.environ["AZURE_STORAGE_ACCOUNT_KEY"]}
    except KeyError:
        raise Exception("AZURE_STORAGE_ACCOUNT_KEY must be set for intermediate store tests")


def get_adls2_client(storage_account):
    creds = get_azure_credential()["key"]
    return create_adls2_client(storage_account, creds)


def get_blob_client(storage_account):
    creds = get_azure_credential()["key"]
    return create_blob_client(storage_account, creds)


@nettest
def test_using_adls2_for_subplan(storage_account, file_system):
    pipeline_def = define_inty_pipeline()

    run_config = {
        'resources': {
            'adls2': {
                'config': {'storage_account': storage_account, 'credential': get_azure_credential()}
            }
        },
        'storage': {'adls2': {'config': {'adls2_file_system': file_system}}},
    }

    run_id = make_new_run_id()

    execution_plan = create_execution_plan(pipeline_def, run_config=run_config)

    assert execution_plan.get_step_by_key('return_one.compute')

    step_keys = ['return_one.compute']
    instance = DagsterInstance.ephemeral()
    pipeline_run = PipelineRun(
        pipeline_name=pipeline_def.name, run_id=run_id, run_config=run_config
    )

    return_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(step_keys),
            run_config=run_config,
            pipeline_run=pipeline_run,
            instance=instance,
        )
    )

    assert get_step_output(return_one_step_events, 'return_one.compute')
    with scoped_pipeline_context(
        execution_plan.build_subset_plan(['return_one.compute']),
        run_config,
        pipeline_run,
        instance,
    ) as context:

        resource = context.scoped_resources_builder.build(required_resource_keys={'adls2'}).adls2
        store = ADLS2IntermediateStore(
            file_system=file_system,
            run_id=run_id,
            adls2_client=resource.adls2_client,
            blob_client=resource.blob_client,
        )
        intermediates_manager = ObjectStoreIntermediateStorage(store)
        step_output_handle = StepOutputHandle('return_one.compute')
        assert intermediates_manager.has_intermediate(context, step_output_handle)
        assert intermediates_manager.get_intermediate(context, Int, step_output_handle).obj == 1

    add_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(['add_one.compute']),
            run_config=run_config,
            pipeline_run=pipeline_run,
            instance=instance,
        )
    )

    assert get_step_output(add_one_step_events, 'add_one.compute')
    with scoped_pipeline_context(
        execution_plan.build_subset_plan(['add_one.compute']), run_config, pipeline_run, instance,
    ) as context:
        step_output_handle = StepOutputHandle('add_one.compute')
        assert intermediates_manager.has_intermediate(context, step_output_handle)
        assert intermediates_manager.get_intermediate(context, Int, step_output_handle).obj == 2


class FancyStringS3TypeStoragePlugin(TypeStoragePlugin):  # pylint:disable=no-init
    @classmethod
    def compatible_with_storage_def(cls, _):
        # Not needed for these tests
        raise NotImplementedError()

    @classmethod
    def set_object(cls, intermediate_store, obj, context, dagster_type, paths):
        check.inst_param(intermediate_store, 'intermediate_store', ADLS2IntermediateStore)
        paths.append(obj)
        return intermediate_store.set_object('', context, dagster_type, paths)

    @classmethod
    def get_object(cls, intermediate_store, _context, _dagster_type, paths):
        check.inst_param(intermediate_store, 'intermediate_store', ADLS2IntermediateStore)
        res = intermediate_store.object_store.file_system_client.get_paths(
            intermediate_store.key_for_paths(paths)
        )
        return next(res).name.split('/')[-1]


@nettest
def test_adls2_intermediate_store_with_type_storage_plugin(storage_account, file_system):
    run_id = make_new_run_id()

    intermediate_store = ADLS2IntermediateStore(
        adls2_client=get_adls2_client(storage_account),
        blob_client=get_blob_client(storage_account),
        run_id=run_id,
        file_system=file_system,
        type_storage_plugin_registry=TypeStoragePluginRegistry(
            [(RuntimeString, FancyStringS3TypeStoragePlugin)]
        ),
    )

    with yield_empty_pipeline_context(run_id=run_id) as context:
        try:
            intermediate_store.set_value('hello', context, RuntimeString, ['obj_name'])

            assert intermediate_store.has_object(context, ['obj_name'])
            assert intermediate_store.get_value(context, RuntimeString, ['obj_name']) == 'hello'

        finally:
            intermediate_store.rm_object(context, ['obj_name'])


@nettest
def test_adls2_intermediate_store_with_composite_type_storage_plugin(storage_account, file_system):
    run_id = make_new_run_id()

    intermediate_store = ADLS2IntermediateStore(
        adls2_client=get_adls2_client(storage_account),
        blob_client=get_blob_client(storage_account),
        run_id=run_id,
        file_system=file_system,
        type_storage_plugin_registry=TypeStoragePluginRegistry(
            [(RuntimeString, FancyStringS3TypeStoragePlugin)]
        ),
    )
    with yield_empty_pipeline_context(run_id=run_id) as context:
        with pytest.raises(check.NotImplementedCheckError):
            intermediate_store.set_value(
                ['hello'], context, resolve_dagster_type(List[String]), ['obj_name']
            )


@nettest
def test_adls2_intermediate_store_composite_types_with_custom_serializer_for_inner_type(
    storage_account, file_system
):
    run_id = make_new_run_id()

    intermediate_store = ADLS2IntermediateStore(
        adls2_client=get_adls2_client(storage_account),
        blob_client=get_blob_client(storage_account),
        run_id=run_id,
        file_system=file_system,
    )

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
def test_adls2_intermediate_store_with_custom_serializer(storage_account, file_system):
    run_id = make_new_run_id()

    intermediate_store = ADLS2IntermediateStore(
        adls2_client=get_adls2_client(storage_account),
        blob_client=get_blob_client(storage_account),
        run_id=run_id,
        file_system=file_system,
    )

    with yield_empty_pipeline_context(run_id=run_id) as context:
        try:
            intermediate_store.set_object('foo', context, LowercaseString, ['foo'])

            assert (
                intermediate_store.object_store.file_system_client.get_file_client(
                    '/'.join([intermediate_store.root] + ['foo']),
                )
                .download_file()
                .readall()
                .decode('utf-8')
                == 'FOO'
            )

            assert intermediate_store.has_object(context, ['foo'])
            assert intermediate_store.get_object(context, LowercaseString, ['foo']).obj == 'foo'
        finally:
            intermediate_store.rm_object(context, ['foo'])


@nettest
def test_adls2_pipeline_with_custom_prefix(storage_account, file_system):
    adls2_prefix = 'custom_prefix'

    pipe = define_inty_pipeline(should_throw=False)
    run_config = {
        'resources': {
            'adls2': {
                'config': {'storage_account': storage_account, 'credential': get_azure_credential()}
            }
        },
        'storage': {
            'adls2': {'config': {'adls2_file_system': file_system, 'adls2_prefix': adls2_prefix}}
        },
    }

    pipeline_run = PipelineRun(pipeline_name=pipe.name, run_config=run_config)
    instance = DagsterInstance.ephemeral()

    result = execute_pipeline(pipe, run_config=run_config,)
    assert result.success

    execution_plan = create_execution_plan(pipe, run_config)
    with scoped_pipeline_context(execution_plan, run_config, pipeline_run, instance,) as context:
        resource = context.scoped_resources_builder.build(required_resource_keys={'adls2'}).adls2
        store = ADLS2IntermediateStore(
            run_id=result.run_id,
            file_system=file_system,
            prefix=adls2_prefix,
            adls2_client=resource.adls2_client,
            blob_client=resource.blob_client,
        )
        intermediates_manager = ObjectStoreIntermediateStorage(store)
        assert store.root == '/'.join(['custom_prefix', 'storage', result.run_id])
        assert (
            intermediates_manager.get_intermediate(
                context, Int, StepOutputHandle('return_one.compute')
            ).obj
            == 1
        )
        assert (
            intermediates_manager.get_intermediate(
                context, Int, StepOutputHandle('add_one.compute')
            ).obj
            == 2
        )


@nettest
def test_adls2_intermediate_store_with_custom_prefix(storage_account, file_system):
    run_id = make_new_run_id()

    intermediate_store = ADLS2IntermediateStore(
        adls2_client=get_adls2_client(storage_account),
        blob_client=get_blob_client(storage_account),
        run_id=run_id,
        file_system=file_system,
        prefix='custom_prefix',
    )
    assert intermediate_store.root == '/'.join(['custom_prefix', 'storage', run_id])

    try:
        with yield_empty_pipeline_context(run_id=run_id) as context:

            intermediate_store.set_object(True, context, RuntimeBool, ['true'])

            assert intermediate_store.has_object(context, ['true'])
            assert intermediate_store.uri_for_paths(['true']).startswith(
                'abfss://{fs}@{account}.dfs.core.windows.net/custom_prefix'.format(
                    account=storage_account, fs=file_system
                )
            )

    finally:
        intermediate_store.rm_object(context, ['true'])


@nettest
def test_adls2_intermediate_store(storage_account, file_system):
    run_id = make_new_run_id()
    run_id_2 = make_new_run_id()

    intermediate_store = ADLS2IntermediateStore(
        adls2_client=get_adls2_client(storage_account),
        blob_client=get_blob_client(storage_account),
        run_id=run_id,
        file_system=file_system,
    )
    assert intermediate_store.root == '/'.join(['dagster', 'storage', run_id])

    intermediate_store_2 = ADLS2IntermediateStore(
        adls2_client=get_adls2_client(storage_account),
        blob_client=get_blob_client(storage_account),
        run_id=run_id_2,
        file_system=file_system,
    )
    assert intermediate_store_2.root == '/'.join(['dagster', 'storage', run_id_2])

    try:
        with yield_empty_pipeline_context(run_id=run_id) as context:

            intermediate_store.set_object(True, context, RuntimeBool, ['true'])

            assert intermediate_store.has_object(context, ['true'])
            assert intermediate_store.get_object(context, RuntimeBool, ['true']).obj is True
            assert intermediate_store.uri_for_paths(['true']).startswith('abfss://')

            intermediate_store_2.copy_object_from_run(context, run_id, ['true'])
            assert intermediate_store_2.has_object(context, ['true'])
            assert intermediate_store_2.get_object(context, RuntimeBool, ['true']).obj is True
    finally:
        intermediate_store.rm_object(context, ['true'])
        intermediate_store_2.rm_object(context, ['true'])


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


def test_custom_read_write_mode(storage_account, file_system):
    run_id = make_new_run_id()
    data_frame = [OrderedDict({'foo': '1', 'bar': '1'}), OrderedDict({'foo': '2', 'bar': '2'})]
    try:
        with yield_empty_pipeline_context(run_id=run_id) as context:
            intermediate_store = ADLS2IntermediateStore(
                adls2_client=get_adls2_client(storage_account),
                blob_client=get_blob_client(storage_account),
                run_id=run_id,
                file_system=file_system,
            )
            intermediate_store.set_object(
                data_frame, context, resolve_dagster_type(LessSimpleDataFrame), ['data_frame']
            )

            assert intermediate_store.has_object(context, ['data_frame'])
            assert (
                intermediate_store.get_object(
                    context, resolve_dagster_type(LessSimpleDataFrame), ['data_frame']
                ).obj
                == data_frame
            )
            assert intermediate_store.uri_for_paths(['data_frame']).startswith('abfss://')

    finally:
        intermediate_store.rm_object(context, ['data_frame'])
