from dagster.api.notebook_data import sync_get_streaming_external_notebook_data_grpc
from dagster.utils import file_relative_path

from .utils import get_bar_repo_handle


def test_external_notebook_grpc():
    notebook_path = file_relative_path(__file__, "foo.ipynb")
    with get_bar_repo_handle() as repository_handle:
        api_client = repository_handle.repository_location.client

        result = sync_get_streaming_external_notebook_data_grpc(
            api_client, notebook_path=notebook_path
        )
        content = result.content
        assert isinstance(content, bytes)
        with open(notebook_path, "rb") as f:
            assert content == f.read()
