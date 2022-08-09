from dagstermill.factory import define_dagstermill_op

from dagster._legacy import pipeline
from dagster._utils import file_relative_path

hello_world_notebook_op = define_dagstermill_op(
    "hello_world_notebook_op",
    file_relative_path(__file__, "hello_world.ipynb"),
)


@pipeline
def hello_world_notebook_pipeline():
    hello_world_notebook_op()
