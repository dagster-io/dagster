import tempfile

import pytest
from dagster import (
    AssetIn,
    AssetKey,
    DagsterInstance,
    DagsterInvalidDefinitionError,
    In,
    InputManager,
    IOManager,
    IOManagerDefinition,
    asset,
    graph,
    input_manager,
    io_manager,
    job,
    materialize,
    op,
    resource,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import Failure, RetryRequested
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.errors import DagsterInvalidConfigError
from dagster._core.instance import InstanceRef
from dagster._core.storage.input_manager import InputManagerDefinition
from dagster._utils.test import wrap_op_in_graph_and_execute

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

    @job(
        resource_defs={
            "io_manager": my_io_manager,
            "my_input_manager": my_input_manager,
        }
    )
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

    @job(
        resource_defs={
            "io_manager": my_io_manager,
            "my_input_manager": my_input_manager,
        }
    )
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

    @job(
        resource_defs={
            "io_manager": my_io_manager,
            "my_input_manager": my_input_manager,
        }
    )
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

    @job(
        resource_defs={
            "io_manager": my_io_manager,
            "my_input_manager": my_input_manager,
        }
    )
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

    @job(
        resource_defs={
            "io_manager": my_io_manager,
            "my_input_manager": my_input_manager,
        }
    )
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

    @job(
        resource_defs={
            "io_manager": my_io_manager,
            "my_input_manager": my_input_manager,
        }
    )
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

    @job(
        resource_defs={
            "io_manager": my_io_manager,
            "my_input_manager": my_input_manager,
        }
    )
    def check_input_managers():
        out = first_op()
        second_op(out)

    check_input_managers.execute_in_process()


def test_input_manager_with_assets():
    @asset
    def upstream() -> int:
        return 1

    @asset(ins={"upstream": AssetIn(input_manager_key="special_io_manager")})
    def downstream(upstream) -> int:
        return upstream + 1

    class MyIOManager(IOManager):
        def load_input(self, context):
            assert context.upstream_output is not None
            assert context.upstream_output.asset_key == AssetKey(["upstream"])

            return 2

        def handle_output(self, context, obj): ...

    materialize([upstream])
    output = materialize(
        [*upstream.to_source_assets(), downstream],
        resources={"special_io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )

    assert output._get_output_for_handle("downstream", "result") == 3  # noqa: SLF001


def test_input_manager_with_assets_no_default_io_manager():
    """Tests loading an upstream asset with an input manager when the downstream asset also uses a
    custom io manager. Fixes a bug where dagster expected the io_manager key to be provided.
    """

    @asset
    def upstream() -> int:
        return 1

    @asset(
        ins={"upstream": AssetIn(input_manager_key="special_io_manager")},
        io_manager_key="special_io_manager",
    )
    def downstream(upstream) -> int:
        return upstream + 1

    class MyIOManager(IOManager):
        def load_input(self, context):
            assert context.upstream_output is not None
            assert context.upstream_output.asset_key == AssetKey(["upstream"])

            return 2

        def handle_output(self, context, obj):
            return None

    materialize(
        [upstream, downstream],
        resources={"special_io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )

    materialize(
        [*upstream.to_source_assets(), downstream],
        resources={"special_io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )


def test_input_manager_with_assets_and_config():
    """Tests that the correct config is passed to the io manager when using input_manager_key.
    Fixes a bug when the config for the default io manager was passed to the input_manager_key io manager.
    """

    @asset
    def upstream() -> int:
        return 1

    @asset(
        ins={"upstream": AssetIn(input_manager_key="special_io_manager")},
        io_manager_key="special_io_manager",
    )
    def downstream(upstream) -> int:
        return upstream + 1

    class MyIOManager(IOManager):
        def load_input(self, context):
            assert context.resource_config["foo"] == "bar"
            assert context.upstream_output is not None
            assert context.upstream_output.asset_key == AssetKey(["upstream"])

            return 2

        def handle_output(self, context, obj):
            return None

    @io_manager(config_schema={"foo": str})
    def my_io_manager():
        return MyIOManager()

    materialize(
        [upstream, downstream],
        resources={"special_io_manager": my_io_manager.configured({"foo": "bar"})},
    )


##################################################
# root input manager tests (deprecate in 1.0.0) #
##################################################


def test_configured():
    @input_manager(
        config_schema={"base_dir": str},
        description="abc",
        input_config_schema={"format": str},
        required_resource_keys={"r1", "r2"},
        version="123",
    )
    def my_input_manager(_):
        pass

    configured_input_manager = my_input_manager.configured({"base_dir": "/a/b/c"})

    assert isinstance(configured_input_manager, InputManagerDefinition)
    assert configured_input_manager.description == my_input_manager.description
    assert (
        configured_input_manager.required_resource_keys == my_input_manager.required_resource_keys
    )
    assert configured_input_manager.version is None


def test_input_manager_with_failure():
    @input_manager
    def should_fail(_):
        raise Failure(
            description="Foolure",
            metadata={"label": "text"},
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

        failure_data = result.filter_events(lambda evt: evt.is_step_failure)[0].step_failure_data

        assert failure_data.error.cls_name == "Failure"

        assert failure_data.user_failure_data.description == "Foolure"
        assert failure_data.user_failure_data.metadata["label"] == MetadataValue.text("text")


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

    @op(ins={"op_input": In(input_manager_key="should_succeed_after_retries")})
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


def test_input_manager_resource_config():
    @input_manager(config_schema={"dog": str})
    def emit_dog(context):
        assert context.resource_config["dog"] == "poodle"

    @op(ins={"op_input": In(input_manager_key="emit_dog")})
    def source_op(_, op_input):
        return op_input

    @job(resource_defs={"emit_dog": emit_dog})
    def basic_job():
        source_op(source_op())

    result = basic_job.execute_in_process(
        run_config={"resources": {"emit_dog": {"config": {"dog": "poodle"}}}},
    )

    assert result.success


def test_input_manager_required_resource_keys():
    @resource
    def foo_resource(_):
        return "foo"

    @input_manager(required_resource_keys={"foo_resource"})
    def input_manager_reqs_resources(context):
        assert context.resources.foo_resource == "foo"

    @op(ins={"_manager_input": In(input_manager_key="input_manager_reqs_resources")})
    def big_op(_, _manager_input):
        return "manager_input"

    @job(
        resource_defs={
            "input_manager_reqs_resources": input_manager_reqs_resources,
            "foo_resource": foo_resource,
        }
    )
    def basic_job():
        big_op()

    result = basic_job.execute_in_process()

    assert result.success


def test_resource_not_input_manager():
    @resource
    def resource_not_manager(_):
        return "foo"

    @op(ins={"_input": In(input_manager_key="not_manager")})
    def op_requires_manager(_, _input):
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "input manager with key 'not_manager' required by input '_input' of op"
            " 'op_requires_manager', but received <class"
            " 'dagster._core.definitions.resource_definition.ResourceDefinition'>"
        ),
    ):

        @job(resource_defs={"not_manager": resource_not_manager})
        def basic():
            op_requires_manager()

        Definitions(jobs=[basic])


def test_missing_input_manager():
    @op(ins={"a": In(input_manager_key="missing_input_manager")})
    def my_op(_, a):
        return a + 1

    with pytest.raises(DagsterInvalidDefinitionError):
        wrap_op_in_graph_and_execute(my_op, input_values={"a": 5})


def test_input_manager_inside_composite():
    @input_manager(input_config_schema={"test": str})
    def my_manager(context):
        return context.config["test"]

    @op(ins={"data": In(dagster_type=str, input_manager_key="my_root")})
    def inner_op(_, data):
        return data

    @graph
    def my_graph():
        return inner_op()

    @job(resource_defs={"my_root": my_manager})
    def my_job():
        my_graph()

    result = my_job.execute_in_process(
        run_config={
            "ops": {
                "my_graph": {
                    "ops": {"inner_op": {"inputs": {"data": {"test": "hello"}}}},
                }
            }
        },
    )

    assert result.output_for_node("my_graph") == "hello"
