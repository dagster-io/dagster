import dagster as dg
from docs_snippets.concepts.assets.build_job import (
    all_assets_job,
    shopping_list,
    sugary_cereals,
    sugary_cereals_job,
)


def test_build_job_doc_snippet():
    defs = dg.Definitions(
        assets=[sugary_cereals, shopping_list],
        jobs=[all_assets_job, sugary_cereals_job],
    )

    assert defs.get_job_def("all_assets_job").execute_in_process().success
    assert defs.get_job_def("sugary_cereals_job").execute_in_process().success
