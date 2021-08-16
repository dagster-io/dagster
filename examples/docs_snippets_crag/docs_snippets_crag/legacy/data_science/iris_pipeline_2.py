import dagstermill as dm
from dagster import InputDefinition, ModeDefinition, fs_io_manager, pipeline
from dagster.utils import script_relative_path
from docs_snippets_crag.legacy.data_science.download_file import download_file

k_means_iris = dm.define_dagstermill_solid(
    "k_means_iris",
    script_relative_path("iris-kmeans_2.ipynb"),
    input_defs=[InputDefinition("path", str, description="Local path to the Iris dataset")],
)


@pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": fs_io_manager})])
def iris_pipeline():
    k_means_iris(download_file())
