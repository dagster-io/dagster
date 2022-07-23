import pytest

from dagster import file_relative_path


@pytest.fixture
def docs_snippets_folder():
    return file_relative_path(__file__, "../docs_snippets/")
