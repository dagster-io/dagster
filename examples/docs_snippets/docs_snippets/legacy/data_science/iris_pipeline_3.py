import dagstermill as dm
from docs_snippets.legacy.data_science.download_file import download_file

from dagster import Field, InputDefinition, Int, pipeline
from dagster.utils import script_relative_path

k_means_iris = dm.define_dagstermill_solid(
    "k_means_iris",
    script_relative_path("iris-kmeans_2.ipynb"),
    input_defs=[InputDefinition("path", str, description="Local path to the Iris dataset")],
    config_schema=Field(
        Int, default_value=3, is_required=False, description="The number of clusters to find"
    ),
)


@pipeline
def iris_pipeline():
    k_means_iris(download_file())
