import csv
import os
from collections import OrderedDict

import pytest
from dagster import (
    Bool,
    InputDefinition,
    Int,
    List,
    ModeDefinition,
    OutputDefinition,
    PipelineRun,
    SerializationStrategy,
    execute_pipeline,
    lambda_solid,
    pipeline,
    usable_as_dagster_type,
)
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.events import DagsterEventType
from dagster.core.execution.api import create_execution_plan, scoped_pipeline_context
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.instance import DagsterInstance
from dagster.core.types.dagster_type import Bool as RuntimeBool
from dagster.core.types.dagster_type import create_any_type, resolve_dagster_type
from dagster.core.utils import make_new_run_id
from dagster.utils.test import yield_empty_pipeline_context
from dagster_azure.adls2 import (
    ADLS2IntermediateStorage,
    adls2_plus_default_intermediate_storage_defs,
    adls2_resource,
    create_adls2_client,
)
from dagster_azure.blob import create_blob_client


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
                intermediate_storage_defs=adls2_plus_default_intermediate_storage_defs,
                resource_defs={"adls2": adls2_resource},
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


def get_azure_credential():
    try:
        return {"key": os.environ["AZURE_STORAGE_ACCOUNT_KEY"]}
    except KeyError:
        raise Exception("AZURE_STORAGE_ACCOUNT_KEY must be set for intermediate store tests")


def get_adls2_client(storage_account):
    creds = get_azure_credential()["key"]
    return create_adls2_client(storage_account, creds)


def get_blob_client(storage_account):
    creds = get_azure_credential()["key"]
    return create_blob_client(storage_account, creds)


@nettest
def test_adls2_intermediate_storage_composite_types_with_custom_serializer_for_inner_type(
    storage_account, file_system
):
    run_id = make_new_run_id()

    intermediate_storage = ADLS2IntermediateStorage(
        adls2_client=get_adls2_client(storage_account),
        blob_client=get_blob_client(storage_account),
        run_id=run_id,
        file_system=file_system,
    )

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
def test_adls2_intermediate_storage_with_custom_serializer(storage_account, file_system):
    run_id = make_new_run_id()

    intermediate_storage = ADLS2IntermediateStorage(
        adls2_client=get_adls2_client(storage_account),
        blob_client=get_blob_client(storage_account),
        run_id=run_id,
        file_system=file_system,
    )

    with yield_empty_pipeline_context(run_id=run_id) as context:
        try:
            intermediate_storage.set_intermediate(
                context, LowercaseString, StepOutputHandle("foo"), "foo"
            )

            assert (
                intermediate_storage.object_store.file_system_client.get_file_client(
                    os.path.join(*[intermediate_storage.root, "intermediates", "foo", "result"]),
                )
                .download_file()
                .readall()
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


@nettest
def test_adls2_pipeline_with_custom_prefix(storage_account, file_system):
    adls2_prefix = "custom_prefix"

    pipe = define_inty_pipeline(should_throw=False)
    run_config = {
        "resources": {
            "adls2": {
                "config": {"storage_account": storage_account, "credential": get_azure_credential()}
            }
        },
        "intermediate_storage": {
            "adls2": {"config": {"adls2_file_system": file_system, "adls2_prefix": adls2_prefix}}
        },
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
        resource = context.scoped_resources_builder.build(required_resource_keys={"adls2"}).adls2
        intermediate_storage = ADLS2IntermediateStorage(
            run_id=result.run_id,
            file_system=file_system,
            prefix=adls2_prefix,
            adls2_client=resource.adls2_client,
            blob_client=resource.blob_client,
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
def test_adls2_intermediate_storage_with_custom_prefix(storage_account, file_system):
    run_id = make_new_run_id()

    intermediate_storage = ADLS2IntermediateStorage(
        adls2_client=get_adls2_client(storage_account),
        blob_client=get_blob_client(storage_account),
        run_id=run_id,
        file_system=file_system,
        prefix="custom_prefix",
    )
    assert intermediate_storage.root == "/".join(["custom_prefix", "storage", run_id])

    try:
        with yield_empty_pipeline_context(run_id=run_id) as context:

            intermediate_storage.set_intermediate(
                context, RuntimeBool, StepOutputHandle("true"), True
            )

            assert intermediate_storage.has_intermediate(context, StepOutputHandle("true"))
            assert intermediate_storage.uri_for_paths(["true"]).startswith(
                "abfss://{fs}@{account}.dfs.core.windows.net/custom_prefix".format(
                    account=storage_account, fs=file_system
                )
            )

    finally:
        intermediate_storage.rm_intermediate(context, StepOutputHandle("true"))


@nettest
def test_adls2_intermediate_storage(storage_account, file_system):
    run_id = make_new_run_id()
    run_id_2 = make_new_run_id()

    intermediate_storage = ADLS2IntermediateStorage(
        adls2_client=get_adls2_client(storage_account),
        blob_client=get_blob_client(storage_account),
        run_id=run_id,
        file_system=file_system,
    )
    assert intermediate_storage.root == "/".join(["dagster", "storage", run_id])

    intermediate_storage_2 = ADLS2IntermediateStorage(
        adls2_client=get_adls2_client(storage_account),
        blob_client=get_blob_client(storage_account),
        run_id=run_id_2,
        file_system=file_system,
    )
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
            assert intermediate_storage.uri_for_paths(["true"]).startswith("abfss://")

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


def test_custom_read_write_mode(storage_account, file_system):
    run_id = make_new_run_id()
    data_frame = [OrderedDict({"foo": "1", "bar": "1"}), OrderedDict({"foo": "2", "bar": "2"})]
    try:
        with yield_empty_pipeline_context(run_id=run_id) as context:
            intermediate_storage = ADLS2IntermediateStorage(
                adls2_client=get_adls2_client(storage_account),
                blob_client=get_blob_client(storage_account),
                run_id=run_id,
                file_system=file_system,
            )
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
            assert intermediate_storage.uri_for_paths(["data_frame"]).startswith("abfss://")

    finally:
        intermediate_storage.rm_intermediate(context, StepOutputHandle("data_frame"))
