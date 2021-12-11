from dagster import pipeline
from dagster.utils import file_relative_path
from dagstermill import define_dagstermill_solid

hello_world_notebook_solid = define_dagstermill_solid(
    "hello_world_notebook_solid",
    file_relative_path(__file__, "hello_world.ipynb"),
)


@pipeline
def hello_world_notebook_pipeline():
    hello_world_notebook_solid()
