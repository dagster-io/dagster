import dagstermill as dm

from dagster import pipeline
from dagster.utils import script_relative_path

k_means_iris = dm.define_dagstermill_solid(
    "k_means_iris", script_relative_path("iris-kmeans.ipynb")
)


@pipeline
def iris_pipeline():
    k_means_iris()
