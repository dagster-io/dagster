# pylint: disable=no-value-for-parameter

import datetime

from dagster import (
    Any,
    Array,
    Enum,
    EnumValue,
    Field,
    IntSource,
    ModeDefinition,
    Noneable,
    Permissive,
    PresetDefinition,
    Selector,
    Shape,
    String,
    StringSource,
    daily_schedule,
    hourly_schedule,
    pipeline,
    repository,
    resource,
    schedule,
    solid,
)


@hourly_schedule(
    pipeline_name="metrics_pipeline",
    start_date=datetime.datetime(2019, 12, 1),
    execution_time=datetime.time(),
)
def daily_ingest_schedule(date):
    date_path = date.strftime("%Y/%m/%d/%H")
    return {
        "solids": {
            "save_metrics": {
                "inputs": {"data_path": {"value": "s3://bucket-name/data/{}".format(date_path)}}
            }
        },
    }


@daily_schedule(
    pipeline_name="rollup_pipeline",
    start_date=datetime.datetime(2019, 12, 1),
    execution_time=datetime.time(hour=3, minute=0),
)
def daily_rollup_schedule(date):
    date_path = date.strftime("%Y/%m/%d")
    return {
        "solids": {
            "rollup_data": {
                "inputs": {"data_path": {"value": "s3://bucket-name/data/{}".format(date_path)}}
            }
        },
    }


@schedule(
    name="test_schedule",
    cron_schedule="* * * * *",
    pipeline_name="metrics_pipeline",
)
def test_schedule(_):
    return {
        "solids": {
            "save_metrics": {
                "inputs": {"data_path": {"value": "s3://bucket-name/data/{}".format("date")}}
            }
        },
    }


def define_schedules():
    return [daily_ingest_schedule, daily_rollup_schedule, test_schedule]


@solid(config_schema={"abc": str, "bcd": str})
def save_metrics(context, data_path):
    context.log.info("Saving metrics to path {data_path}".format(data_path=data_path))


@pipeline(
    preset_defs=[
        PresetDefinition(
            name="test",
            run_config={
                "solids": {
                    "save_metrics": {
                        "inputs": {"data_path": {"value": "s3://bucket-name/test_data"}}
                    }
                }
            },
        ),
    ],
)
def metrics_pipeline():
    save_metrics()


@solid
def rollup_data(context, data_path):
    context.log.info("Rolling up data from path {data_path}".format(data_path=data_path))


@pipeline(
    preset_defs=[
        PresetDefinition(
            name="test",
            run_config={
                "solids": {
                    "rollup_data": {
                        "inputs": {"data_path": {"value": "s3://bucket-name/test_data"}}
                    }
                }
            },
        ),
    ],
)
def rollup_pipeline():
    rollup_data()


@resource(
    config_schema={
        "string": str,
        "string_source": StringSource,
        "int_source": IntSource,
        "number": int,
        "boolean": bool,
        "not_required": Field(bool, is_required=False),
        "default_value": Field(str, default_value="default_value"),
        "enum": Enum("CowboyType", [EnumValue("good"), EnumValue("bad"), EnumValue("ugly")]),
        "array": Array(String),
        "selector": Selector(
            {
                "a": str,
                "b": str,
                "c": str,
            }
        ),
        "noneable_array": Noneable(Array(String)),
        "noneable_string": Noneable(String),
    }
)
def my_resource(_):
    return None


@solid(
    required_resource_keys={"my_resource"},
    config_schema={
        "any": Any,
        "string": str,
        "string_source": StringSource,
        "int_source": IntSource,
        "number": int,
        "boolean": bool,
        "not_required": Field(bool, is_required=False),
        "default_value": Field(str, default_value="default_value"),
        "enum": Enum("CowboyType", [EnumValue("good"), EnumValue("bad"), EnumValue("ugly")]),
        "array": Array(String),
        "selector": Selector(
            {
                "a": str,
                "b": str,
                "c": str,
            }
        ),
        "noneable_array": Noneable(Array(String)),
        "noneable_string": Noneable(String),
        "complex_shape": Shape(
            fields={"inner_shape_array": Array(str), "inner_shape_string": String}
        ),
        "permissive_complex_shape": Permissive(
            fields={"inner_shape_array": Array(str), "inner_shape_string": String}
        ),
        "noneable_complex_shape": Noneable(
            Shape(
                fields={
                    "inner_noneable_shape_array": Array(str),
                    "inner_noneable_shape_string": String,
                }
            )
        ),
    },
)
def test_solid(_):
    return 1


@pipeline(mode_defs=[ModeDefinition(resource_defs={"my_resource": my_resource})])
def test_pipeline():
    test_solid()


@repository
def experimental_repository():
    return [test_pipeline, metrics_pipeline, rollup_pipeline] + define_schedules()
