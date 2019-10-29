'''isort:skip_file'''

import sys

from dagster import RepositoryDefinition
from dagster.utils import script_relative_path

sys.path.append(script_relative_path('.'))

from hello_cereal import hello_cereal_pipeline
from complex_pipeline import complex_pipeline


def define_repo():
    return RepositoryDefinition(
        name='hello_cereal_repository',
        # Note that we can pass a function, rather than pipeline instance.
        # This allows us to construct pipelines lazily, if, e.g.,
        # initializing a pipeline involves any heavy compute
        pipeline_dict={
            'hello_cereal_pipeline': lambda: hello_cereal_pipeline,
            'complex_pipeline': lambda: complex_pipeline,
        },
    )
