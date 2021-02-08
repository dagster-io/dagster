import csv
import datetime
import logging
import os
import time
from collections import OrderedDict
from contextlib import contextmanager
from copy import deepcopy

from dagster import (
    Any,
    AssetMaterialization,
    Bool,
    DagsterInstance,
    Enum,
    EnumValue,
    EventMetadataEntry,
    ExpectationResult,
    Field,
    InputDefinition,
    Int,
    ModeDefinition,
    Noneable,
    Nothing,
    Output,
    OutputDefinition,
    Partition,
    PartitionSetDefinition,
    PresetDefinition,
    PythonObjectDagsterType,
    ScheduleDefinition,
    String,
    check,
    composite_solid,
    dagster_type_loader,
    dagster_type_materializer,
    daily_schedule,
    hourly_schedule,
    lambda_solid,
    logger,
    monthly_schedule,
    pipeline,
    repository,
    resource,
    solid,
    usable_as_dagster_type,
    weekly_schedule,
)
from dagster.cli.workspace.load import location_origin_from_python_file
from dagster.core.definitions.decorators.sensor import sensor
from dagster.core.definitions.partition import last_empty_partition
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.definitions.sensor import RunRequest, SkipReason
from dagster.core.log_manager import coerce_valid_log_level
from dagster.core.storage.tags import RESUME_RETRY_TAG
from dagster.core.test_utils import today_at_midnight
from dagster.experimental import DynamicOutput, DynamicOutputDefinition
from dagster.seven import get_system_temp_directory
from dagster.utils import file_relative_path, segfault
from dagster_graphql.test.utils import (
    define_in_process_context,
    define_out_of_process_context,
    infer_pipeline_selector,
    main_repo_location_name,
    main_repo_name,
)


@dagster_type_loader(String)
def df_input_schema(_context, path):
    with open(path, "r") as fd:
        return [OrderedDict(sorted(x.items(), key=lambda x: x[0])) for x in csv.DictReader(fd)]


@dagster_type_materializer(String)
def df_output_schema(_context, path, value):
    with open(path, "w") as fd:
        writer = csv.DictWriter(fd, fieldnames=value[0].keys())
        writer.writeheader()
        writer.writerows(rowdicts=value)

    return AssetMaterialization.file(path)


PoorMansDataFrame = PythonObjectDagsterType(
    python_type=list,
    name="PoorMansDataFrame",
    loader=df_input_schema,
    materializer=df_output_schema,
)


@contextmanager
def define_test_out_of_process_context(instance):
    check.inst_param(instance, "instance", DagsterInstance)
    with define_out_of_process_context(__file__, main_repo_name(), instance) as context:
        yield context


def define_test_in_process_context(instance):
    check.inst_param(instance, "instance", DagsterInstance)
    return define_in_process_context(__file__, main_repo_name(), instance)


def create_main_recon_repo():
    return ReconstructableRepository.for_file(__file__, main_repo_name())


@contextmanager
def get_main_external_repo():
    with location_origin_from_python_file(
        python_file=file_relative_path(__file__, "setup.py"),
        attribute=main_repo_name(),
        working_directory=None,
        location_name=main_repo_location_name(),
    ).create_handle() as handle:
        yield handle.create_location().get_repository(main_repo_name())


@lambda_solid(
    input_defs=[InputDefinition("num", PoorMansDataFrame)],
    output_def=OutputDefinition(PoorMansDataFrame),
)
def sum_solid(num):
    sum_df = deepcopy(num)
    for x in sum_df:
        x["sum"] = int(x["num1"]) + int(x["num2"])
    return sum_df


@lambda_solid(
    input_defs=[InputDefinition("sum_df", PoorMansDataFrame)],
    output_def=OutputDefinition(PoorMansDataFrame),
)
def sum_sq_solid(sum_df):
    sum_sq_df = deepcopy(sum_df)
    for x in sum_sq_df:
        x["sum_sq"] = int(x["sum"]) ** 2
    return sum_sq_df


