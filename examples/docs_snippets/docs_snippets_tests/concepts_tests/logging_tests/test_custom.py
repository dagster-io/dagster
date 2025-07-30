import yaml

from dagster._utils import file_relative_path
from docs_snippets.concepts.logging.custom_logger import (
    defs,
    demo_job,
    json_console_logger,
    test_init_json_console_logger,
    test_init_json_console_logger_with_context,
)


def test_json_logger():
    with open(
        file_relative_path(
            __file__,
            "../../../docs_snippets/concepts/logging/config_custom_logger.yaml",
        ),
        encoding="utf8",
    ) as fd:
        run_config = yaml.safe_load(fd.read())
    assert demo_job.execute_in_process(run_config=run_config).success


def test_testing_examples():
    test_init_json_console_logger()
    test_init_json_console_logger_with_context()


def test_default_logger_repo_example():
    assert defs.get_job_def("the_job").loggers == {"json_logger": json_console_logger}
