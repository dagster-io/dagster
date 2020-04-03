import dagstermill as dm
from dagster_examples.util import download_file

from dagster import DependencyDefinition, Field, InputDefinition, Int, Path, PipelineDefinition
from dagster.utils import script_relative_path

k_means_iris_solid = dm.define_dagstermill_solid(
    'k_means_iris',
    script_relative_path('iris-kmeans_2.ipynb'),
    input_defs=[InputDefinition('path', Path, description='Local path to the Iris dataset')],
    config=Field(
        Int, default_value=3, is_required=False, description='The number of clusters to find'
    ),
)


def define_iris_pipeline():
    return PipelineDefinition(
        name='iris_pipeline',
        solid_defs=[download_file, k_means_iris_solid],
        dependencies={'k_means_iris': {'path': DependencyDefinition('download_file', 'path')}},
    )