@solid(
    input_defs=[InputDefinition("sum_df", PoorMansDataFrame)],
    output_defs=[OutputDefinition(PoorMansDataFrame)],
)
def df_expectations_solid(_context, sum_df):
    yield ExpectationResult(label="some_expectation", success=True)
    yield ExpectationResult(label="other_expectation", success=True)
    yield Output(sum_df)


def csv_hello_world_solids_config():
    return {
        "solids": {
            "sum_solid": {"inputs": {"num": file_relative_path(__file__, "../data/num.csv")}}
        }
    }


def csv_hello_world_solids_config_fs_storage():
    return {
        "solids": {
            "sum_solid": {"inputs": {"num": file_relative_path(__file__, "../data/num.csv")}}
        },
        "intermediate_storage": {"filesystem": {}},
    }


@solid(config_schema={"file": Field(String)})
def loop(context):
    with open(context.solid_config["file"], "w") as ff:
        ff.write("yup")

    while True:
        time.sleep(0.1)


@pipeline
def infinite_loop_pipeline():
    loop()


@solid
def noop_solid(_):
    pass


@pipeline
def noop_pipeline():
    noop_solid()


@solid
def solid_asset_a(_):
    yield AssetMaterialization(asset_key="a")
    yield Output(1)


@solid
def solid_asset_b(_, num):
    yield AssetMaterialization(asset_key="b")
    time.sleep(0.1)
    yield AssetMaterialization(asset_key="c")
    yield Output(num)


@solid
def solid_partitioned_asset(_):
    yield AssetMaterialization(asset_key="a", partition="partition_1")
    yield Output(1)


@pipeline
def single_asset_pipeline():
    solid_asset_a()


@pipeline
def multi_asset_pipeline():
    solid_asset_b(solid_asset_a())


@pipeline
def partitioned_asset_pipeline():
    solid_partitioned_asset()


@pipeline
def pipeline_with_expectations():
    @solid(output_defs=[])
    def emit_successful_expectation(_context):
        yield ExpectationResult(
            success=True,
            label="always_true",
            description="Successful",
            metadata_entries=[
                EventMetadataEntry.json(label="data", data={"reason": "Just because."})
            ],
        )

    @solid(output_defs=[])
    def emit_failed_expectation(_context):
        yield ExpectationResult(
            success=False,
            label="always_false",
            description="Failure",
            metadata_entries=[
                EventMetadataEntry.json(label="data", data={"reason": "Relentless pessimism."})
            ],
        )

    @solid(output_defs=[])
    def emit_successful_expectation_no_metadata(_context):
        yield ExpectationResult(success=True, label="no_metadata", description="Successful")

    emit_successful_expectation()
    emit_failed_expectation()
    emit_successful_expectation_no_metadata()


@pipeline
def more_complicated_config():
    @solid(
        config_schema={
            "field_one": Field(String),
            "field_two": Field(String, is_required=False),
            "field_three": Field(String, is_required=False, default_value="some_value"),
        }
    )
    def a_solid_with_three_field_config(_context):
        return None

    noop_solid()
    a_solid_with_three_field_config()


@pipeline
def more_complicated_nested_config():
    @solid(
        name="a_solid_with_multilayered_config",
        input_defs=[],
        output_defs=[],
        config_schema={
            "field_any": Any,
            "field_one": String,
            "field_two": Field(String, is_required=False),
            "field_three": Field(String, is_required=False, default_value="some_value"),
            "nested_field": {
                "field_four_str": String,
                "field_five_int": Int,
                "field_six_nullable_int_list": Field([Noneable(int)], is_required=False),
            },
        },
    )
    def a_solid_with_multilayered_config(_):
        return None

    a_solid_with_multilayered_config()


@pipeline(
    preset_defs=[
        PresetDefinition.from_files(
            name="prod",
            config_files=[
                file_relative_path(__file__, "../environments/csv_hello_world_prod.yaml")
            ],
        ),
        PresetDefinition.from_files(
            name="test",
            config_files=[
                file_relative_path(__file__, "../environments/csv_hello_world_test.yaml")
            ],
        ),
        PresetDefinition(
            name="test_inline",
            run_config={
                "solids": {
                    "sum_solid": {
                        "inputs": {"num": file_relative_path(__file__, "../data/num.csv")}
                    }
                }
            },
        ),
    ]
)
def csv_hello_world():
    sum_sq_solid(sum_df=sum_solid())


