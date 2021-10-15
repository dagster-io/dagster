from tempfile import TemporaryDirectory

from docs_snippets_crag.concepts.io_management.default_io_manager import my_job


def test_default_io_manager():
    with TemporaryDirectory() as tmpdir:
        my_job.execute_in_process(
            run_config={"resources": {"io_manager": {"config": {"base_dir": tmpdir}}}},
        )
