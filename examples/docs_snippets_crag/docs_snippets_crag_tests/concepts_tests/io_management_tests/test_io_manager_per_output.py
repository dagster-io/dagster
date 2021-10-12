from tempfile import TemporaryDirectory

from docs_snippets_crag.concepts.io_management.io_manager_per_output import my_job


def test_io_manager_per_output():
    with TemporaryDirectory() as tmpdir:
        my_job.execute_in_process(
            run_config={"resources": {"fs": {"config": {"base_dir": tmpdir}}}},
        )