@pipeline
def csv_hello_world_with_expectations():
    ss = sum_solid()
    sum_sq_solid(sum_df=ss)
    df_expectations_solid(sum_df=ss)


@pipeline
def csv_hello_world_two():
    sum_solid()


@solid
def solid_that_gets_tags(context):
    return context.pipeline_run.tags


@pipeline(tags={"tag_key": "tag_value"})
def hello_world_with_tags():
    solid_that_gets_tags()


@solid(name="solid_with_list", input_defs=[], output_defs=[], config_schema=[int])
def solid_def(_):
    return None


@pipeline
def pipeline_with_list():
    solid_def()


@pipeline
def csv_hello_world_df_input():
    sum_sq_solid(sum_solid())


@pipeline
def no_config_pipeline():
    @lambda_solid
    def return_hello():
        return "Hello"

    return_hello()


@pipeline
def no_config_chain_pipeline():
    @lambda_solid
    def return_foo():
        return "foo"

    @lambda_solid
    def return_hello_world(_):
        return "Hello World"

    return_hello_world(return_foo())


@pipeline
def scalar_output_pipeline():
    @lambda_solid(output_def=OutputDefinition(String))
    def return_str():
        return "foo"

    @lambda_solid(output_def=OutputDefinition(Int))
    def return_int():
        return 34234

    @lambda_solid(output_def=OutputDefinition(Bool))
    def return_bool():
        return True

    @lambda_solid(output_def=OutputDefinition(Any))
    def return_any():
        return "dkjfkdjfe"

    return_str()
    return_int()
    return_bool()
    return_any()


@pipeline
def pipeline_with_enum_config():
    @solid(
        config_schema=Enum(
            "TestEnum",
            [
                EnumValue(config_value="ENUM_VALUE_ONE", description="An enum value."),
                EnumValue(config_value="ENUM_VALUE_TWO", description="An enum value."),
                EnumValue(config_value="ENUM_VALUE_THREE", description="An enum value."),
            ],
        )
    )
    def takes_an_enum(_context):
        pass

    takes_an_enum()


@pipeline
def naughty_programmer_pipeline():
    @lambda_solid
    def throw_a_thing():
        raise Exception("bad programmer, bad")

    throw_a_thing()


@pipeline
def pipeline_with_invalid_definition_error():
    @usable_as_dagster_type(name="InputTypeWithoutHydration")
    class InputTypeWithoutHydration(int):
        pass

    @solid(output_defs=[OutputDefinition(InputTypeWithoutHydration)])
    def one(_):
        return 1

    @solid(
        input_defs=[InputDefinition("some_input", InputTypeWithoutHydration)],
        output_defs=[OutputDefinition(Int)],
    )
    def fail_subset(_, some_input):
        return some_input

    fail_subset(one())


@resource(config_schema=Field(Int))
def adder_resource(init_context):
    return lambda x: x + init_context.resource_config


@resource(config_schema=Field(Int))
def multer_resource(init_context):
    return lambda x: x * init_context.resource_config


@resource(config_schema={"num_one": Field(Int), "num_two": Field(Int)})
def double_adder_resource(init_context):
    return (
        lambda x: x
        + init_context.resource_config["num_one"]
        + init_context.resource_config["num_two"]
    )


@pipeline(
    mode_defs=[
        ModeDefinition(
            name="add_mode",
            resource_defs={"op": adder_resource},
            description="Mode that adds things",
        ),
        ModeDefinition(
            name="mult_mode",
            resource_defs={"op": multer_resource},
            description="Mode that multiplies things",
        ),
        ModeDefinition(
            name="double_adder",
            resource_defs={"op": double_adder_resource},
            description="Mode that adds two numbers to thing",
        ),
    ],
    preset_defs=[PresetDefinition.from_files("add", mode="add_mode")],
)
def multi_mode_with_resources():
    @solid(required_resource_keys={"op"})
    def apply_to_three(context):
        return context.resources.op(3)

    apply_to_three()


