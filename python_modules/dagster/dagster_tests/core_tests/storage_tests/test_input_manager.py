import tempfile

import pytest

from dagster import (
    DagsterInstance,
    DagsterInvalidDefinitionError,
    IOManager,
    In,
    InputDefinition,
    InputManager,
    MetadataEntry,
    ModeDefinition,
    OutputDefinition,
    PythonObjectDagsterType,
    composite_solid,
    execute_pipeline,
    execute_solid,
    input_manager,
    io_manager,
    job,
    op,
    pipeline,
    resource,
    input_manager,
    solid,
)
from dagster.core.definitions.events import Failure, RetryRequested
from dagster.core.errors import DagsterInvalidConfigError
from dagster.core.instance import InstanceRef

### input manager tests


def test_input_manager_override():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert False, "should not be called"

    @io_manager
    def my_io_manager():
        return MyIOManager()

    class MyInputManager(MyIOManager):
        def load_input(self, context):
            if context.upstream_output is None:
                assert False, "upstream output should not be None"
            else:
                return 4

    @io_manager
    def my_input_manager():
        return MyInputManager()

    @op
    def first_op():
        return 1

    @op(ins={"an_input": In(input_manager_key="my_input_manager")})
    def second_op(an_input):
        assert an_input == 4

    @job(resource_defs={"io_manager": my_io_manager, "my_input_manager": my_input_manager})
    def check_input_managers():
        out = first_op()
        second_op(out)

    check_input_managers.execute_in_process()


def test_input_manager_root_input():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert False, "should not be called"

    @io_manager
    def my_io_manager():
        return MyIOManager()

    class MyInputManager(MyIOManager):
        def load_input(self, context):
            if context.upstream_output is None:
                return 4
            else:
                assert False, "upstream output should be None"

    @io_manager
    def my_input_manager():
        return MyInputManager()

    @op
    def first_op():
        return 1

    @op(ins={"an_input": In(input_manager_key="my_input_manager")})
    def second_op(an_input):
        assert an_input == 4

    @job(resource_defs={"io_manager": my_io_manager, "my_input_manager": my_input_manager})
    def check_input_managers():
        first_op()
        second_op()

    check_input_managers.execute_in_process()


def test_input_manager_calls_super():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 6

    @io_manager
    def my_io_manager():
        return MyIOManager()

    class MyInputManager(MyIOManager):
        def load_input(self, context):
            if context.upstream_output is None:
                assert False, "upstream output should not be None"
            else:
                return super().load_input(context)

    @io_manager
    def my_input_manager():
        return MyInputManager()

    @op
    def first_op():
        return 1

    @op(ins={"an_input": In(input_manager_key="my_input_manager")})
    def second_op(an_input):
        assert an_input == 6

    @job(resource_defs={"io_manager": my_io_manager, "my_input_manager": my_input_manager})
    def check_input_managers():
        out = first_op()
        second_op(out)

    check_input_managers.execute_in_process()


def test_input_config():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert False, "should not be called"

    @io_manager
    def my_io_manager():
        return MyIOManager()

    class MyInputManager(MyIOManager):
        def load_input(self, context):
            if context.upstream_output is None:
                assert False, "upstream output should not be None"
            else:
                return context.config["config_value"]

    @io_manager(input_config_schema={"config_value": int})
    def my_input_manager():
        return MyInputManager()

    @op
    def first_op():
        return 1

    @op(ins={"an_input": In(input_manager_key="my_input_manager")})
    def second_op(an_input):
        assert an_input == 6

    @job(resource_defs={"io_manager": my_io_manager, "my_input_manager": my_input_manager})
    def check_input_managers():
        out = first_op()
        second_op(out)

    check_input_managers.execute_in_process(
        run_config={"ops": {"second_op": {"inputs": {"an_input": {"config_value": 6}}}}}
    )

    with pytest.raises(DagsterInvalidConfigError):
        check_input_managers.execute_in_process(
            run_config={
                "ops": {"second_op": {"inputs": {"an_input": {"config_value": "a_string"}}}}
            }
        )


def test_input_manager_decorator():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert False, "should not be called"

    @io_manager
    def my_io_manager():
        return MyIOManager()

    class MyInputManager(MyIOManager):
        def load_input(self, context):
            if context.upstream_output is None:
                assert False, "upstream output should not be None"
            else:
                return 4

    @input_manager
    def my_input_manager():
        return MyInputManager()

    @op
    def first_op():
        return 1

    @op(ins={"an_input": In(input_manager_key="my_input_manager")})
    def second_op(an_input):
        assert an_input == 4

    @job(resource_defs={"io_manager": my_io_manager, "my_input_manager": my_input_manager})
    def check_input_managers():
        out = first_op()
        second_op(out)

    check_input_managers.execute_in_process()


def test_input_manager_w_function():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert False, "should not be called"

    @io_manager
    def my_io_manager():
        return MyIOManager()

    @input_manager
    def my_input_manager():
        return 4

    @op
    def first_op():
        return 1

    @op(ins={"an_input": In(input_manager_key="my_input_manager")})
    def second_op(an_input):
        assert an_input == 4

    @job(resource_defs={"io_manager": my_io_manager, "my_input_manager": my_input_manager})
    def check_input_managers():
        out = first_op()
        second_op(out)

    check_input_managers.execute_in_process()


def test_input_manager_class():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert False, "should not be called"

    @io_manager
    def my_io_manager():
        return MyIOManager()

    class MyInputManager(InputManager):
        def load_input(self, context):
            if context.upstream_output is None:
                assert False, "upstream output should not be None"
            else:
                return 4

    @input_manager
    def my_input_manager():
        return MyInputManager()

    @op
    def first_op():
        return 1

    @op(ins={"an_input": In(input_manager_key="my_input_manager")})
    def second_op(an_input):
        assert an_input == 4

    @job(resource_defs={"io_manager": my_io_manager, "my_input_manager": my_input_manager})
    def check_input_managers():
        out = first_op()
        second_op(out)

    check_input_managers.execute_in_process()
