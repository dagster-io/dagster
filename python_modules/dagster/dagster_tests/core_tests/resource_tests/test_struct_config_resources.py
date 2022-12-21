from dagster import (
    job,
    op,
)
from dagster._config.structured_config import StructuredConfigResource


def test_basic_structured_resource():

    output = []

    class WriterResource(StructuredConfigResource):
        prefix: str

        def output(self, text: str) -> None:
            output.append(f"{self.prefix}{text}")

    @op
    def hello_world_op(writer: WriterResource):
        writer.output("hello, world!")

    @job(resource_defs={"writer": WriterResource(prefix="")})
    def no_prefix_job():
        hello_world_op()

    assert no_prefix_job.execute_in_process().success
    assert output == ["hello, world!"]

    output.clear()

    @job(resource_defs={"writer": WriterResource(prefix="greeting: ")})
    def prefix_job():
        hello_world_op()

    assert prefix_job.execute_in_process().success
    assert output == ["greeting: hello, world!"]
