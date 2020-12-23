from tempfile import TemporaryDirectory

from dagster import execute_pipeline
from docs_snippets.overview.object_managers.default_object_manager import my_pipeline


def test_default_object_manager():
    with TemporaryDirectory() as tmpdir:
        execute_pipeline(
            my_pipeline,
            run_config={"resources": {"object_manager": {"config": {"base_dir": tmpdir}}}},
        )
