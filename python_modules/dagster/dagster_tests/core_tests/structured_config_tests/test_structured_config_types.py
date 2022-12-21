import pytest
from dagster import job, op
from dagster._config.config_type import ConfigTypeKind
from dagster._config.structured_config import Config, PermissiveConfig
from dagster._core.errors import DagsterInvalidConfigError


def test_default_config_class_non_permissive():
    class AnOpConfig(Config):
        a_string: str
        an_int: int

    executed = {}

    @op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.a_string == "foo"
        assert config.an_int == 2

    @job
    def a_job():
        a_struct_config_op()

    with pytest.raises(DagsterInvalidConfigError):
        a_job.execute_in_process(
            {
                "ops": {
                    "a_struct_config_op": {
                        "config": {"a_string": "foo", "an_int": 2, "a_bool": True}
                    }
                }
            }
        )


def test_struct_config_permissive():
    class AnOpConfig(PermissiveConfig):
        a_string: str
        an_int: int

    executed = {}

    @op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.a_string == "foo"
        assert config.an_int == 2

        # Can pull out config dict to access permissive fields
        assert config.dict() == {"a_string": "foo", "an_int": 2, "a_bool": True}

    from dagster._core.definitions.decorators.solid_decorator import DecoratedOpFunction

    assert DecoratedOpFunction(a_struct_config_op).has_config_arg()

    # test fields are inferred correctly
    assert a_struct_config_op.config_schema.config_type.kind == ConfigTypeKind.PERMISSIVE_SHAPE
    assert list(a_struct_config_op.config_schema.config_type.fields.keys()) == [
        "a_string",
        "an_int",
    ]

    @job
    def a_job():
        a_struct_config_op()

    assert a_job

    a_job.execute_in_process(
        {
            "ops": {
                "a_struct_config_op": {"config": {"a_string": "foo", "an_int": 2, "a_bool": True}}
            }
        }
    )

    assert executed["yes"]
