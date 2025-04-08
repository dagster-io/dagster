from dagster import job

try:
    from dagstermill.factory import define_dagstermill_op

    hello_world_notebook_op = define_dagstermill_op("hello_world_notebook_op", "hello_world.ipynb")
except ImportError:
    hello_world_notebook_op = lambda: None


@job
def hello_world_notebook_pipeline():
    hello_world_notebook_op()
