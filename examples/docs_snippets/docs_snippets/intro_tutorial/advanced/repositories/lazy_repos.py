"""isort:skip_file"""

import sys

from dagster import repository
from dagster.utils import script_relative_path

sys.path.append(script_relative_path("."))

from hello_cereal import hello_cereal_pipeline
from complex_pipeline import complex_pipeline


# start_lazy_repos_marker_0
@repository
def hello_cereal_repository():
    # Note that we can pass a dict of functions, rather than a list of
    # pipeline definitions. This allows us to construct pipelines lazily,
    # if, e.g., initializing a pipeline involves any heavy compute
    return {
        "pipelines": {
            "hello_cereal_pipeline": lambda: hello_cereal_pipeline,
            "complex_pipeline": lambda: complex_pipeline,
        }
    }


# end_lazy_repos_marker_0
