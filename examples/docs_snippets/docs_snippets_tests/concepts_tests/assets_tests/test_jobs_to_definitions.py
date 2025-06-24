import dagster as dg
from docs_snippets.concepts.assets.jobs_to_definitions import (
    number_asset,
    number_asset_job,
)


def test_build_job_doc_snippet():
    defs = dg.Definitions(
        assets=[number_asset],
        jobs=[number_asset_job],
    )

    assert defs.get_job_def("number_asset_job").execute_in_process().success
