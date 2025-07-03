import tempfile

import dagster as dg
import pytest
from dagster import DagsterInstance, IOManagerDefinition
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.instance import InstanceRef
from dagster._utils.test import wrap_op_in_graph_and_execute

### input manager tests


def test_input_manager_override():
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert False, "should not be called"

    @dg.io_manager
    def my_io_manager():
        return MyIOManager()

    class MyInputManager(MyIOManager):
        def load_input(self, context):  # pyright: ignore[reportIncompatibleMethodOverride]
            if context.upstream_output is None:
                assert False, "upstream output should not be None"
            else:
                return 4

    @dg.io_manager
    def my_input_manager():
        return MyInputManager()

    @dg.op
    def first_op():
        return 1

    @dg.op(ins={"an_input": dg.In(input_manager_key="my_input_manager")})
    def second_op(an_input):
        assert an_input == 4

    @dg.job(
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
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert False, "should not be called"

    @dg.io_manager
    def my_io_manager():
        return MyIOManager()

    class MyInputManager(MyIOManager):
        def load_input(self, context):  # pyright: ignore[reportIncompatibleMethodOverride]
            if context.upstream_output is None:
                return 4
            else:
                assert False, "upstream output should be None"

    @dg.io_manager
    def my_input_manager():
        return MyInputManager()

    @dg.op
    def first_op():
        return 1

    @dg.op(ins={"an_input": dg.In(input_manager_key="my_input_manager")})
    def second_op(an_input):
        assert an_input == 4

    @dg.job(
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
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 6

    @dg.io_manager
    def my_io_manager():
        return MyIOManager()

    class MyInputManager(MyIOManager):
        def load_input(self, context):
            if context.upstream_output is None:
                assert False, "upstream output should not be None"
            else:
                return super().load_input(context)

    @dg.io_manager
    def my_input_manager():
        return MyInputManager()

    @dg.op
    def first_op():
        return 1

    @dg.op(ins={"an_input": dg.In(input_manager_key="my_input_manager")})
    def second_op(an_input):
        assert an_input == 6

    @dg.job(
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
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert False, "should not be called"

    @dg.io_manager
    def my_io_manager():
        return MyIOManager()

    class MyInputManager(MyIOManager):
        def load_input(self, context):
            if context.upstream_output is None:
                assert False, "upstream output should not be None"
            else:
                return context.config["config_value"]

    @dg.io_manager(input_config_schema={"config_value": int})
    def my_input_manager():
        return MyInputManager()

    @dg.op
    def first_op():
        return 1

    @dg.op(ins={"an_input": dg.In(input_manager_key="my_input_manager")})
    def second_op(an_input):
        assert an_input == 6

    @dg.job(
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

    with pytest.raises(dg.DagsterInvalidConfigError):
        check_input_managers.execute_in_process(
            run_config={
                "ops": {"second_op": {"inputs": {"an_input": {"config_value": "a_string"}}}}
            }
        )


def test_input_manager_decorator():
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert False, "should not be called"

    @dg.io_manager
    def my_io_manager():
        return MyIOManager()

    class MyInputManager(MyIOManager):
        def load_input(self, context):  # pyright: ignore[reportIncompatibleMethodOverride]
            if context.upstream_output is None:
                assert False, "upstream output should not be None"
            else:
                return 4

    @dg.input_manager
    def my_input_manager():
        return MyInputManager()

    @dg.op
    def first_op():
        return 1

    @dg.op(ins={"an_input": dg.In(input_manager_key="my_input_manager")})
    def second_op(an_input):
        assert an_input == 4

    @dg.job(
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
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert False, "should not be called"

    @dg.io_manager
    def my_io_manager():
        return MyIOManager()

    @dg.input_manager
    def my_input_manager():
        return 4

    @dg.op
    def first_op():
        return 1

    @dg.op(ins={"an_input": dg.In(input_manager_key="my_input_manager")})
    def second_op(an_input):
        assert an_input == 4

    @dg.job(
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
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert False, "should not be called"

    @dg.io_manager
    def my_io_manager():
        return MyIOManager()

    class MyInputManager(dg.InputManager):
        def load_input(self, context):
            if context.upstream_output is None:
                assert False, "upstream output should not be None"
            else:
                return 4

    @dg.input_manager
    def my_input_manager():
        return MyInputManager()

    @dg.op
    def first_op():
        return 1

    @dg.op(ins={"an_input": dg.In(input_manager_key="my_input_manager")})
    def second_op(an_input):
        assert an_input == 4

    @dg.job(
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
    @dg.asset
    def upstream() -> int:
        return 1

    @dg.asset(ins={"upstream": dg.AssetIn(input_manager_key="special_io_manager")})
    def downstream(upstream) -> int:
        return upstream + 1

    class MyIOManager(dg.IOManager):
        def load_input(self, context):
            assert context.upstream_output is not None
            assert context.upstream_output.asset_key == dg.AssetKey(["upstream"])

            return 2

        def handle_output(self, context, obj): ...

    dg.materialize([upstream])
    output = dg.materialize(
        [*upstream.to_source_assets(), downstream],
        resources={"special_io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )

    assert output._get_output_for_handle("downstream", "result") == 3  # noqa: SLF001  # pyright: ignore[reportArgumentType]


def test_input_manager_with_observable_source_asset() -> None:
    fancy_metadata = {"foo": "bar", "baz": 1.23}

    @dg.observable_source_asset(metadata=fancy_metadata)
    def upstream():
        return dg.DataVersion("1")

    @dg.asset(ins={"upstream": dg.AssetIn(input_manager_key="special_io_manager")})
    def downstream(upstream) -> int:
        return upstream + 1

    class MyIOManager(dg.IOManager):
        def load_input(self, context) -> int:
            assert context.upstream_output is not None
            assert context.upstream_output.asset_key == dg.AssetKey(["upstream"])
            # the process of converting assets to source assets leaves an extra metadata entry
            # of dagster/io_manager_key in the dictionary, so we can't use simple equality here
            for k, v in fancy_metadata.items():
                assert context.upstream_output.definition_metadata[k] == v
            return 2

        def handle_output(self, context, obj) -> None: ...

    dg.materialize(assets=[upstream, downstream], resources={"special_io_manager": MyIOManager()})


def test_input_manager_with_assets_no_default_io_manager():
    """Tests loading an upstream asset with an input manager when the downstream asset also uses a
    custom io manager. Fixes a bug where dagster expected the io_manager key to be provided.
    """

    @dg.asset
    def upstream() -> int:
        return 1

    @dg.asset(
        ins={"upstream": dg.AssetIn(input_manager_key="special_io_manager")},
        io_manager_key="special_io_manager",
    )
    def downstream(upstream) -> int:
        return upstream + 1

    class MyIOManager(dg.IOManager):
        def load_input(self, context):
            assert context.upstream_output is not None
            assert context.upstream_output.asset_key == dg.AssetKey(["upstream"])

            return 2

        def handle_output(self, context, obj):
            return None

    dg.materialize(
        [upstream, downstream],
        resources={"special_io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )

    dg.materialize(
        [*upstream.to_source_assets(), downstream],
        resources={"special_io_manager": IOManagerDefinition.hardcoded_io_manager(MyIOManager())},
    )


def test_input_manager_with_assets_and_config():
    """Tests that the correct config is passed to the io manager when using input_manager_key.
    Fixes a bug when the config for the default io manager was passed to the input_manager_key io manager.
    """

    @dg.asset
    def upstream() -> int:
        return 1

    @dg.asset(
        ins={"upstream": dg.AssetIn(input_manager_key="special_io_manager")},
        io_manager_key="special_io_manager",
    )
    def downstream(upstream) -> int:
        return upstream + 1

    class MyIOManager(dg.IOManager):
        def load_input(self, context):
            assert context.resource_config["foo"] == "bar"  # pyright: ignore[reportOptionalSubscript]
            assert context.upstream_output is not None
            assert context.upstream_output.asset_key == dg.AssetKey(["upstream"])

            return 2

        def handle_output(self, context, obj):
            return None

    @dg.io_manager(config_schema={"foo": str})
    def my_io_manager():
        return MyIOManager()

    dg.materialize(
        [upstream, downstream],
        resources={"special_io_manager": my_io_manager.configured({"foo": "bar"})},
    )


##################################################
# root input manager tests (deprecate in 1.0.0) #
##################################################


def test_configured():
    @dg.input_manager(
        config_schema={"base_dir": str},
        description="abc",
        input_config_schema={"format": str},
        required_resource_keys={"r1", "r2"},
        version="123",
    )
    def my_input_manager(_):
        pass

    configured_input_manager = my_input_manager.configured({"base_dir": "/a/b/c"})

    assert isinstance(configured_input_manager, dg.InputManagerDefinition)
    assert configured_input_manager.description == my_input_manager.description
    assert (
        configured_input_manager.required_resource_keys == my_input_manager.required_resource_keys
    )
    assert configured_input_manager.version is None


def test_input_manager_with_failure():
    @dg.input_manager
    def should_fail(_):
        raise dg.Failure(
            description="Foolure",
            metadata={"label": "text"},
        )

    @dg.op(ins={"_fail_input": dg.In(input_manager_key="should_fail")})
    def fail_on_input(_, _fail_input):
        assert False, "should not be called"

    @dg.job(resource_defs={"should_fail": should_fail})
    def simple():
        fail_on_input()

    with tempfile.TemporaryDirectory() as tmpdir_path:
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(tmpdir_path))

        result = simple.execute_in_process(instance=instance, raise_on_error=False)

        assert not result.success

        failure_data = result.filter_events(lambda evt: evt.is_step_failure)[0].step_failure_data

        assert failure_data.error.cls_name == "Failure"  # pyright: ignore[reportOptionalMemberAccess]

        assert failure_data.user_failure_data.description == "Foolure"  # pyright: ignore[reportOptionalMemberAccess]
        assert failure_data.user_failure_data.metadata["label"] == MetadataValue.text("text")  # pyright: ignore[reportOptionalMemberAccess]


def test_input_manager_with_retries():
    _count = {"total": 0}

    @dg.input_manager
    def should_succeed_after_retries(_):
        if _count["total"] < 2:
            _count["total"] += 1
            raise dg.RetryRequested(max_retries=3)
        return "foo"

    @dg.input_manager
    def should_retry(_):
        raise dg.RetryRequested(max_retries=3)

    @dg.op(ins={"op_input": dg.In(input_manager_key="should_succeed_after_retries")})
    def take_input_1(_, op_input):
        return op_input

    @dg.op(ins={"op_input": dg.In(input_manager_key="should_retry")})
    def take_input_2(_, op_input):
        return op_input

    @dg.op
    def take_input_3(_, _input1, _input2):
        assert False, "should not be called"

    @dg.job(
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
        assert step_stat_1.status.value == "SUCCESS"  # pyright: ignore[reportOptionalMemberAccess]
        assert step_stat_1.attempts == 3

        step_stats_2 = instance.get_run_step_stats(result.run_id, step_keys=["take_input_2"])
        assert len(step_stats_2) == 1
        step_stat_2 = step_stats_2[0]
        assert step_stat_2.status.value == "FAILURE"  # pyright: ignore[reportOptionalMemberAccess]
        assert step_stat_2.attempts == 4

        step_stats_3 = instance.get_run_step_stats(result.run_id, step_keys=["take_input_3"])
        assert len(step_stats_3) == 0


def test_input_manager_resource_config():
    @dg.input_manager(config_schema={"dog": str})
    def emit_dog(context):
        assert context.resource_config["dog"] == "poodle"

    @dg.op(ins={"op_input": dg.In(input_manager_key="emit_dog")})
    def source_op(_, op_input):
        return op_input

    @dg.job(resource_defs={"emit_dog": emit_dog})
    def basic_job():
        source_op(source_op())

    result = basic_job.execute_in_process(
        run_config={"resources": {"emit_dog": {"config": {"dog": "poodle"}}}},
    )

    assert result.success


def test_input_manager_required_resource_keys():
    @dg.resource
    def foo_resource(_):
        return "foo"

    @dg.input_manager(required_resource_keys={"foo_resource"})
    def input_manager_reqs_resources(context):
        assert context.resources.foo_resource == "foo"

    @dg.op(ins={"_manager_input": dg.In(input_manager_key="input_manager_reqs_resources")})
    def big_op(_, _manager_input):
        return "manager_input"

    @dg.job(
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
    @dg.resource
    def resource_not_manager(_):
        return "foo"

    @dg.op(ins={"_input": dg.In(input_manager_key="not_manager")})
    def op_requires_manager(_, _input):
        pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "input manager with key 'not_manager' required by input '_input' of op"
            " 'op_requires_manager', but received <class"
            " 'dagster._core.definitions.resource_definition.ResourceDefinition'>"
        ),
    ):

        @dg.job(resource_defs={"not_manager": resource_not_manager})
        def basic():
            op_requires_manager()

        dg.Definitions(jobs=[basic])


def test_missing_input_manager():
    @dg.op(ins={"a": dg.In(input_manager_key="missing_input_manager")})
    def my_op(_, a):
        return a + 1

    with pytest.raises(dg.DagsterInvalidDefinitionError):
        wrap_op_in_graph_and_execute(my_op, input_values={"a": 5})


def test_input_manager_inside_composite():
    @dg.input_manager(input_config_schema={"test": str})
    def my_manager(context):
        return context.config["test"]

    @dg.op(ins={"data": dg.In(dagster_type=str, input_manager_key="my_root")})
    def inner_op(_, data):
        return data

    @dg.graph
    def my_graph():
        return inner_op()

    @dg.job(resource_defs={"my_root": my_manager})
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
