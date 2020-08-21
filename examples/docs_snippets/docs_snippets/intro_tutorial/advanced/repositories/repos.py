"""isort:skip_file"""

import sys

from dagster import repository
from dagster.utils import script_relative_path

sys.path.append(script_relative_path("."))

from hello_cereal import hello_cereal_pipeline
from complex_pipeline import complex_pipeline


@repository
def hello_cereal_repository():
    return [hello_cereal_pipeline, complex_pipeline]
