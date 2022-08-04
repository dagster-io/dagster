import tempfile

import yaml

from dagster._utils import file_relative_path
from docs_snippets.concepts.configuration.make_values_resource_any import file_dir_job
from docs_snippets.concepts.configuration.make_values_resource_config_schema import (
    file_dirs_job,
)


def test_make_values_resource_any():
    with tempfile.TemporaryDirectory() as tmp_dir:
        run_config = {
            "resources": {
                "file_dir": {
                    "config": tmp_dir,
                }
            }
        }

        assert file_dir_job.execute_in_process(run_config=run_config).success


def test_make_values_resource_config_schema():
    with tempfile.TemporaryDirectory() as tmp_dir:
        run_config = {
            "resources": {
                "file_dirs": {
                    "config": {
                        "write_file_dir": tmp_dir,
                        "count_file_dir": tmp_dir,
                    }
                }
            }
        }
        assert file_dirs_job.execute_in_process(run_config=run_config).success
