from dagster._api.notebook_data import sync_get_streaming_external_notebook_data_grpc
from dagster._utils import file_relative_path

from dagster_tests.api_tests.utils import get_bar_repo_code_location


def test_external_notebook_grpc(instance):
    notebook_path = file_relative_path(__file__, "foo.ipynb")
    with get_bar_repo_code_location(instance) as code_location:
        api_client = code_location.client

        content = sync_get_streaming_external_notebook_data_grpc(
            api_client, notebook_path=notebook_path
        )
        assert isinstance(content, bytes)
        with open(notebook_path, "rb") as f:
            assert content == f.read()
