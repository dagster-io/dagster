import csv
import os
from collections import OrderedDict
from io import BytesIO

import pytest
from dagster import (
    Bool,
    InputDefinition,
    Int,
    List,
    ModeDefinition,
    OutputDefinition,
    SerializationStrategy,
    String,
    check,
    execute_pipeline,
    lambda_solid,
    pipeline,
    usable_as_dagster_type,
)
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.events import DagsterEventType
from dagster.core.execution.api import create_execution_plan, execute_plan, scoped_pipeline_context
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.storage.type_storage import TypeStoragePlugin, TypeStoragePluginRegistry
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.core.types.dagster_type import Bool as RuntimeBool
from dagster.core.types.dagster_type import String as RuntimeString
from dagster.core.types.dagster_type import create_any_type, resolve_dagster_type
from dagster.core.utils import make_new_run_id
from dagster.utils.test import yield_empty_pipeline_context
from dagster_gcp.gcs.intermediate_storage import GCSIntermediateStorage
from dagster_gcp.gcs.resources import gcs_resource
from dagster_gcp.gcs.system_storage import gcs_plus_default_intermediate_storage_defs


class UppercaseSerializationStrategy(SerializationStrategy):  # pylint: disable=no-init
    def serialize(self, value, write_file_obj):
        return write_file_obj.write(bytes(value.upper().encode("utf-8")))

    def deserialize(self, read_file_obj):
        return read_file_obj.read().decode("utf-8").lower()


LowercaseString = create_any_type(
    "LowercaseString",
    serialization_strategy=UppercaseSerializationStrategy("uppercase"),
)


nettest = pytest.mark.nettest


def define_inty_pipeline(should_throw=True):
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid(input_defs=[InputDefinition("num", Int)], output_def=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    @lambda_solid
    def user_throw_exception():
        raise Exception("whoops")

    @pipeline(
        mode_defs=[
            ModeDefinition(
                intermediate_storage_defs=gcs_plus_default_intermediate_storage_defs,
                resource_defs={"gcs": gcs_resource},
            )
        ]
    )
    def basic_external_plan_execution():
        add_one(return_one())
        if should_throw:
            user_throw_exception()

    return basic_external_plan_execution


def get_step_output(step_events, step_key, output_name="result"):
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

    run_config = {"intermediate_storage": {"gcs": {"config": {"gcs_bucket": gcs_bucket}}}}

    run_id = make_new_run_id()

    environment_config = EnvironmentConfig.build(pipeline_def, run_config=run_config)
    execution_plan = ExecutionPlan.build(InMemoryPipeline(pipeline_def), environment_config)

    assert execution_plan.get_step_by_key("return_one")

    step_keys = ["return_one"]
    instance = DagsterInstance.ephemeral()
    pipeline_run = PipelineRun(
        pipeline_name=pipeline_def.name, run_id=run_id, run_config=run_config
    )

    return_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(step_keys, pipeline_def, environment_config),
            pipeline=InMemoryPipeline(pipeline_def),
            run_config=run_config,
            pipeline_run=pipeline_run,
            instance=instance,
        )
    )

    assert get_step_output(return_one_step_events, "return_one")
    with scoped_pipeline_context(
        execution_plan.build_subset_plan(["return_one"], pipeline_def, environment_config),
        InMemoryPipeline(pipeline_def),
        run_config,
        pipeline_run,
        instance,
    ) as context:
        intermediate_storage = GCSIntermediateStorage(
            gcs_bucket,
            run_id,
            client=context.scoped_resources_builder.build(
                required_resource_keys={"gcs"},
            ).gcs,
        )
        assert intermediate_storage.has_intermediate(context, StepOutputHandle("return_one"))
        assert (
            intermediate_storage.get_intermediate(context, Int, StepOutputHandle("return_one")).obj
            == 1
        )

    add_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(["add_one"], pipeline_def, environment_config),
            pipeline=InMemoryPipeline(pipeline_def),
            run_config=run_config,
            pipeline_run=pipeline_run,
            instance=instance,
        )
    )

    assert get_step_output(add_one_step_events, "add_one")
    with scoped_pipeline_context(
        execution_plan.build_subset_plan(["return_one"], pipeline_def, environment_config),
        InMemoryPipeline(pipeline_def),
        run_config,
        pipeline_run,
        instance,
    ) as context:
        assert intermediate_storage.has_intermediate(context, StepOutputHandle("add_one"))
        assert (
            intermediate_storage.get_intermediate(context, Int, StepOutputHandle("add_one")).obj
            == 2
        )


