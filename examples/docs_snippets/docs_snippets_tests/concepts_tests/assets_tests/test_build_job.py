from docs_snippets.concepts.assets.build_job import (
    all_assets,
    downstream_assets,
    upstream_and_downstream_1,
)


def test_jobs():
    all_assets.execute_in_process()
    downstream_assets.execute_in_process()
    upstream_and_downstream_1.execute_in_process()
