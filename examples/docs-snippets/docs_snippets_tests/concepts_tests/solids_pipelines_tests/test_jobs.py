from docs_snippets.concepts.solids_pipelines.jobs import do_it_all
from docs_snippets.concepts.solids_pipelines.jobs_with_config_mapping import (
    do_it_all_with_simplified_config,
)
from docs_snippets.concepts.solids_pipelines.jobs_with_default_config import (
    do_it_all_with_default_config,
)


def test_do_it_all_job():
    do_it_all.execute_in_process()


def test_do_it_all_with_default_config():
    do_it_all_with_default_config.execute_in_process()


def test_do_it_all_with_simplified_config():
    do_it_all_with_simplified_config.execute_in_process(run_config={"simplified_param": "stuff"})
