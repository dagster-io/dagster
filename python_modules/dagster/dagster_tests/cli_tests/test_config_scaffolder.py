from dagster import (
    Int,
    OpDefinition,
    ResourceDefinition,
    _check as check,
)
from dagster._cli.config_scaffolder import scaffold_job_config, scaffold_type
from dagster._config import config_type
from dagster._core.definitions.graph_definition import GraphDefinition


def fail_me():
    return check.failed("Should not call")


def test_scalars():
    assert scaffold_type(config_type.Int()) == 0
    assert scaffold_type(config_type.String()) == ""
    assert scaffold_type(config_type.Bool()) is True
    assert scaffold_type(config_type.Any()) == "AnyType"


def test_basic_ops_config(snapshot):
    job_def = GraphDefinition(
        name="BasicOpsConfigGraph",
        node_defs=[
            OpDefinition(
                name="required_field_op",
                config_schema={"required_int": Int},
                compute_fn=lambda *_args: fail_me(),
            )
        ],
    ).to_job()

    env_config_type = job_def.run_config_schema.config_type

    assert env_config_type.fields["ops"].is_required
    ops_config_type = env_config_type.fields["ops"].config_type
    assert ops_config_type.fields["required_field_op"].is_required
    required_op_config_type = ops_config_type.fields["required_field_op"].config_type
    assert required_op_config_type.fields["config"].is_required

    assert set(env_config_type.fields["loggers"].config_type.fields.keys()) == set(["console"])

    console_logger_config_type = env_config_type.fields["loggers"].config_type.fields["console"]

    assert set(console_logger_config_type.config_type.fields.keys()) == set(["config"])

    assert console_logger_config_type.config_type.fields["config"].is_required is False

    console_logger_config_config_type = console_logger_config_type.config_type.fields[
        "config"
    ].config_type

    assert set(console_logger_config_config_type.fields.keys()) == set(["log_level", "name"])

    snapshot.assert_match(scaffold_job_config(job_def, skip_non_required=False))


def dummy_resource(config_field):
    return ResourceDefinition(lambda _: None, config_field)
