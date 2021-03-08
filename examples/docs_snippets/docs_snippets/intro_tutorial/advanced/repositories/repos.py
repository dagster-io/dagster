from dagster import repository

from .complex_pipeline import complex_pipeline
from .hello_cereal import hello_cereal_pipeline


# start_repos_marker_0
@repository
def hello_cereal_repository():
    return [hello_cereal_pipeline, complex_pipeline]


# end_repos_marker_0
