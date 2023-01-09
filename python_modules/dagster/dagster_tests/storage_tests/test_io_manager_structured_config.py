# pylint: disable=unused-argument

from dagster import Definitions, In, asset, job, op
from dagster._config.structured_config import StructuredConfigIOManager


def test_load_input_handle_output():
    class MyIOManager(StructuredConfigIOManager):
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


def test_structured_resource_runtime_config():
    out_txt = []

    class MyIOManager(StructuredConfigIOManager):
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
        resources={"io_manager": MyIOManager},
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
