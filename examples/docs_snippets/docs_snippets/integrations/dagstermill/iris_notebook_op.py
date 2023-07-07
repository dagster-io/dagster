# ruff: isort: split
# start

from dagstermill import ConfigurableLocalOutputNotebookIOManager, define_dagstermill_op

from dagster import file_relative_path, job

k_means_iris = define_dagstermill_op(
    name="k_means_iris",
    notebook_path=file_relative_path(__file__, "./notebooks/iris-kmeans.ipynb"),
    output_notebook_name="iris_kmeans_output",
)


@job(
    resource_defs={
        "output_notebook_io_manager": ConfigurableLocalOutputNotebookIOManager(),
    }
)
def iris_classify():
    k_means_iris()
