import csv
import os
from collections import OrderedDict
from io import BytesIO

import pytest
from dagster import Bool, List, SerializationStrategy, usable_as_dagster_type
from dagster.core.events import DagsterEventType
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.types.dagster_type import Bool as RuntimeBool
from dagster.core.types.dagster_type import create_any_type, resolve_dagster_type
from dagster.core.utils import make_new_run_id
from dagster.utils.test import yield_empty_pipeline_context
from dagster_gcp.gcs.intermediate_storage import GCSIntermediateStorage


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
