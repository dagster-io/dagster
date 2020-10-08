import pytest
import yaml
from docs_snippets.overview.logging.builtin_logger import demo_pipeline
from docs_snippets.overview.logging.builtin_logger_error import demo_pipeline_error
from docs_snippets.overview.logging.logging_modes import hello_modes

from dagster import execute_pipeline
from dagster.utils import file_relative_path


def test_demo_pipeline():
    assert execute_pipeline(demo_pipeline).success


def test_demo_pipeline_config():
    with open(
        file_relative_path(__file__, "../../../docs_snippets/overview/logging/config.yaml"), "r"
    ) as fd:
        run_config = yaml.safe_load(fd.read())
    assert execute_pipeline(demo_pipeline, run_config=run_config).success


def test_demo_pipeline_error():
    with pytest.raises(Exception) as exc_info:
        execute_pipeline(demo_pipeline_error)
    assert str(exc_info.value) == "Somebody set up us the bomb"


def test_hello_modes():
    assert execute_pipeline(hello_modes, mode="local").success
