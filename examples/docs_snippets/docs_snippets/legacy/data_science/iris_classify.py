from dagster._utils import script_relative_path

# isort: split
# start

import dagstermill as dm

from dagster import job

k_means_iris = dm.define_dagstermill_op(
    "k_means_iris",
    script_relative_path("iris-kmeans.ipynb"),
    output_notebook_name="iris_kmeans_output",
)


@job(
    resource_defs={
        "output_notebook_io_manager": dm.local_output_notebook_io_manager,
    }
)
def iris_classify():
    k_means_iris()
