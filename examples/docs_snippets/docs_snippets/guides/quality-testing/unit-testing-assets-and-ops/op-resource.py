from unittest import mock

from dagster_aws.s3 import S3FileHandle, S3FileManager
from my_project.defs.assets import load_file

import dagster as dg


# highlight-start
def test_load_file() -> None:
    mocked_resource = mock.Mock(spec=S3FileManager)
    mocked_resource.read_data.return_value = "contents"

    assert load_file(mocked_resource) == "contents"
    assert mocked_resource.read_data.called_once_with(
        S3FileHandle("bucket", "path.txt")
    )
    # highlight-end
