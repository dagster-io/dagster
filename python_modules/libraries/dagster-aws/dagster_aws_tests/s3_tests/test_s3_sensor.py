import time

import boto3
import pytest

from dagster_aws.s3.sensor import get_objects, get_s3_keys

BUCKET_NAME = "test-bucket"
PREFIX = "content"


def _put_object(client, bucket_name, prefix, key, body, delay=0) -> None:
    time.sleep(delay)
    r = client.put_object(Bucket=bucket_name, Key=f"{prefix}/{key}", Body=body)
    if not r:
        raise Exception("Failed to create object")


def test_get_s3_keys():
    s3_client = boto3.client("s3", region_name="us-east-1")
    response = s3_client.create_bucket(Bucket=BUCKET_NAME)
    if not response:
        raise Exception("Failed to create bucket")

    no_key = get_s3_keys(bucket=BUCKET_NAME, prefix=PREFIX)
    assert len(no_key) == 0  # no keys in bucket

    _put_object(
        client=s3_client,
        bucket_name=BUCKET_NAME,
        prefix=PREFIX,
        key="foo-1",
        body="test",
    )
    one_key = get_s3_keys(bucket=BUCKET_NAME, prefix=PREFIX)
    assert len(one_key) == 1

    _put_object(
        client=s3_client,
        bucket_name=BUCKET_NAME,
        prefix=PREFIX,
        key="foo-2",
        body="test",
    )
    two_keys = get_s3_keys(bucket=BUCKET_NAME, prefix=PREFIX)
    assert len(two_keys) == 2, "both keys should be returned"

    one_key_shift = get_s3_keys(bucket=BUCKET_NAME, prefix=PREFIX, since_key=two_keys[0])
    assert len(one_key_shift) == 1, "only one key should be returned"

    two_key_shift = get_s3_keys(bucket=BUCKET_NAME, prefix=PREFIX, since_key=two_keys[1])
    assert len(two_key_shift) == 0, "no keys should be returned"

    # test pagination
    for i in range(3, 1002):
        _put_object(
            client=s3_client,
            bucket_name=BUCKET_NAME,
            prefix=PREFIX,
            key=f"foo-{i}",
            body="test",
        )
    thousand_and_one_keys = get_s3_keys(bucket=BUCKET_NAME, prefix=PREFIX)
    assert len(thousand_and_one_keys) == 1001, "1001 keys should be returned"

    #  test pagination with since_key
    # keys are sorted by LastModified time, with a resolution of 1 second, so the key at index 999 will vary.
    # The test would be flaky if sorted was not guaranteed to be stable, which it is
    # according to: https://wiki.python.org/moin/HowTo/Sorting/.
    keys = get_s3_keys(bucket=BUCKET_NAME, prefix=PREFIX, since_key=thousand_and_one_keys[999])
    assert len(keys) == 1, "1 key should be returned"

    #  test pagination with since_key > 1000
    for i in range(1002, 1101):
        _put_object(
            client=s3_client,
            bucket_name=BUCKET_NAME,
            prefix=PREFIX,
            key=f"foo-{i}",
            body="test",
        )
    thousand_and_one_hundred_keys = get_s3_keys(bucket=BUCKET_NAME, prefix=PREFIX)
    assert len(thousand_and_one_hundred_keys) == 1100, "1100 keys should be returned"

    # keys are sorted by LastModified time, with a resolution of 1 second, so the key at index 999 will vary.
    # The test would be flaky if sorted was not guaranteed to be stable, which it is
    # according to: https://wiki.python.org/moin/HowTo/Sorting/.
    keys = get_s3_keys(
        bucket=BUCKET_NAME,
        prefix=PREFIX,
        since_key=thousand_and_one_hundred_keys[1090],
    )
    assert len(keys) == 9, "9 keys should be returned"


