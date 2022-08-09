from dagstermill.factory import define_dagstermill_op

from dagster._legacy import pipeline

hello_world_notebook_op = define_dagstermill_op("hello_world_notebook_op", "hello_world.ipynb")


@pipeline
def hello_world_notebook_pipeline():
    hello_world_notebook_op()
