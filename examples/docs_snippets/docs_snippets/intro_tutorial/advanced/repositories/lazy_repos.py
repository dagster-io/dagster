from dagster import repository

from .complex_job import complex_job
from .hello_cereal import hello_cereal_job


# start_lazy_repos_marker_0
@repository
def hello_cereal_repository():
    # Note that we can pass a dict of functions, rather than a list of
    # job definitions. This allows us to construct jobs lazily,
    # if, e.g., initializing a job involves any heavy compute
    return {
        "jobs": {
            "hello_cereal_job": lambda: hello_cereal_job,
            "complex_job": lambda: complex_job,
        }
    }


# end_lazy_repos_marker_0
