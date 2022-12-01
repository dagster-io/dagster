from dagster import (
    Int,
    OpDefinition,
    ResourceDefinition,
    String,
    _check as check,
)
from dagster._cli.config_scaffolder import scaffold_pipeline_config, scaffold_type
from dagster._config import config_type
from dagster._core.definitions import create_run_config_schema
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.job_definition import JobDefinition


def fail_me():
    return check.failed("Should not call")


def test_scalars():
    assert scaffold_type(config_type.Int()) == 0
    assert scaffold_type(config_type.String()) == ""
    assert scaffold_type(config_type.Bool()) is True
    assert scaffold_type(config_type.Any()) == "AnyType"


def test_basic_ops_config(snapshot):
    pipeline_def = JobDefinition(
        graph_def=GraphDefinition(
            name="BasicSolidsConfigPipeline",
            node_defs=[
                OpDefinition(
                    name="required_field_solid",
                    config_schema={"required_int": Int},
                    compute_fn=lambda *_args: fail_me(),
                )
            ],
        )
    )

    env_config_type = create_run_config_schema(pipeline_def).config_type

    assert env_config_type.fields["solids"].is_required
    solids_config_type = env_config_type.fields["solids"].config_type
    assert solids_config_type.fields["required_field_solid"].is_required
    required_solid_config_type = solids_config_type.fields["required_field_solid"].config_type
    assert required_solid_config_type.fields["config"].is_required

    assert set(env_config_type.fields["loggers"].config_type.fields.keys()) == set(["console"])

    console_logger_config_type = env_config_type.fields["loggers"].config_type.fields["console"]

    assert set(console_logger_config_type.config_type.fields.keys()) == set(["config"])

    assert console_logger_config_type.config_type.fields["config"].is_required is False

    console_logger_config_config_type = console_logger_config_type.config_type.fields[
        "config"
    ].config_type

    assert set(console_logger_config_config_type.fields.keys()) == set(["log_level", "name"])

    snapshot.assert_match(scaffold_pipeline_config(pipeline_def, skip_non_required=False))


def dummy_resource(config_field):
    return ResourceDefinition(lambda _: None, config_field)
