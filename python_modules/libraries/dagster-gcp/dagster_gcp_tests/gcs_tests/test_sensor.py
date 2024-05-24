import time
from datetime import datetime
from typing import List, Optional
from unittest import mock

import pytest
from dagster_gcp.gcs.sensor import get_gcs_keys


@pytest.mark.parametrize(
    "test_name, since_key, blob_prefix, nb_bucket_keys, expected_keys",
    [
        ("no key in bucket", None, None, 0, []),
        ("one key in bucket", None, None, 1, ["foo-1"]),
        ("two keys in bucket with one key offset", "foo-1", None, 2, ["foo-2"]),
        ("three keys in bucket with wrong prefix", None, "bar", 3, []),
        ("three keys in bucket with correct prefix", None, "foo", 3, ["foo-1", "foo-2", "foo-3"]),
        (
            "a thousand keys in bucket with offset of -4",
            "foo-999",
            "",
            1003,
            ["foo-1000", "foo-1001", "foo-1002", "foo-1003"],
        ),
        ("two thousand keys in bucket with offset of -1", "foo-1199", None, 1200, ["foo-1200"]),
    ],
)
def test_get_gcs_keys(
    test_name: str,
    since_key: Optional[str],
    blob_prefix: Optional[str],
    nb_bucket_keys: int,
    expected_keys: List[str],
):
    bucket_name = "test-bucket"

    class Blob:
        def __init__(self, name, updated):
            self.name = name
            self.updated = updated

    now = time.time()
    bucket_keys = [
        Blob(name=f"foo-{i + 1}", updated=datetime.fromtimestamp(now - nb_bucket_keys + i))
        for i in range(nb_bucket_keys)
    ]

    class MockBlobIterator:
        """Mock the page iterator returned by google.cloud.storage.client.list_blobs."""

        def __init__(self, collection):
            self.collection = collection
            self.num_results = 0

        def __iter__(self):
            return self

        def __next__(self):
            if self.num_results < len(self.collection):
                self.num_results += 1
                return self.collection[self.num_results - 1]
            raise StopIteration

    def mock_list_blobs(bucket_or_name, prefix, **kwargs):
        """Mock the list_blobs method."""
        assert bucket_or_name == bucket_name, "bucket name should be the same"

        nonlocal bucket_keys
        returned_keys = []
        offset = 0
        for idx, key in enumerate(bucket_keys[offset:]):
            if not prefix or key.name.startswith(prefix):
                returned_keys.append(key)

        return MockBlobIterator(returned_keys)

    gcs_client = mock.MagicMock
    gcs_client.list_blobs = mock.Mock(side_effect=mock_list_blobs)

    keys = get_gcs_keys(
        bucket=bucket_name, prefix=blob_prefix, since_key=since_key, gcs_session=gcs_client
    )

    assert len(keys) == len(
        expected_keys
    ), f"{test_name}: {len(expected_keys)} key(s) should be returned"
    assert keys == expected_keys
    assert gcs_client.list_blobs.call_count == 1
