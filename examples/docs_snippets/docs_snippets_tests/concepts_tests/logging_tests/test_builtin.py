import pytest
import yaml

from dagster.utils import file_relative_path
from docs_snippets.concepts.logging.builtin_logger import demo_job, demo_job_error
from docs_snippets.concepts.logging.logging_jobs import local_logs, prod_logs


def test_demo_job():
    assert demo_job.execute_in_process().success


def test_demo_job_config():
    with open(
        file_relative_path(
            __file__, "../../../docs_snippets/concepts/logging/config.yaml"
        ),
        "r",
        encoding="utf-8",
    ) as fd:
        run_config = yaml.safe_load(fd.read())
    assert demo_job.execute_in_process(run_config=run_config).success


def test_demo_job_error():
    with pytest.raises(Exception) as exc_info:
        demo_job_error.execute_in_process()
    assert str(exc_info.value) == "Somebody set up us the bomb"


def test_local_and_prod_jobs():
    assert local_logs.execute_in_process().success
    assert prod_logs.execute_in_process().success
