from dagster._utils import script_relative_path

# isort: split
# start

import dagstermill as dm

from dagster import Field, In, Int, job
from docs_snippets.legacy.data_science.download_file import download_file

k_means_iris = dm.define_dagstermill_op(
    "k_means_iris",
    script_relative_path("iris-kmeans_2.ipynb"),
    output_notebook_name="iris_kmeans_output",
    ins={"path": In(str, description="Local path to the Iris dataset")},
    config_schema=Field(
        Int,
        default_value=3,
        is_required=False,
        description="The number of clusters to find",
    ),
)


@job(
    resource_defs={
        "output_notebook_io_manager": dm.local_output_notebook_io_manager,
    }
)
def iris_classify():
    k_means_iris(download_file())
