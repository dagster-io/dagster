import yaml
from dagster import execute_pipeline
from dagster.utils import file_relative_path
from docs_snippets_crag.concepts.logging.custom_logger import (
    demo_pipeline,
    test_init_json_console_logger,
    test_init_json_console_logger_with_context,
)


def test_json_logger():
    with open(
        file_relative_path(
            __file__, "../../../docs_snippets_crag/concepts/logging/config_custom_logger.yaml"
        ),
        "r",
    ) as fd:
        run_config = yaml.safe_load(fd.read())
    assert execute_pipeline(demo_pipeline, run_config=run_config).success


def test_testing_examples():
    test_init_json_console_logger()
    test_init_json_console_logger_with_context()
