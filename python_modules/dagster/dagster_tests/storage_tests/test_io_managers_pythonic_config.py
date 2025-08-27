import os
import tempfile
from typing import Any

import dagster as dg
from dagster import FilesystemIOManager
from dagster._config.type_printer import print_config_type_to_string


def type_string_from_config_schema(config_schema):
    return print_config_type_to_string(config_schema.config_type)


def test_load_input_handle_output():
    class MyIOManager(dg.ConfigurableIOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert False, "should not be called"

    class MyInputManager(MyIOManager):
        def load_input(self, context):  # pyright: ignore[reportIncompatibleMethodOverride]
            if context.upstream_output is None:
                assert False, "upstream output should not be None"
            else:
                return 6

    did_run = {}

    @dg.op
    def first_op():
        did_run["first_op"] = True
        return 1

    @dg.op(ins={"an_input": dg.In(input_manager_key="my_input_manager")})
    def second_op(an_input):
        assert an_input == 6
        did_run["second_op"] = True

    @dg.job(
        resource_defs={
            "io_manager": MyIOManager(),
            "my_input_manager": MyInputManager(),
        }
    )
    def check_input_managers():
        out = first_op()
        second_op(out)

    check_input_managers.execute_in_process()
    assert did_run["first_op"]
    assert did_run["second_op"]


def test_runtime_config():
    out_txt = []

    class MyIOManager(dg.ConfigurableIOManager):
        prefix: str

        def handle_output(self, context, obj):
            out_txt.append(f"{self.prefix}{obj}")

        def load_input(self, context):
            assert False, "should not be called"

    @dg.asset
    def hello_world_asset():
        return "hello, world!"

    defs = dg.Definitions(
        assets=[hello_world_asset],
        resources={"io_manager": MyIOManager.configure_at_launch()},
    )

    assert (
        defs.resolve_implicit_global_asset_job_def()
        .execute_in_process({"resources": {"io_manager": {"config": {"prefix": ""}}}})
        .success
    )
    assert out_txt == ["hello, world!"]

    out_txt.clear()

    assert (
        defs.resolve_implicit_global_asset_job_def()
        .execute_in_process({"resources": {"io_manager": {"config": {"prefix": "greeting: "}}}})
        .success
    )
    assert out_txt == ["greeting: hello, world!"]


def test_nested_resources():
    out_txt = []

    class IOConfigResource(dg.ConfigurableResource):
        prefix: str

    class MyIOManager(dg.ConfigurableIOManager):
        config: IOConfigResource

        def handle_output(self, context, obj):
            out_txt.append(f"{self.config.prefix}{obj}")

        def load_input(self, context):
            assert False, "should not be called"

    @dg.asset
    def hello_world_asset():
        return "hello, world!"

    defs = dg.Definitions(
        assets=[hello_world_asset],
        resources={
            "io_manager": MyIOManager(config=IOConfigResource(prefix="greeting: ")),
        },
    )

    assert defs.resolve_implicit_global_asset_job_def().execute_in_process().success
    assert out_txt == ["greeting: hello, world!"]


def test_nested_resources_runtime_config():
    out_txt = []

    class IOConfigResource(dg.ConfigurableResource):
        prefix: str

    class MyIOManager(dg.ConfigurableIOManager):
        config: IOConfigResource

        def handle_output(self, context, obj):
            out_txt.append(f"{self.config.prefix}{obj}")

        def load_input(self, context):
            assert False, "should not be called"

    @dg.asset
    def hello_world_asset():
        return "hello, world!"

    io_config = IOConfigResource.configure_at_launch()

    defs = dg.Definitions(
        assets=[hello_world_asset],
        resources={
            "io_config": io_config,
            "io_manager": MyIOManager(config=io_config),
        },
    )

    assert (
        defs.resolve_implicit_global_asset_job_def()
        .execute_in_process({"resources": {"io_config": {"config": {"prefix": ""}}}})
        .success
    )
    assert out_txt == ["hello, world!"]

    out_txt.clear()

    assert (
        defs.resolve_implicit_global_asset_job_def()
        .execute_in_process({"resources": {"io_config": {"config": {"prefix": "greeting: "}}}})
        .success
    )
    assert out_txt == ["greeting: hello, world!"]


def test_pythonic_fs_io_manager() -> None:
    with tempfile.TemporaryDirectory() as tmpdir_path:

        @dg.asset
        def hello_world_asset():
            return "hello, world!"

        defs = dg.Definitions(
            assets=[hello_world_asset],
            resources={"io_manager": dg.FilesystemIOManager(base_dir=tmpdir_path)},
        )

        assert not os.path.exists(os.path.join(tmpdir_path, "hello_world_asset"))
        assert defs.resolve_implicit_global_asset_job_def().execute_in_process().success
        assert os.path.exists(os.path.join(tmpdir_path, "hello_world_asset"))


def test_pythonic_fs_io_manager_runtime_config() -> None:
    with tempfile.TemporaryDirectory() as tmpdir_path:

        @dg.asset
        def hello_world_asset():
            return "hello, world!"

        defs = dg.Definitions(
            assets=[hello_world_asset],
            resources={"io_manager": FilesystemIOManager.configure_at_launch()},
        )

        assert not os.path.exists(os.path.join(tmpdir_path, "hello_world_asset"))
        assert (
            defs.resolve_implicit_global_asset_job_def()
            .execute_in_process(
                run_config=dg.RunConfig(
                    resources={"io_manager": dg.FilesystemIOManager(base_dir=tmpdir_path)}
                )
            )
            .success
        )
        assert os.path.exists(os.path.join(tmpdir_path, "hello_world_asset"))


def test_config_schemas() -> None:
    # Decorator-based IO manager definition
    @dg.io_manager(  # pyright: ignore[reportArgumentType]
        config_schema={"base_dir": dg.StringSource},
        output_config_schema={"path": dg.StringSource},
        input_config_schema={"format": dg.StringSource},
    )
    def an_io_manager():
        pass

    class OutputConfigSchema(dg.Config):
        path: str

    class InputConfigSchema(dg.Config):
        format: str

    class MyIOManager(dg.ConfigurableIOManager):
        base_dir: str

        @classmethod
        def input_config_schema(cls) -> type[dg.Config]:
            return InputConfigSchema

        @classmethod
        def output_config_schema(cls) -> type[dg.Config]:
            return OutputConfigSchema

        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            pass

    configured_io_manager = MyIOManager(base_dir="/a/b/c").get_resource_definition()

    # Check that the config schemas are the same
    assert isinstance(configured_io_manager, dg.IOManagerDefinition)
    assert type_string_from_config_schema(
        configured_io_manager.output_config_schema
    ) == type_string_from_config_schema(an_io_manager.output_config_schema)
    assert type_string_from_config_schema(
        configured_io_manager.input_config_schema
    ) == type_string_from_config_schema(an_io_manager.input_config_schema)

    class MyIOManagerNonPythonicSchemas(dg.ConfigurableIOManager):
        base_dir: str

        @classmethod
        def input_config_schema(cls):
            return {"format": dg.StringSource}

        @classmethod
        def output_config_schema(cls):
            return {"path": dg.StringSource}

        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            pass

    configured_io_manager_non_pythonic = MyIOManagerNonPythonicSchemas(
        base_dir="/a/b/c"
    ).get_resource_definition()

    # Check that the config schemas are the same
    assert isinstance(configured_io_manager_non_pythonic, dg.IOManagerDefinition)
    assert type_string_from_config_schema(
        configured_io_manager_non_pythonic.output_config_schema
    ) == type_string_from_config_schema(an_io_manager.output_config_schema)
    assert type_string_from_config_schema(
        configured_io_manager_non_pythonic.input_config_schema
    ) == type_string_from_config_schema(an_io_manager.input_config_schema)


import pytest
from dagster import InputContext, OutputContext


def test_load_input_handle_output_input_config() -> None:
    class MyIOManager(dg.ConfigurableIOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert False, "should not be called"

    class InputConfigSchema(dg.Config):
        config_value: int

    class MyInputManager(MyIOManager):
        def load_input(self, context):
            if context.upstream_output is None:
                assert False, "upstream output should not be None"
            else:
                return context.config["config_value"]

        @classmethod
        def input_config_schema(cls) -> type[dg.Config]:
            return InputConfigSchema

    did_run = {}

    @dg.op
    def first_op():
        did_run["first_op"] = True
        return 1

    @dg.op(ins={"an_input": dg.In(input_manager_key="my_input_manager")})
    def second_op(an_input):
        assert an_input == 6
        did_run["second_op"] = True

    @dg.job(
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

    with pytest.raises(dg.DagsterInvalidConfigError):
        check_input_managers.execute_in_process(
            run_config={
                "ops": {"second_op": {"inputs": {"an_input": {"config_value": "a_string"}}}}
            }
        )


def test_config_param_load_input_handle_output_config() -> None:
    storage = {}

    class InputConfigSchema(dg.Config):
        prefix_input: str

    class OutputConfigSchema(dg.Config):
        postfix_output: str

    class MyIOManager(dg.ConfigurableIOManager):
        prefix_output: str

        @classmethod
        def input_config_schema(cls) -> type[dg.Config]:
            return InputConfigSchema

        @classmethod
        def output_config_schema(cls) -> type[dg.Config]:
            return OutputConfigSchema

        def load_input(self, context: InputContext):
            return f"{context.config['prefix_input']}{storage[context.name]}"

        def handle_output(self, context: OutputContext, obj: str):
            storage[context.name] = f"{self.prefix_output}{obj}{context.config['postfix_output']}"

    did_run = {}

    @dg.op(out={"first_op": dg.Out(io_manager_key="io_manager")})
    def first_op():
        did_run["first_op"] = True
        return "foo"

    @dg.op(
        ins={"first_op": dg.In(input_manager_key="io_manager")},
        out={"second_op": dg.Out(io_manager_key="io_manager")},
    )
    def second_op(first_op):
        assert first_op == "barprefoopost"
        did_run["second_op"] = True
        return first_op

    @dg.job(
        resource_defs={
            "io_manager": MyIOManager(
                prefix_output="pre",
            ),
        }
    )
    def check_input_managers():
        out = first_op()
        second_op(out)

    check_input_managers.execute_in_process(
        run_config={
            "ops": {
                "first_op": {"outputs": {"first_op": {"postfix_output": "post"}}},
                "second_op": {
                    "inputs": {"first_op": {"prefix_input": "bar"}},
                    "outputs": {"second_op": {"postfix_output": "post"}},
                },
            }
        }
    )
    assert did_run["first_op"]
    assert did_run["second_op"]
    assert storage["first_op"] == "prefoopost"
    assert storage["second_op"] == "prebarprefoopostpost"


def test_io_manager_def() -> None:
    with tempfile.TemporaryDirectory() as tmpdir_path:

        @dg.asset(io_manager_def=dg.FilesystemIOManager(base_dir=tmpdir_path))
        def hello_world_asset():
            return "hello, world!"

        defs = dg.Definitions(
            assets=[hello_world_asset],
        )

        assert not os.path.exists(os.path.join(tmpdir_path, "hello_world_asset"))
        assert defs.resolve_implicit_global_asset_job_def().execute_in_process().success
        assert os.path.exists(os.path.join(tmpdir_path, "hello_world_asset"))


def test_observable_source_asset_io_manager_def() -> None:
    class FileStringIOManager(dg.ConfigurableIOManager):
        base_path: str

        def load_input(self, context: "InputContext") -> object:
            with open(
                os.path.join(self.base_path, "/".join(context.asset_key.path)),
                encoding="utf-8",
            ) as ff:
                return str(ff.read())

        def handle_output(self, context: "OutputContext", obj: Any) -> None:
            with open(
                os.path.join(self.base_path, "/".join(context.asset_key.path)),
                mode="w",
                encoding="utf-8",
            ) as ff:
                ff.write(str(obj))

    with tempfile.TemporaryDirectory() as tmpdir_path:
        with open(os.path.join(tmpdir_path, "my_observable_asset"), "w") as f:
            f.write("foo")

        # we never actually observe this asset, we just attach the io manager to it
        # to verify that any downstream assets that depend on it will use the right io manager
        @dg.observable_source_asset(io_manager_def=FileStringIOManager(base_path=tmpdir_path))
        def my_observable_asset() -> dg.DataVersion:
            return dg.DataVersion("alpha")

        @dg.asset
        def my_downstream_asset(my_observable_asset: str) -> str:
            return my_observable_asset + "bar"

        defs = dg.Definitions(
            assets=[my_observable_asset, my_downstream_asset],
        )

        result = defs.resolve_implicit_global_asset_job_def().execute_in_process()
        assert result.success
        assert result.output_for_node("my_downstream_asset") == "foobar"


def test_telemetry_custom_io_manager():
    class MyIOManager(dg.ConfigurableIOManager):
        def handle_output(self, context, obj):  # pyright: ignore[reportIncompatibleMethodOverride]
            return {}

        def load_input(self, context):
            return 1

    assert not MyIOManager._is_dagster_maintained()  # noqa: SLF001


def test_telemetry_dagster_io_manager():
    class MyIOManager(dg.ConfigurableIOManager):
        @classmethod
        def _is_dagster_maintained(cls) -> bool:
            return True

        def handle_output(self, context, obj):  # pyright: ignore[reportIncompatibleMethodOverride]
            return {}

        def load_input(self, context):
            return 1

    assert MyIOManager()._is_dagster_maintained()  # noqa: SLF001


def test_telemetry_custom_io_manager_factory():
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):  # pyright: ignore[reportIncompatibleMethodOverride]
            return {}

        def load_input(self, context):
            return 1

    class AnIOManagerFactory(dg.ConfigurableIOManagerFactory):
        def create_io_manager(self, _) -> dg.IOManager:  # pyright: ignore[reportIncompatibleMethodOverride]
            return MyIOManager()

    assert not AnIOManagerFactory()._is_dagster_maintained()  # noqa: SLF001


def test_telemetry_dagster_io_manager_factory():
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):  # pyright: ignore[reportIncompatibleMethodOverride]
            return {}

        def load_input(self, context):
            return 1

    class AnIOManagerFactory(dg.ConfigurableIOManagerFactory):
        @classmethod
        def _is_dagster_maintained(cls) -> bool:
            return True

        def create_io_manager(self, _) -> dg.IOManager:  # pyright: ignore[reportIncompatibleMethodOverride]
            return MyIOManager()

    assert AnIOManagerFactory()._is_dagster_maintained()  # noqa: SLF001


def test_inherited_io_config_schemas() -> None:
    files = {}

    class MyIOManager(dg.IOManager):
        def __init__(self, base_path) -> None:
            self._base_path = base_path

        def handle_output(self, context: OutputContext, obj):
            file_path = self._base_path + context.config["file_name"]
            files[file_path] = obj

        def load_input(self, context: InputContext):
            if context.upstream_output:
                file_path = self._base_path + context.upstream_output.config["file_name"]
                return files[file_path]

    class MyIOManagerOutputConfigSchema(dg.Config):
        file_name: str

    class MyConfigurableIOManager(dg.ConfigurableIOManagerFactory):
        base_path: str

        def create_io_manager(self, context) -> dg.IOManager:
            return MyIOManager(self.base_path)

        @classmethod
        def output_config_schema(cls) -> MyIOManagerOutputConfigSchema:  # pyright: ignore[reportIncompatibleMethodOverride]
            return MyIOManagerOutputConfigSchema

    @dg.op
    def op_1() -> str:
        return "output 1"

    @dg.op
    def op_2(input_data) -> str:
        assert input_data == "output 1"
        return "output 2"

    @dg.job
    def my_job():
        op_2(op_1())

    defs = dg.Definitions(
        resources={"io_manager": MyConfigurableIOManager(base_path="my-bucket/")},
        jobs=[my_job],
    )
    defs.resolve_job_def("my_job").execute_in_process(
        run_config={
            "ops": {
                "op_1": {"outputs": {"result": {"file_name": "table1"}}},
                "op_2": {"outputs": {"result": {"file_name": "table2"}}},
            }
        },
    )
    assert files == {
        "my-bucket/table1": "output 1",
        "my-bucket/table2": "output 2",
    }
