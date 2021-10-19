import csv
import os
from collections import OrderedDict

from dagster import (
    Bool,
    InputDefinition,
    Int,
    List,
    ModeDefinition,
    OutputDefinition,
    SerializationStrategy,
    lambda_solid,
    pipeline,
    usable_as_dagster_type,
)
from dagster.core.events import DagsterEventType
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.types.dagster_type import Bool as RuntimeBool
from dagster.core.types.dagster_type import create_any_type, resolve_dagster_type
from dagster.core.utils import make_new_run_id
from dagster.utils.test import yield_empty_pipeline_context
from dagster_aws.s3 import (
    S3IntermediateStorage,
    s3_plus_default_intermediate_storage_defs,
    s3_resource,
)


class UppercaseSerializationStrategy(SerializationStrategy):  # pylint: disable=no-init
    def serialize(self, value, write_file_obj):
        return write_file_obj.write(bytes(value.upper().encode("utf-8")))

    def deserialize(self, read_file_obj):
        return read_file_obj.read().decode("utf-8").lower()


LowercaseString = create_any_type(
    "LowercaseString",
    serialization_strategy=UppercaseSerializationStrategy("uppercase"),
)


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
                intermediate_storage_defs=s3_plus_default_intermediate_storage_defs,
                resource_defs={"s3": s3_resource},
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


def test_s3_intermediate_storage_composite_types_with_custom_serializer_for_inner_type(
    mock_s3_bucket,
):
    run_id = make_new_run_id()

    intermediate_storage = S3IntermediateStorage(run_id=run_id, s3_bucket=mock_s3_bucket.name)
    with yield_empty_pipeline_context(run_id=run_id) as context:
        try:
            intermediate_storage.set_intermediate(
                context,
                resolve_dagster_type(List[LowercaseString]),
                StepOutputHandle("list"),
                ["foo", "bar"],
            )
            assert intermediate_storage.has_intermediate(context, StepOutputHandle("list"))
            assert intermediate_storage.get_intermediate(
                context, resolve_dagster_type(List[Bool]), StepOutputHandle("list")
            ).obj == ["foo", "bar"]

        finally:
            intermediate_storage.rm_intermediate(context, StepOutputHandle("list"))


def test_s3_intermediate_storage_with_custom_serializer(mock_s3_bucket):
    run_id = make_new_run_id()

    intermediate_storage = S3IntermediateStorage(run_id=run_id, s3_bucket=mock_s3_bucket.name)

    with yield_empty_pipeline_context(run_id=run_id) as context:
        try:
            intermediate_storage.set_intermediate(
                context, LowercaseString, StepOutputHandle("foo"), "foo"
            )

            assert (
                intermediate_storage.object_store.s3.get_object(
                    Bucket=intermediate_storage.object_store.bucket,
                    Key=os.path.join(intermediate_storage.root, "intermediates", "foo", "result"),
                )["Body"]
                .read()
                .decode("utf-8")
                == "FOO"
            )

            assert intermediate_storage.has_intermediate(context, StepOutputHandle("foo"))
            assert (
                intermediate_storage.get_intermediate(
                    context, LowercaseString, StepOutputHandle("foo")
                ).obj
                == "foo"
            )
        finally:
            intermediate_storage.rm_intermediate(context, StepOutputHandle("foo"))


def test_s3_intermediate_storage_with_custom_prefix(mock_s3_bucket):
    run_id = make_new_run_id()

    intermediate_storage = S3IntermediateStorage(
        run_id=run_id, s3_bucket=mock_s3_bucket.name, s3_prefix="custom_prefix"
    )
    assert intermediate_storage.root == "/".join(["custom_prefix", "storage", run_id])

    try:
        with yield_empty_pipeline_context(run_id=run_id) as context:

            intermediate_storage.set_intermediate(
                context, RuntimeBool, StepOutputHandle("true"), True
            )

            assert intermediate_storage.has_intermediate(context, StepOutputHandle("true"))
            assert intermediate_storage.uri_for_paths(["true"]).startswith(
                "s3://%s/custom_prefix" % mock_s3_bucket.name
            )

    finally:
        intermediate_storage.rm_intermediate(context, StepOutputHandle("true"))


def test_s3_intermediate_storage(mock_s3_bucket):
    run_id = make_new_run_id()
    run_id_2 = make_new_run_id()

    intermediate_storage = S3IntermediateStorage(run_id=run_id, s3_bucket=mock_s3_bucket.name)
    assert intermediate_storage.root == "/".join(["dagster", "storage", run_id])

    intermediate_storage_2 = S3IntermediateStorage(run_id=run_id_2, s3_bucket=mock_s3_bucket.name)
    assert intermediate_storage_2.root == "/".join(["dagster", "storage", run_id_2])

    try:
        with yield_empty_pipeline_context(run_id=run_id) as context:

            intermediate_storage.set_intermediate(
                context, RuntimeBool, StepOutputHandle("true"), True
            )

            assert intermediate_storage.has_intermediate(context, StepOutputHandle("true"))
            assert (
                intermediate_storage.get_intermediate(
                    context, RuntimeBool, StepOutputHandle("true")
                ).obj
                is True
            )
            assert intermediate_storage.uri_for_paths(["true"]).startswith("s3://")

            intermediate_storage_2.copy_intermediate_from_run(
                context, run_id, StepOutputHandle("true")
            )
            assert intermediate_storage_2.has_intermediate(context, StepOutputHandle("true"))
            assert (
                intermediate_storage_2.get_intermediate(
                    context, RuntimeBool, StepOutputHandle("true")
                ).obj
                is True
            )
    finally:
        intermediate_storage.rm_intermediate(context, StepOutputHandle("true"))
        intermediate_storage_2.rm_intermediate(context, StepOutputHandle("true"))


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


def test_custom_read_write_mode(mock_s3_bucket):
    run_id = make_new_run_id()
    intermediate_storage = S3IntermediateStorage(run_id=run_id, s3_bucket=mock_s3_bucket.name)
    data_frame = [OrderedDict({"foo": "1", "bar": "1"}), OrderedDict({"foo": "2", "bar": "2"})]
    try:
        with yield_empty_pipeline_context(run_id=run_id) as context:
            intermediate_storage.set_intermediate(
                context,
                resolve_dagster_type(LessSimpleDataFrame),
                StepOutputHandle("data_frame"),
                data_frame,
            )

            assert intermediate_storage.has_intermediate(context, StepOutputHandle("data_frame"))
            assert (
                intermediate_storage.get_intermediate(
                    context,
                    resolve_dagster_type(LessSimpleDataFrame),
                    StepOutputHandle("data_frame"),
                ).obj
                == data_frame
            )
            assert intermediate_storage.uri_for_paths(["data_frame"]).startswith("s3://")

    finally:
        intermediate_storage.rm_intermediate(context, StepOutputHandle("data_frame"))
