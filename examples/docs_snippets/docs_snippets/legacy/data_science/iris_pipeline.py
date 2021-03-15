import dagstermill as dm
from dagster import ModeDefinition, fs_io_manager, local_file_manager, pipeline
from dagster.utils import script_relative_path

k_means_iris = dm.define_dagstermill_solid(
    "k_means_iris", script_relative_path("iris-kmeans.ipynb")
)


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={"io_manager": fs_io_manager, "file_manager": local_file_manager}
        )
    ]
)
def iris_pipeline():
    k_means_iris()