class FancyStringGCSTypeStoragePlugin(TypeStoragePlugin):  # pylint:disable=no-init
    @classmethod
    def compatible_with_storage_def(cls, _):
        # Not needed for these tests
        raise NotImplementedError()

    @classmethod
    def set_intermediate_object(
        cls, intermediate_storage, context, dagster_type, step_output_handle, value
    ):
        check.inst_param(intermediate_storage, "intermediate_storage", GCSIntermediateStorage)
        paths = ["intermediates", step_output_handle.step_key, step_output_handle.output_name]
        paths.append(value)
        key = intermediate_storage.object_store.key_for_paths([intermediate_storage.root] + paths)
        return intermediate_storage.object_store.set_object(
            key, "", dagster_type.serialization_strategy
        )

    @classmethod
    def get_intermediate_object(
        cls, intermediate_storage, context, dagster_type, step_output_handle
    ):
        check.inst_param(intermediate_storage, "intermediate_storage", GCSIntermediateStorage)
        paths = ["intermediates", step_output_handle.step_key, step_output_handle.output_name]
        res = list(
            intermediate_storage.object_store.client.list_blobs(
                intermediate_storage.object_store.bucket,
                prefix=intermediate_storage.key_for_paths(paths),
            )
        )
        return res[0].name.split("/")[-1]


@nettest
def test_gcs_intermediate_storage_with_type_storage_plugin(gcs_bucket):
    run_id = make_new_run_id()

    intermediate_storage = GCSIntermediateStorage(
        run_id=run_id,
        gcs_bucket=gcs_bucket,
        type_storage_plugin_registry=TypeStoragePluginRegistry(
            [(RuntimeString, FancyStringGCSTypeStoragePlugin)]
        ),
    )

    obj_name = "obj_name"

    with yield_empty_pipeline_context(run_id=run_id) as context:
        try:
            intermediate_storage.set_intermediate(
                context, RuntimeString, StepOutputHandle(obj_name), "hello"
            )

            assert intermediate_storage.has_intermediate(context, StepOutputHandle(obj_name))
            assert (
                intermediate_storage.get_intermediate(
                    context, RuntimeString, StepOutputHandle(obj_name)
                )
                == "hello"
            )

        finally:
            intermediate_storage.rm_intermediate(context, StepOutputHandle(obj_name))


@nettest
def test_gcs_intermediate_storage_with_composite_type_storage_plugin(gcs_bucket):
    run_id = make_new_run_id()

    intermediate_storage = GCSIntermediateStorage(
        run_id=run_id,
        gcs_bucket=gcs_bucket,
        type_storage_plugin_registry=TypeStoragePluginRegistry(
            [(RuntimeString, FancyStringGCSTypeStoragePlugin)]
        ),
    )

    obj_name = "obj_name"

    with yield_empty_pipeline_context(run_id=run_id) as context:
        with pytest.raises(check.NotImplementedCheckError):
            intermediate_storage.set_intermediate(
                context, resolve_dagster_type(List[String]), StepOutputHandle(obj_name), ["hello"]
            )


@nettest
def test_gcs_intermediate_storage_composite_types_with_custom_serializer_for_inner_type(gcs_bucket):
    run_id = make_new_run_id()

    intermediate_storage = GCSIntermediateStorage(run_id=run_id, gcs_bucket=gcs_bucket)

    obj_name = "list"

    with yield_empty_pipeline_context(run_id=run_id) as context:
        try:
            intermediate_storage.set_intermediate(
                context,
                resolve_dagster_type(List[LowercaseString]),
                StepOutputHandle(obj_name),
                ["foo", "bar"],
            )
            assert intermediate_storage.has_intermediate(context, StepOutputHandle(obj_name))
            assert intermediate_storage.get_intermediate(
                context, resolve_dagster_type(List[Bool]), StepOutputHandle(obj_name)
            ).obj == ["foo", "bar"]

        finally:
            intermediate_storage.rm_intermediate(context, StepOutputHandle(obj_name))


@nettest
def test_gcs_intermediate_storage_with_custom_serializer(gcs_bucket):
    run_id = make_new_run_id()

    intermediate_storage = GCSIntermediateStorage(run_id=run_id, gcs_bucket=gcs_bucket)

    obj_name = "foo"

    with yield_empty_pipeline_context(run_id=run_id) as context:
        try:
            intermediate_storage.set_intermediate(
                context, LowercaseString, StepOutputHandle(obj_name), "foo"
            )

            bucket_obj = intermediate_storage.object_store.client.get_bucket(
                intermediate_storage.object_store.bucket
            )
            blob = bucket_obj.blob(
                os.path.join(
                    *[
                        intermediate_storage.root,
                        "intermediates",
                        StepOutputHandle(obj_name).step_key,
                        StepOutputHandle(obj_name).output_name,
                    ]
                )
            )
            file_obj = BytesIO()
            blob.download_to_file(file_obj)
            file_obj.seek(0)

            assert file_obj.read().decode("utf-8") == "FOO"

            assert intermediate_storage.has_intermediate(context, StepOutputHandle(obj_name))
            assert (
                intermediate_storage.get_intermediate(
                    context, LowercaseString, StepOutputHandle(obj_name)
                ).obj
                == "foo"
            )
        finally:
            intermediate_storage.rm_intermediate(context, StepOutputHandle(obj_name))


