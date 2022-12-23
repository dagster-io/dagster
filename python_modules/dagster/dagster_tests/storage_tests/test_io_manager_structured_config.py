# pylint: disable=unused-argument
import pytest

from dagster import DagsterInvalidConfigError, In, io_manager, job, op
from dagster._config.structured_config import (
    Config,
    StructuredConfigIOManager,
    StructuredConfigIOManagerBase,
)
from dagster._config.type_printer import print_config_type_to_string
from dagster._core.definitions.definition_config_schema import IDefinitionConfigSchema
from dagster._core.storage.io_manager import IOManagerDefinition


def test_config_schemas():
    # Decorator-based IO manager definition
    @io_manager(
        config_schema={"base_dir": str},
        output_config_schema={"path": str},
        input_config_schema={"format": str},
    )
    def an_io_manager():
        pass

    # Equivalent class-based IO manager definition
    class AnIoManager(StructuredConfigIOManagerBase):
        base_dir: str

        class OutputConfigSchema(Config):
            path: str

        class InputConfigSchema(Config):
            format: str

        def resource_function(self, _):
            pass

    configured_io_manager = AnIoManager(base_dir="/a/b/c")

    assert isinstance(configured_io_manager, IOManagerDefinition)
    assert type_string_from_config_schema(
        configured_io_manager.output_config_schema
    ) == type_string_from_config_schema(an_io_manager.output_config_schema)
    assert type_string_from_config_schema(
        configured_io_manager.input_config_schema
    ) == type_string_from_config_schema(an_io_manager.input_config_schema)


def type_string_from_config_schema(config_schema: IDefinitionConfigSchema):
    return print_config_type_to_string(config_schema.config_type)


def test_load_input_handle_output():
    class MyIOManager(StructuredConfigIOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert False, "should not be called"

    class MyInputManager(MyIOManager):
        class InputConfigSchema(Config):
            config_value: int

        def load_input(self, context):
            if context.upstream_output is None:
                assert False, "upstream output should not be None"
            else:
                return context.config["config_value"]

    did_run = {}

    @op
    def first_op():
        did_run["first_op"] = True
        return 1

    @op(ins={"an_input": In(input_manager_key="my_input_manager")})
    def second_op(an_input):
        assert an_input == 6
        did_run["second_op"] = True

    @job(
        resource_defs={
            "io_manager": MyIOManager(),
            "my_input_manager": MyInputManager(),
        }
    )
    def check_input_managers():
        out = first_op()
        second_op(out)

    check_input_managers.execute_in_process(
        run_config={"ops": {"second_op": {"inputs": {"an_input": {"config_value": 6}}}}}
    )
    assert did_run["first_op"]
    assert did_run["second_op"]

    with pytest.raises(DagsterInvalidConfigError):
        check_input_managers.execute_in_process(
            run_config={
                "ops": {"second_op": {"inputs": {"an_input": {"config_value": "a_string"}}}}
            }
        )
