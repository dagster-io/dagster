from tempfile import TemporaryDirectory

from dagster import execute_pipeline
from docs_snippets.overview.io_managers.default_io_manager import my_pipeline


def test_default_io_manager():
    with TemporaryDirectory() as tmpdir:
        execute_pipeline(
            my_pipeline,
            run_config={"resources": {"io_manager": {"config": {"base_dir": tmpdir}}}},
        )
