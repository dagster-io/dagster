from docs_snippets.concepts.io_management.custom_io_manager import (  # pylint: disable=E0401
    my_job,
    my_job_with_metadata,
)


def test_custom_io_manager():
    my_job.execute_in_process()


def test_custom_io_manager_with_metadata():
    my_job_with_metadata.execute_in_process()
