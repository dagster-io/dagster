from dagstermill import define_dagstermill_solid

from dagster._legacy import pipeline

hello_world_notebook_solid = define_dagstermill_solid(
    "hello_world_notebook_solid", "hello_world.ipynb"
)


@pipeline
def hello_world_notebook_pipeline():
    hello_world_notebook_solid()
