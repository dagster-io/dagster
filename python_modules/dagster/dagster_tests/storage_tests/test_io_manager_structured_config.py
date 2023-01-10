# pylint: disable=unused-argument

from dagster import Definitions, In, asset, job, op
from dagster._config.structured_config import (
    Config,
    RequiresResources,
    Resource,
    StructuredConfigIOManager,
)
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.execution.context.input import InputContext
from dagster._core.execution.context.output import OutputContext
from dagster._core.storage.io_manager import IOManager


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


def test_multiple_similar_resource_deps():
    out_txt = []

    class AWSCredentialsResource(Resource):
        username: str
        password: str

    class AWSDeps(Config):
        aws_credentials: AWSCredentialsResource

    class S3IOManager(StructuredConfigIOManager, RequiresResources[AWSDeps]):
        bucket_name: str

        def handle_output(self, context, obj):
            assert self.required_resources.aws_credentials.username == "foo"
            assert self.required_resources.aws_credentials.password == "bar"
            out_txt.append(f"{self.bucket_name}: {obj}")

        def load_input(self, context):
            assert False, "should not be called"

    @asset
    def my_asset():
        return "hello, world"

    defs = Definitions(
        assets=[my_asset],
        resources={
            "aws_credentials": AWSCredentialsResource(username="foo", password="bar"),
            "io_manager": S3IOManager,
        },
    )

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process(
            {
                "resources": {
                    "io_manager": {"config": {"bucket_name": "my_bucket"}},
                }
            }
        )
        .success
    )
    assert out_txt == ["my_bucket: hello, world"]


def test_io_manager_resource_deps():
    prod_data_store = {}
    staging_data_store = {}

    class MyProdIOManager(StructuredConfigIOManager):
        def handle_output(self, context: OutputContext, obj):
            prod_data_store[context.name] = obj

        def load_input(self, context: InputContext):
            return prod_data_store.get(context.name)

    class MyStagingIOManager(StructuredConfigIOManager):
        def handle_output(self, context: OutputContext, obj):
            staging_data_store[context.name] = obj

        def load_input(self, context: InputContext):
            return staging_data_store.get(context.name)

    class BranchingIOManagerDeps(Config):
        prod_io_manager: IOManager
        staging_io_manager: IOManager

    class BranchingIOManager(StructuredConfigIOManager, RequiresResources[BranchingIOManagerDeps]):
        def handle_output(self, context: OutputContext, obj):
            self.required_resources.staging_io_manager.handle_output(context, obj)

        def load_input(self, context: InputContext):
            staging_value = self.required_resources.staging_io_manager.load_input(context)
            if staging_value is not None:
                return staging_value

            return self.required_resources.prod_io_manager.load_input(context)

    @asset
    def hello_world():
        return "hello, world, in staging this time"

    @asset
    def hello_world_capitalized(hello_world: str):
        return hello_world.capitalize()

    hello_world_capitalized_job = define_asset_job(
        name="hello_world_capitalized_job", selection="hello_world_capitalized"
    )

    prod_data_store["hello_world"] = "hello, world"

    defs = Definitions(
        assets=[hello_world, hello_world_capitalized],
        jobs=[hello_world_capitalized_job],
        resources={
            "prod_io_manager": MyProdIOManager(),
            "staging_io_manager": MyStagingIOManager(),
            "io_manager": BranchingIOManager(),
        },
    )

    assert defs.get_job_def("hello_world_capitalized_job").execute_in_process().success
    assert staging_data_store["result"] == "Hello, world"

    staging_data_store["hello_world"] = "hello, world, in staging this time"

    assert defs.get_job_def("hello_world_capitalized_job").execute_in_process().success
    assert staging_data_store["result"] == "Hello, world, in staging this time"
