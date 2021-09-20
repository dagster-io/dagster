from dagster.api.notebook_data import sync_get_streaming_external_notebook_data_grpc
from dagster.utils import file_relative_path

from .utils import get_bar_repo_repository_location


def test_external_notebook_grpc():
    notebook_path = file_relative_path(__file__, "foo.ipynb")
    with get_bar_repo_repository_location() as repository_location:
        api_client = repository_location.client

        content = sync_get_streaming_external_notebook_data_grpc(
            api_client, notebook_path=notebook_path
        )
        assert isinstance(content, bytes)
        with open(notebook_path, "rb") as f:
            assert content == f.read()