@resource(config_schema=Field(Int, is_required=False))
def req_resource(_):
    return 1


@pipeline(mode_defs=[ModeDefinition(resource_defs={"R1": req_resource})])
def required_resource_pipeline():
    @solid(required_resource_keys={"R1"})
    def solid_with_required_resource(_):
        return 1

    solid_with_required_resource()


@logger(config_schema=Field(str))
def foo_logger(init_context):
    logger_ = logging.Logger("foo")
    logger_.setLevel(coerce_valid_log_level(init_context.logger_config))
    return logger_


@logger({"log_level": Field(str), "prefix": Field(str)})
def bar_logger(init_context):
    class BarLogger(logging.Logger):
        def __init__(self, name, prefix, *args, **kwargs):
            self.prefix = prefix
            super(BarLogger, self).__init__(name, *args, **kwargs)

        def log(self, lvl, msg, *args, **kwargs):  # pylint: disable=arguments-differ
            msg = self.prefix + msg
            super(BarLogger, self).log(lvl, msg, *args, **kwargs)

    logger_ = BarLogger("bar", init_context.logger_config["prefix"])
    logger_.setLevel(coerce_valid_log_level(init_context.logger_config["log_level"]))


@pipeline(
    mode_defs=[
        ModeDefinition(
            name="foo_mode", logger_defs={"foo": foo_logger}, description="Mode with foo logger"
        ),
        ModeDefinition(
            name="bar_mode", logger_defs={"bar": bar_logger}, description="Mode with bar logger"
        ),
        ModeDefinition(
            name="foobar_mode",
            logger_defs={"foo": foo_logger, "bar": bar_logger},
            description="Mode with multiple loggers",
        ),
    ]
)
def multi_mode_with_loggers():
    @solid
    def return_six(context):
        context.log.critical("OMG!")
        return 6

    return_six()


