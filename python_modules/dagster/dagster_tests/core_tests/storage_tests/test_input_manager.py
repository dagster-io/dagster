import tempfile

import pytest

from dagster import (
    IOManager,
    In,
    InputManager,
    input_manager,
    io_manager,
    job,
    op,
    DagsterInstance,
    MetadataEntry
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

def test_input_manager_with_retries():
    _count = {"total": 0}

    @input_manager
    def should_succeed_after_retries(_):
        if _count["total"] < 2:
            _count["total"] += 1
            raise RetryRequested(max_retries=3)
        return "foo"

    @input_manager
    def should_retry(_):
        raise RetryRequested(max_retries=3)

    @op(
        ins={"op_input": In(input_manager_key="should_succeed_after_retries")}
    )
    def take_input_1(_, op_input):
        return op_input

    @op(ins={"op_input": In(input_manager_key="should_retry")})
    def take_input_2(_, op_input):
        return op_input

    @op
    def take_input_3(_, _input1, _input2):
        assert False, "should not be called"

    @job(
        resource_defs={
            "should_succeed_after_retries": should_succeed_after_retries,
            "should_retry": should_retry,
        }
    )
    def simple():
        take_input_3(take_input_2(), take_input_1())

    with tempfile.TemporaryDirectory() as tmpdir_path:

        instance = DagsterInstance.from_ref(InstanceRef.from_dir(tmpdir_path))

        result = simple.execute_in_process(instance=instance, raise_on_error=False)

        step_stats = instance.get_run_step_stats(result.run_id)
        assert len(step_stats) == 2

        step_stats_1 = instance.get_run_step_stats(result.run_id, step_keys=["take_input_1"])
        assert len(step_stats_1) == 1
        step_stat_1 = step_stats_1[0]
        assert step_stat_1.status.value == "SUCCESS"
        assert step_stat_1.attempts == 3

        step_stats_2 = instance.get_run_step_stats(result.run_id, step_keys=["take_input_2"])
        assert len(step_stats_2) == 1
        step_stat_2 = step_stats_2[0]
        assert step_stat_2.status.value == "FAILURE"
        assert step_stat_2.attempts == 4

        step_stats_3 = instance.get_run_step_stats(result.run_id, step_keys=["take_input_3"])
        assert len(step_stats_3) == 0


def test_input_manager_with_failure():
    @input_manager
    def should_fail(_):
        raise Failure(
            description="Foolure",
            metadata_entries=[MetadataEntry("label", value="text")],
        )

    @op(ins={"_fail_input": In(input_manager_key="should_fail")})
    def fail_on_input(_, _fail_input):
        assert False, "should not be called"

    @job(resource_defs={"should_fail": should_fail})
    def simple():
        fail_on_input()

    with tempfile.TemporaryDirectory() as tmpdir_path:

        instance = DagsterInstance.from_ref(InstanceRef.from_dir(tmpdir_path))

        result = simple.execute_in_process(instance=instance, raise_on_error=False)

        assert not result.success
