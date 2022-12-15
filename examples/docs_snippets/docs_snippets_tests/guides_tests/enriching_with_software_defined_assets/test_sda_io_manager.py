from docs_snippets.guides.dagster.enriching_with_software_defined_assets.sda_io_manager import (
    defs,
)


def test_sda_nothing():
    assert defs.get_job_def("users_recommender_job").execute_in_process().success
