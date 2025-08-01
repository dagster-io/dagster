from docs_snippets.guides.dagster.enriching_with_software_defined_assets.sda_graph import (
    defs,
)


def test_sda_graph() -> None:
    assert (
        defs.resolve_job_def("products_and_categories_job").execute_in_process().success
    )