@pipeline
def composites_pipeline():
    @lambda_solid(input_defs=[InputDefinition("num", Int)], output_def=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    @lambda_solid(input_defs=[InputDefinition("num")])
    def div_two(num):
        return num / 2

    @composite_solid(input_defs=[InputDefinition("num", Int)], output_defs=[OutputDefinition(Int)])
    def add_two(num):
        return add_one.alias("adder_2")(add_one.alias("adder_1")(num))

    @composite_solid(input_defs=[InputDefinition("num", Int)], output_defs=[OutputDefinition(Int)])
    def add_four(num):
        return add_two.alias("adder_2")(add_two.alias("adder_1")(num))

    @composite_solid
    def div_four(num):
        return div_two.alias("div_2")(div_two.alias("div_1")(num))

    div_four(add_four())


@pipeline
def materialization_pipeline():
    @solid
    def materialize(_):
        yield AssetMaterialization(
            asset_key="all_types",
            description="a materialization with all metadata types",
            metadata_entries=[
                EventMetadataEntry.text("text is cool", "text"),
                EventMetadataEntry.url("https://bigty.pe/neato", "url"),
                EventMetadataEntry.fspath("/tmp/awesome", "path"),
                EventMetadataEntry.json({"is_dope": True}, "json"),
                EventMetadataEntry.python_artifact(EventMetadataEntry, "python class"),
                EventMetadataEntry.python_artifact(file_relative_path, "python function"),
                EventMetadataEntry.float(1.2, "float"),
                EventMetadataEntry.int(1, "int"),
            ],
        )
        yield Output(None)

    materialize()


@pipeline
def spew_pipeline():
    @solid
    def spew(_):
        print("HELLO WORLD")  # pylint: disable=print-call

    spew()


def retry_config(count):
    return {
        "resources": {"retry_count": {"config": {"count": count}}},
        "intermediate_storage": {"filesystem": {}},
    }


@resource(config_schema={"count": Field(Int, is_required=False, default_value=0)})
def retry_config_resource(context):
    return context.resource_config["count"]


@pipeline(mode_defs=[ModeDefinition(resource_defs={"retry_count": retry_config_resource})])
def eventually_successful():
    @solid(output_defs=[OutputDefinition(Int)])
    def spawn(_):
        return 0

    @solid(
        input_defs=[InputDefinition("depth", Int)],
        output_defs=[OutputDefinition(Int)],
        required_resource_keys={"retry_count"},
    )
    def fail(context, depth):
        if context.resources.retry_count <= depth:
            raise Exception("fail")

        return depth + 1

    @solid
    def reset(_, depth):
        return depth

    reset(fail(fail(fail(spawn()))))


@pipeline
def hard_failer():
    @solid(
        config_schema={"fail": Field(Bool, is_required=False, default_value=False)},
        output_defs=[OutputDefinition(Int)],
    )
    def hard_fail_or_0(context):
        if context.solid_config["fail"]:
            segfault()
        return 0

    @solid(
        input_defs=[InputDefinition("n", Int)],
    )
    def increment(_, n):
        return n + 1

    increment(hard_fail_or_0())


@resource
def resource_a(_):
    return "A"


@resource
def resource_b(_):
    return "B"


@solid(required_resource_keys={"a"})
def start(context):
    assert context.resources.a == "A"
    return 1


@solid(required_resource_keys={"b"})
def will_fail(context, num):  # pylint: disable=unused-argument
    assert context.resources.b == "B"
    raise Exception("fail")


@pipeline(mode_defs=[ModeDefinition(resource_defs={"a": resource_a, "b": resource_b})])
def retry_resource_pipeline():
    will_fail(start())


@solid(
    config_schema={"fail": bool},
    input_defs=[InputDefinition("inp", str)],
    output_defs=[
        OutputDefinition(str, "start_fail", is_required=False),
        OutputDefinition(str, "start_skip", is_required=False),
    ],
)
def can_fail(context, inp):  # pylint: disable=unused-argument
    if context.solid_config["fail"]:
        raise Exception("blah")

    yield Output("okay perfect", "start_fail")


@solid(
    output_defs=[
        OutputDefinition(str, "success", is_required=False),
        OutputDefinition(str, "skip", is_required=False),
    ],
)
def multi(_):
    yield Output("okay perfect", "success")


@solid
def passthrough(_, value):
    return value


@solid(input_defs=[InputDefinition("start", Nothing)], output_defs=[])
def no_output(_):
    yield ExpectationResult(True)


@pipeline
def retry_multi_output_pipeline():
    multi_success, multi_skip = multi()
    fail, skip = can_fail(multi_success)
    no_output.alias("child_multi_skip")(multi_skip)
    no_output.alias("child_skip")(skip)
    no_output.alias("grandchild_fail")(passthrough.alias("child_fail")(fail))


@pipeline(tags={"foo": "bar"})
def tagged_pipeline():
    @lambda_solid
    def simple_solid():
        return "Hello"

    simple_solid()


@pipeline
def retry_multi_input_early_terminate_pipeline():
    @lambda_solid(output_def=OutputDefinition(Int))
    def return_one():
        return 1

    @solid(
        config_schema={"wait_to_terminate": bool},
        input_defs=[InputDefinition("one", Int)],
        output_defs=[OutputDefinition(Int)],
    )
    def get_input_one(context, one):
        if context.solid_config["wait_to_terminate"]:
            while True:
                time.sleep(0.1)
        return one

    @solid(
        config_schema={"wait_to_terminate": bool},
        input_defs=[InputDefinition("one", Int)],
        output_defs=[OutputDefinition(Int)],
    )
    def get_input_two(context, one):
        if context.solid_config["wait_to_terminate"]:
            while True:
                time.sleep(0.1)
        return one

    @lambda_solid(
        input_defs=[InputDefinition("input_one", Int), InputDefinition("input_two", Int)],
        output_def=OutputDefinition(Int),
    )
    def sum_inputs(input_one, input_two):
        return input_one + input_two

    step_one = return_one()
    sum_inputs(input_one=get_input_one(step_one), input_two=get_input_two(step_one))


@pipeline
def dynamic_pipeline():
    @solid
    def multiply_by_two(context, y):
        context.log.info("multiply_by_two is returning " + str(y * 2))
        return y * 2

    @solid
    def multiply_inputs(context, y, ten, should_fail):
        current_run = context.instance.get_run_by_id(context.run_id)
        if should_fail:
            if y == 2 and current_run.parent_run_id is None:
                raise Exception()
        context.log.info("multiply_inputs is returning " + str(y * ten))
        return y * ten

    @solid
    def emit_ten(_):
        return 10

    @solid(output_defs=[DynamicOutputDefinition()])
    def emit(_):
        for i in range(3):
            yield DynamicOutput(value=i, mapping_key=str(i))

    # pylint: disable=no-member
    emit().map(lambda n: multiply_by_two(multiply_inputs(n, emit_ten())))


def get_retry_multi_execution_params(graphql_context, should_fail, retry_id=None):
    selector = infer_pipeline_selector(graphql_context, "retry_multi_output_pipeline")
    return {
        "mode": "default",
        "selector": selector,
        "runConfigData": {
            "intermediate_storage": {"filesystem": {}},
            "solids": {"can_fail": {"config": {"fail": should_fail}}},
        },
        "executionMetadata": {
            "rootRunId": retry_id,
            "parentRunId": retry_id,
            "tags": [{"key": RESUME_RETRY_TAG, "value": "true"}],
        },
    }


def define_schedules():
    integer_partition_set = PartitionSetDefinition(
        name="scheduled_integer_partitions",
        pipeline_name="no_config_pipeline",
        partition_fn=lambda: [Partition(x) for x in range(1, 10)],
        run_config_fn_for_partition=lambda _partition: {"intermediate_storage": {"filesystem": {}}},
        tags_fn_for_partition=lambda _partition: {"test": "1234"},
    )

    no_config_pipeline_hourly_schedule = ScheduleDefinition(
        name="no_config_pipeline_hourly_schedule",
        cron_schedule="0 0 * * *",
        pipeline_name="no_config_pipeline",
        run_config={"intermediate_storage": {"filesystem": {}}},
    )

    no_config_pipeline_hourly_schedule_with_config_fn = ScheduleDefinition(
        name="no_config_pipeline_hourly_schedule_with_config_fn",
        cron_schedule="0 0 * * *",
        pipeline_name="no_config_pipeline",
        run_config_fn=lambda _context: {"intermediate_storage": {"filesystem": {}}},
    )

    no_config_should_execute = ScheduleDefinition(
        name="no_config_should_execute",
        cron_schedule="0 0 * * *",
        pipeline_name="no_config_pipeline",
        run_config={"intermediate_storage": {"filesystem": {}}},
        should_execute=lambda _context: False,
    )

    dynamic_config = ScheduleDefinition(
        name="dynamic_config",
        cron_schedule="0 0 * * *",
        pipeline_name="no_config_pipeline",
        run_config_fn=lambda _context: {"intermediate_storage": {"filesystem": {}}},
    )

    partition_based = integer_partition_set.create_schedule_definition(
        schedule_name="partition_based",
        cron_schedule="0 0 * * *",
        partition_selector=last_empty_partition,
    )

    @daily_schedule(
        pipeline_name="no_config_pipeline",
        start_date=today_at_midnight().subtract(days=1),
        execution_time=(datetime.datetime.now() + datetime.timedelta(hours=2)).time(),
    )
    def partition_based_decorator(_date):
        return {"intermediate_storage": {"filesystem": {}}}

    @daily_schedule(
        pipeline_name="multi_mode_with_loggers",
        start_date=today_at_midnight().subtract(days=1),
        execution_time=(datetime.datetime.now() + datetime.timedelta(hours=2)).time(),
        mode="foo_mode",
    )
    def partition_based_multi_mode_decorator(_date):
        return {"intermediate_storage": {"filesystem": {}}}

    @hourly_schedule(
        pipeline_name="no_config_chain_pipeline",
        start_date=today_at_midnight().subtract(days=1),
        execution_time=(datetime.datetime.now() + datetime.timedelta(hours=2)).time(),
        solid_selection=["return_foo"],
    )
    def solid_selection_hourly_decorator(_date):
        return {"intermediate_storage": {"filesystem": {}}}

    @daily_schedule(
        pipeline_name="no_config_chain_pipeline",
        start_date=today_at_midnight().subtract(days=2),
        execution_time=(datetime.datetime.now() + datetime.timedelta(hours=3)).time(),
        solid_selection=["return_foo"],
    )
    def solid_selection_daily_decorator(_date):
        return {"intermediate_storage": {"filesystem": {}}}

    @monthly_schedule(
        pipeline_name="no_config_chain_pipeline",
        start_date=(today_at_midnight().subtract(days=100)).replace(day=1),
        execution_time=(datetime.datetime.now() + datetime.timedelta(hours=4)).time(),
        solid_selection=["return_foo"],
    )
    def solid_selection_monthly_decorator(_date):
        return {"intermediate_storage": {"filesystem": {}}}

    @weekly_schedule(
        pipeline_name="no_config_chain_pipeline",
        start_date=today_at_midnight().subtract(days=50),
        execution_time=(datetime.datetime.now() + datetime.timedelta(hours=5)).time(),
        solid_selection=["return_foo"],
    )
    def solid_selection_weekly_decorator(_date):
        return {"intermediate_storage": {"filesystem": {}}}

    # Schedules for testing the user error boundary
    @daily_schedule(
        pipeline_name="no_config_pipeline",
        start_date=today_at_midnight().subtract(days=1),
        should_execute=lambda _: asdf,  # pylint: disable=undefined-variable
    )
    def should_execute_error_schedule(_date):
        return {"intermediate_storage": {"filesystem": {}}}

    @daily_schedule(
        pipeline_name="no_config_pipeline",
        start_date=today_at_midnight().subtract(days=1),
        tags_fn_for_date=lambda _: asdf,  # pylint: disable=undefined-variable
    )
    def tags_error_schedule(_date):
        return {"intermediate_storage": {"filesystem": {}}}

    @daily_schedule(
        pipeline_name="no_config_pipeline",
        start_date=today_at_midnight().subtract(days=1),
    )
    def run_config_error_schedule(_date):
        return asdf  # pylint: disable=undefined-variable

    @daily_schedule(
        pipeline_name="no_config_pipeline",
        start_date=today_at_midnight("US/Central") - datetime.timedelta(days=1),
        execution_timezone="US/Central",
    )
    def timezone_schedule(_date):
        return {"intermediate_storage": {"filesystem": {}}}

    tagged_pipeline_schedule = ScheduleDefinition(
        name="tagged_pipeline_schedule",
        cron_schedule="0 0 * * *",
        pipeline_name="tagged_pipeline",
        run_config={"intermediate_storage": {"filesystem": {}}},
    )

    tagged_pipeline_override_schedule = ScheduleDefinition(
        name="tagged_pipeline_override_schedule",
        cron_schedule="0 0 * * *",
        pipeline_name="tagged_pipeline",
        run_config={"intermediate_storage": {"filesystem": {}}},
        tags={"foo": "notbar"},
    )

    invalid_config_schedule = ScheduleDefinition(
        name="invalid_config_schedule",
        cron_schedule="0 0 * * *",
        pipeline_name="pipeline_with_enum_config",
        run_config={"solids": {"takes_an_enum": {"config": "invalid"}}},
    )

    return [
        run_config_error_schedule,
        no_config_pipeline_hourly_schedule,
        no_config_pipeline_hourly_schedule_with_config_fn,
        no_config_should_execute,
        dynamic_config,
        partition_based,
        partition_based_decorator,
        partition_based_multi_mode_decorator,
        solid_selection_hourly_decorator,
        solid_selection_daily_decorator,
        solid_selection_monthly_decorator,
        solid_selection_weekly_decorator,
        should_execute_error_schedule,
        tagged_pipeline_schedule,
        tagged_pipeline_override_schedule,
        tags_error_schedule,
        timezone_schedule,
        invalid_config_schedule,
    ]


def define_partitions():
    integer_set = PartitionSetDefinition(
        name="integer_partition",
        pipeline_name="no_config_pipeline",
        solid_selection=["return_hello"],
        mode="default",
        partition_fn=lambda: [Partition(i) for i in range(10)],
        run_config_fn_for_partition=lambda _: {"intermediate_storage": {"filesystem": {}}},
        tags_fn_for_partition=lambda partition: {"foo": partition.name},
    )

    enum_set = PartitionSetDefinition(
        name="enum_partition",
        pipeline_name="noop_pipeline",
        partition_fn=lambda: ["one", "two", "three"],
        run_config_fn_for_partition=lambda _: {"intermediate_storage": {"filesystem": {}}},
    )

    chained_partition_set = PartitionSetDefinition(
        name="chained_integer_partition",
        pipeline_name="chained_failure_pipeline",
        mode="default",
        partition_fn=lambda: [Partition(i) for i in range(10)],
        run_config_fn_for_partition=lambda _: {"intermediate_storage": {"filesystem": {}}},
    )

    return [integer_set, enum_set, chained_partition_set]


def define_sensors():
    @sensor(pipeline_name="no_config_pipeline", mode="default")
    def always_no_config_sensor(_):
        return RunRequest(
            run_key=None,
            run_config={"intermediate_storage": {"filesystem": {}}},
            tags={"test": "1234"},
        )

    @sensor(pipeline_name="no_config_pipeline", mode="default")
    def once_no_config_sensor(_):
        return RunRequest(
            run_key="once",
            run_config={"intermediate_storage": {"filesystem": {}}},
            tags={"test": "1234"},
        )

    @sensor(pipeline_name="no_config_pipeline", mode="default")
    def never_no_config_sensor(_):
        return SkipReason("never")

    @sensor(pipeline_name="no_config_pipeline", mode="default")
    def multi_no_config_sensor(_):
        yield RunRequest(run_key="A")
        yield RunRequest(run_key="B")

    @sensor(pipeline_name="no_config_pipeline", mode="default", minimum_interval_seconds=60)
    def custom_interval_sensor(_):
        return RunRequest(
            run_key=None,
            run_config={"intermediate_storage": {"filesystem": {}}},
            tags={"test": "1234"},
        )

    return [
        always_no_config_sensor,
        once_no_config_sensor,
        never_no_config_sensor,
        multi_no_config_sensor,
        custom_interval_sensor,
    ]


@pipeline
def chained_failure_pipeline():
    @lambda_solid
    def always_succeed():
        return "hello"

    @lambda_solid
    def conditionally_fail(_):
        if os.path.isfile(
            os.path.join(get_system_temp_directory(), "chained_failure_pipeline_conditionally_fail")
        ):
            raise Exception("blah")

        return "hello"

    @lambda_solid
    def after_failure(_):
        return "world"

    after_failure(conditionally_fail(always_succeed()))


@repository
def empty_repo():
    return []


@repository
def test_repo():
    return (
        [
            composites_pipeline,
            csv_hello_world_df_input,
            csv_hello_world_two,
            csv_hello_world_with_expectations,
            csv_hello_world,
            eventually_successful,
            hard_failer,
            hello_world_with_tags,
            infinite_loop_pipeline,
            materialization_pipeline,
            more_complicated_config,
            more_complicated_nested_config,
            multi_asset_pipeline,
            multi_mode_with_loggers,
            multi_mode_with_resources,
            naughty_programmer_pipeline,
            no_config_chain_pipeline,
            no_config_pipeline,
            noop_pipeline,
            partitioned_asset_pipeline,
            pipeline_with_enum_config,
            pipeline_with_expectations,
            pipeline_with_invalid_definition_error,
            pipeline_with_list,
            required_resource_pipeline,
            retry_multi_input_early_terminate_pipeline,
            retry_multi_output_pipeline,
            retry_resource_pipeline,
            scalar_output_pipeline,
            single_asset_pipeline,
            spew_pipeline,
            tagged_pipeline,
            chained_failure_pipeline,
            dynamic_pipeline,
        ]
        + define_schedules()
        + define_sensors()
        + define_partitions()
    )
