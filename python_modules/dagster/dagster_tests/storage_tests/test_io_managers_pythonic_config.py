import os
import tempfile

from dagster import Definitions, FilesystemIOManager, In, RunConfig, asset, job, op
from dagster._config.pythonic_config import ConfigurableIOManager, ConfigurableResource


def test_load_input_handle_output():
    class MyIOManager(ConfigurableIOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert False, "should not be called"

    class MyInputManager(MyIOManager):
        def load_input(self, context):
            if context.upstream_output is None:
                assert False, "upstream output should not be None"
            else:
                return 6

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

    check_input_managers.execute_in_process()
    assert did_run["first_op"]
    assert did_run["second_op"]


def test_runtime_config():
    out_txt = []

    class MyIOManager(ConfigurableIOManager):
        prefix: str

        def handle_output(self, context, obj):
            out_txt.append(f"{self.prefix}{obj}")

        def load_input(self, context):
            assert False, "should not be called"

    @asset
    def hello_world_asset():
        return "hello, world!"

    defs = Definitions(
        assets=[hello_world_asset],
        resources={"io_manager": MyIOManager.configure_at_launch()},
    )

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process({"resources": {"io_manager": {"config": {"prefix": ""}}}})
        .success
    )
    assert out_txt == ["hello, world!"]

    out_txt.clear()

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process({"resources": {"io_manager": {"config": {"prefix": "greeting: "}}}})
        .success
    )
    assert out_txt == ["greeting: hello, world!"]


def test_nested_resources():
    out_txt = []

    class IOConfigResource(ConfigurableResource):
        prefix: str

    class MyIOManager(ConfigurableIOManager):
        config: IOConfigResource

        def handle_output(self, context, obj):
            out_txt.append(f"{self.config.prefix}{obj}")

        def load_input(self, context):
            assert False, "should not be called"

    @asset
    def hello_world_asset():
        return "hello, world!"

    defs = Definitions(
        assets=[hello_world_asset],
        resources={
            "io_manager": MyIOManager(config=IOConfigResource(prefix="greeting: ")),
        },
    )

    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
    assert out_txt == ["greeting: hello, world!"]


def test_nested_resources_runtime_config():
    out_txt = []

    class IOConfigResource(ConfigurableResource):
        prefix: str

    class MyIOManager(ConfigurableIOManager):
        config: IOConfigResource

        def handle_output(self, context, obj):
            out_txt.append(f"{self.config.prefix}{obj}")

        def load_input(self, context):
            assert False, "should not be called"

    @asset
    def hello_world_asset():
        return "hello, world!"

    io_config = IOConfigResource.configure_at_launch()

    defs = Definitions(
        assets=[hello_world_asset],
        resources={
            "io_config": io_config,
            "io_manager": MyIOManager(config=io_config),
        },
    )

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process({"resources": {"io_config": {"config": {"prefix": ""}}}})
        .success
    )
    assert out_txt == ["hello, world!"]

    out_txt.clear()

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process({"resources": {"io_config": {"config": {"prefix": "greeting: "}}}})
        .success
    )
    assert out_txt == ["greeting: hello, world!"]


def test_pythonic_fs_io_manager() -> None:
    with tempfile.TemporaryDirectory() as tmpdir_path:

        @asset
        def hello_world_asset():
            return "hello, world!"

        defs = Definitions(
            assets=[hello_world_asset],
            resources={"io_manager": FilesystemIOManager(base_dir=tmpdir_path)},
        )

        assert not os.path.exists(os.path.join(tmpdir_path, "hello_world_asset"))
        assert defs.get_implicit_global_asset_job_def().execute_in_process().success
        assert os.path.exists(os.path.join(tmpdir_path, "hello_world_asset"))


def test_pythonic_fs_io_manager_runtime_config() -> None:
    with tempfile.TemporaryDirectory() as tmpdir_path:

        @asset
        def hello_world_asset():
            return "hello, world!"

        defs = Definitions(
            assets=[hello_world_asset],
            resources={"io_manager": FilesystemIOManager.configure_at_launch()},
        )

        assert not os.path.exists(os.path.join(tmpdir_path, "hello_world_asset"))
        assert (
            defs.get_implicit_global_asset_job_def()
            .execute_in_process(
                run_config=RunConfig(
                    resources={"io_manager": FilesystemIOManager(base_dir=tmpdir_path)}
                )
            )
            .success
        )
        assert os.path.exists(os.path.join(tmpdir_path, "hello_world_asset"))
