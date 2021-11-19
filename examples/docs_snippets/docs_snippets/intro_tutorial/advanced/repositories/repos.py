from dagster import repository

from .complex_job import complex_job
from .hello_cereal import hello_cereal_job


# start_repos_marker_0
@repository
def hello_cereal_repository():
    return [hello_cereal_job, complex_job]


# end_repos_marker_0