def test_get_s3_keys_missing_key_raises_exception():
    s3_client = boto3.client("s3", region_name="us-east-1")
    response = s3_client.create_bucket(Bucket=BUCKET_NAME)
    if not response:
        raise Exception("Failed to create bucket")

    no_key = get_s3_keys(bucket=BUCKET_NAME, prefix=PREFIX)
    assert len(no_key) == 0  # no keys in bucket

    _put_object(
        client=s3_client,
        bucket_name=BUCKET_NAME,
        prefix=PREFIX,
        key="foo-1",
        body="test",
    )
    _put_object(
        client=s3_client,
        bucket_name=BUCKET_NAME,
        prefix=PREFIX,
        key="foo-2",
        body="test",
    )
    two_keys = get_s3_keys(bucket=BUCKET_NAME, prefix=PREFIX)
    assert len(two_keys) == 2

    # if `since_key` is not present in the list of objects, then an exception is thrown
    with pytest.raises(Exception):
        _ = get_s3_keys(bucket=BUCKET_NAME, prefix=PREFIX, since_key="content/foo-z")


def test_get_s3_since_key_with_modified_files():
    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.create_bucket(Bucket=BUCKET_NAME)

    _put_object(
        client=s3_client,
        bucket_name=BUCKET_NAME,
        prefix=PREFIX,
        key="A",
        body="initial content",
        delay=1,
    )

    initial_keys = get_s3_keys(bucket=BUCKET_NAME, prefix=PREFIX)
    assert len(initial_keys) == 1
    assert initial_keys[0].endswith("A")

    _put_object(
        client=s3_client,
        bucket_name=BUCKET_NAME,
        prefix=PREFIX,
        key="B",
        body="content B",
        delay=1,
    )
    _put_object(
        client=s3_client,
        bucket_name=BUCKET_NAME,
        prefix=PREFIX,
        key="C",
        body="content C",
        delay=1,
    )

    # Modify the original `A` object
    _put_object(
        client=s3_client,
        bucket_name=BUCKET_NAME,
        prefix=PREFIX,
        key="A",
        body="modified content",
        delay=1,
    )

    new_keys = get_s3_keys(bucket=BUCKET_NAME, prefix=PREFIX, since_key=initial_keys[0])

    # Since A has been modified, and B and C were created before this key, we will not get new keys
    assert len(new_keys) == 0


def test_get_objects():
    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.create_bucket(Bucket=BUCKET_NAME)

    _put_object(
        client=s3_client,
        bucket_name=BUCKET_NAME,
        prefix=PREFIX,
        key="A",
        body="initial content",
        delay=1,
    )

    objects = get_objects(bucket=BUCKET_NAME, prefix=PREFIX)

    obj = objects[0]
    object_key = obj.get("Key")
    object_last_modified = obj.get("LastModified")
    assert len(objects) == 1
    assert object_key.endswith("A")

    _put_object(
        client=s3_client,
        bucket_name=BUCKET_NAME,
        prefix=PREFIX,
        key="B",
        body="content B",
        delay=1,
    )
    _put_object(
        client=s3_client,
        bucket_name=BUCKET_NAME,
        prefix=PREFIX,
        key="C",
        body="content C",
        delay=1,
    )

    new_keys = get_objects(
        bucket=BUCKET_NAME, prefix=PREFIX, since_last_modified=object_last_modified
    )

    assert len(new_keys) == 2


def test_get_objects_with_modified():
    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.create_bucket(Bucket=BUCKET_NAME)

    _put_object(
        client=s3_client,
        bucket_name=BUCKET_NAME,
        prefix=PREFIX,
        key="A",
        body="content",
        delay=1,
    )

    _put_object(
        client=s3_client,
        bucket_name=BUCKET_NAME,
        prefix=PREFIX,
        key="B",
        body="content",
        delay=1,
    )

    objects = get_objects(bucket=BUCKET_NAME, prefix=PREFIX)
    assert len(objects) == 2

    obj = objects[1]
    obj_b_last_modified = obj.get("LastModified")

    _put_object(
        client=s3_client,
        bucket_name=BUCKET_NAME,
        prefix=PREFIX,
        key="C",
        body="content",
        delay=1,
    )

    # modify timestamp of B
    _put_object(
        client=s3_client,
        bucket_name=BUCKET_NAME,
        prefix=PREFIX,
        key="B",
        body="updated content",
        delay=1,
    )

    objects = get_objects(
        bucket=BUCKET_NAME, prefix=PREFIX, since_last_modified=obj_b_last_modified
    )

    assert len(objects) == 2
    assert objects[0].get("Key").endswith("C")
    assert objects[1].get("Key").endswith("B")
