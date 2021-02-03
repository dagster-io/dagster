from tempfile import TemporaryDirectory

from dagster import execute_pipeline
from docs_snippets.overview.io_managers.io_manager_per_output import my_pipeline


def test_io_manager_per_output():
    with TemporaryDirectory() as tmpdir:
        execute_pipeline(
            my_pipeline,
            run_config={"resources": {"fs": {"config": {"base_dir": tmpdir}}}},
        )
