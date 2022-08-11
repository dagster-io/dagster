from dagstermill import define_dagstermill_op

from dagster import job

hello_world_notebook_op = define_dagstermill_op(
    name="hello_world_notebook_op", notebook_path="hello_world.ipynb"
)


@job
def hello_world_notebook_job():
    hello_world_notebook_op()
