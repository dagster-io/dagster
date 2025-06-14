from docs_snippets.guides.dagster.enriching_with_software_defined_assets.sda_nothing import (
    defs,
)


def test_sda_nothing() -> None:
    assert defs.resolve_job_def("users_recommenders_job").execute_in_process().success
