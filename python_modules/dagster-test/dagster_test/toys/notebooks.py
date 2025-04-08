from dagster import job, op

try:
    from dagstermill.factory import define_dagstermill_op

    hello_world_notebook_op = define_dagstermill_op("hello_world_notebook_op", "hello_world.ipynb")
except ImportError:

    @op(name="hello_world_notebook_op")
    def mock_notebook_op():
        return None

    hello_world_notebook_op = mock_notebook_op


@job
def hello_world_notebook_pipeline():
    hello_world_notebook_op()
