import os
import sys
from dagster import RepositoryDefinition
from dagster.utils import script_relative_path

sys.path.insert(0, os.path.abspath(script_relative_path('.')))
# above confuses pylint
# pylint: disable=wrong-import-position, import-error

from error_monster import define_pipeline
from sleepy import define_sleepy_pipeline
from log_spew import define_spew_pipeline


def define_repo():
    return RepositoryDefinition(
        name='toys_repository',
        pipeline_dict={
            'sleepy': define_sleepy_pipeline,
            'error_monster': define_pipeline,
            'log_spew': define_spew_pipeline,
        },
    )