@nettest
def test_gcs_pipeline_with_custom_prefix(gcs_bucket):
    gcs_prefix = "custom_prefix"

    pipe = define_inty_pipeline(should_throw=False)
    run_config = {
        "intermediate_storage": {
            "gcs": {"config": {"gcs_bucket": gcs_bucket, "gcs_prefix": gcs_prefix}}
        }
    }

    pipeline_run = PipelineRun(pipeline_name=pipe.name, run_config=run_config)
    instance = DagsterInstance.ephemeral()

    result = execute_pipeline(
        pipe,
        run_config=run_config,
    )
    assert result.success

    execution_plan = create_execution_plan(pipe, run_config)
    with scoped_pipeline_context(
        execution_plan,
        InMemoryPipeline(pipe),
        run_config,
        pipeline_run,
        instance,
    ) as context:
        intermediate_storage = GCSIntermediateStorage(
            run_id=result.run_id,
            gcs_bucket=gcs_bucket,
            gcs_prefix=gcs_prefix,
            client=context.scoped_resources_builder.build(
                required_resource_keys={"gcs"},
            ).gcs,
        )
        assert intermediate_storage.root == "/".join(["custom_prefix", "storage", result.run_id])
        assert (
            intermediate_storage.get_intermediate(context, Int, StepOutputHandle("return_one")).obj
            == 1
        )
        assert (
            intermediate_storage.get_intermediate(context, Int, StepOutputHandle("add_one")).obj
            == 2
        )


@nettest
def test_gcs_intermediate_storage_with_custom_prefix(gcs_bucket):
    run_id = make_new_run_id()

    intermediate_storage = GCSIntermediateStorage(
        run_id=run_id, gcs_bucket=gcs_bucket, gcs_prefix="custom_prefix"
    )
    assert intermediate_storage.root == "/".join(["custom_prefix", "storage", run_id])

    obj_name = "true"

    try:
        with yield_empty_pipeline_context(run_id=run_id) as context:

            intermediate_storage.set_intermediate(
                context, RuntimeBool, StepOutputHandle(obj_name), True
            )

            assert intermediate_storage.has_intermediate(context, StepOutputHandle(obj_name))
            assert intermediate_storage.uri_for_paths([obj_name]).startswith(
                "gs://%s/custom_prefix" % gcs_bucket
            )

    finally:
        intermediate_storage.rm_intermediate(context, StepOutputHandle(obj_name))


@nettest
def test_gcs_intermediate_storage(gcs_bucket):
    run_id = make_new_run_id()
    run_id_2 = make_new_run_id()

    intermediate_storage = GCSIntermediateStorage(run_id=run_id, gcs_bucket=gcs_bucket)
    assert intermediate_storage.root == "/".join(["dagster", "storage", run_id])

    intermediate_storage_2 = GCSIntermediateStorage(run_id=run_id_2, gcs_bucket=gcs_bucket)
    assert intermediate_storage_2.root == "/".join(["dagster", "storage", run_id_2])

    obj_name = "true"

    try:
        with yield_empty_pipeline_context(run_id=run_id) as context:

            intermediate_storage.set_intermediate(
                context, RuntimeBool, StepOutputHandle(obj_name), True
            )

            assert intermediate_storage.has_intermediate(context, StepOutputHandle(obj_name))
            assert (
                intermediate_storage.get_intermediate(
                    context, RuntimeBool, StepOutputHandle(obj_name)
                ).obj
                is True
            )
            assert intermediate_storage.uri_for_paths([obj_name]).startswith("gs://")

            intermediate_storage_2.copy_intermediate_from_run(
                context, run_id, StepOutputHandle(obj_name)
            )
            assert intermediate_storage_2.has_intermediate(context, StepOutputHandle(obj_name))
            assert (
                intermediate_storage_2.get_intermediate(
                    context, RuntimeBool, StepOutputHandle(obj_name)
                ).obj
                is True
            )
    finally:
        intermediate_storage.rm_intermediate(context, StepOutputHandle(obj_name))
        intermediate_storage_2.rm_intermediate(context, StepOutputHandle(obj_name))


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
    intermediate_storage = GCSIntermediateStorage(run_id=run_id, gcs_bucket=gcs_bucket)
    data_frame = [OrderedDict({"foo": "1", "bar": "1"}), OrderedDict({"foo": "2", "bar": "2"})]

    obj_name = "data_frame"

    try:
        with yield_empty_pipeline_context(run_id=run_id) as context:
            intermediate_storage.set_intermediate(
                context,
                resolve_dagster_type(LessSimpleDataFrame),
                StepOutputHandle(obj_name),
                data_frame,
            )

            assert intermediate_storage.has_intermediate(context, StepOutputHandle(obj_name))
            assert (
                intermediate_storage.get_intermediate(
                    context, resolve_dagster_type(LessSimpleDataFrame), StepOutputHandle(obj_name)
                ).obj
                == data_frame
            )
            assert intermediate_storage.uri_for_paths([obj_name]).startswith("gs://")

    finally:
        intermediate_storage.rm_intermediate(context, StepOutputHandle(obj_name))
