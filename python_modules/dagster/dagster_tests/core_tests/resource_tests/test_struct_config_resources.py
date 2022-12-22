from dagster import job, op
from dagster._config.structured_config import Resource


def test_basic_structured_resource():

    out_txt = []

    class WriterResource(Resource):
        prefix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}")

    @op
    def hello_world_op(writer: WriterResource):
        writer.output("hello, world!")

    @job(resource_defs={"writer": WriterResource(prefix="")})
    def no_prefix_job():
        hello_world_op()

    assert no_prefix_job.execute_in_process().success
    assert out_txt == ["hello, world!"]

    out_txt.clear()

    @job(resource_defs={"writer": WriterResource(prefix="greeting: ")})
    def prefix_job():
        hello_world_op()

    assert prefix_job.execute_in_process().success
    assert out_txt == ["greeting: hello, world!"]
