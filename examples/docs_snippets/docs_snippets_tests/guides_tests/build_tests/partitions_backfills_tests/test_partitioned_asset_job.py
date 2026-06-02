from docs_snippets.guides.build.partitions_backfills.partitioned_asset_job import defs


def test():
    assert defs.get_job_def("asset_1_and_2_job")
