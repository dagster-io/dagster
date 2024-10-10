import time

import boto3
import moto
import pytest

from dagster_aws.s3.sensor import get_s3_keys


def test_get_s3_keys():
    bucket_name = "test-bucket"
    prefix = "content"

    with moto.mock_s3():
        s3_client = boto3.client("s3", region_name="us-east-1")
        response = s3_client.create_bucket(Bucket=bucket_name)
        if not response:
            raise Exception("Failed to create bucket")

        def put_key_in_bucket(key, body):
            r = s3_client.put_object(Bucket=bucket_name, Key=f"{prefix}/{key}", Body=body)
            if not r:
                raise Exception("Failed to create object")

        no_key = get_s3_keys(bucket=bucket_name, prefix=prefix)
        assert len(no_key) == 0  # no keys in bucket

        put_key_in_bucket(key="foo-1", body="test")
        one_key = get_s3_keys(bucket=bucket_name, prefix=prefix)
        assert len(one_key) == 1

        put_key_in_bucket(key="foo-2", body="test")
        two_keys = get_s3_keys(bucket=bucket_name, prefix=prefix)
        assert len(two_keys) == 2, "both keys should be returned"

        one_key_shift = get_s3_keys(bucket=bucket_name, prefix=prefix, since_key=two_keys[0])
        assert len(one_key_shift) == 1, "only one key should be returned"

        two_key_shift = get_s3_keys(bucket=bucket_name, prefix=prefix, since_key=two_keys[1])
        assert len(two_key_shift) == 0, "no keys should be returned"

        # test pagination
        for i in range(3, 1002):
            put_key_in_bucket(key=f"foo-{i}", body="test")
        thousand_and_one_keys = get_s3_keys(bucket=bucket_name, prefix=prefix)
        assert len(thousand_and_one_keys) == 1001, "1001 keys should be returned"

        #  test pagination with since_key
        # keys are sorted by LastModified time, with a resolution of 1 second, so the key at index 999 will vary.
        # The test would be flaky if sorted was not guaranteed to be stable, which it is
        # according to: https://wiki.python.org/moin/HowTo/Sorting/.
        keys = get_s3_keys(bucket=bucket_name, prefix=prefix, since_key=thousand_and_one_keys[999])
        assert len(keys) == 1, "1 key should be returned"

        #  test pagination with since_key > 1000
        for i in range(1002, 1101):
            put_key_in_bucket(key=f"foo-{i}", body="test")
        thousand_and_one_hundred_keys = get_s3_keys(bucket=bucket_name, prefix=prefix)
        assert len(thousand_and_one_hundred_keys) == 1100, "1100 keys should be returned"

        # keys are sorted by LastModified time, with a resolution of 1 second, so the key at index 999 will vary.
        # The test would be flaky if sorted was not guaranteed to be stable, which it is
        # according to: https://wiki.python.org/moin/HowTo/Sorting/.
        keys = get_s3_keys(
            bucket=bucket_name,
            prefix=prefix,
            since_key=thousand_and_one_hundred_keys[1090],
        )
        assert len(keys) == 9, "9 keys should be returned"


def test_get_s3_keys_missing_since_key():
    bucket_name = "test-bucket"
    prefix = "content"

    with moto.mock_s3():
        s3_client = boto3.client("s3", region_name="us-east-1")
        response = s3_client.create_bucket(Bucket=bucket_name)
        if not response:
            raise Exception("Failed to create bucket")

        def put_key_in_bucket(key, body):
            r = s3_client.put_object(Bucket=bucket_name, Key=f"{prefix}/{key}", Body=body)
            if not r:
                raise Exception("Failed to create object")

        no_key = get_s3_keys(bucket=bucket_name, prefix=prefix)
        assert len(no_key) == 0  # no keys in bucket

        put_key_in_bucket(key="foo-1", body="test")
        put_key_in_bucket(key="foo-2", body="test")
        two_keys = get_s3_keys(bucket=bucket_name, prefix=prefix)
        assert len(two_keys) == 2

        # if `since_key` is not present in the list of objects, then an exception is thrown
        with pytest.raises(Exception):
            _ = get_s3_keys(bucket=bucket_name, prefix=prefix, since_key="content/foo-z")


def test_get_s3_keys_with_modified_files():
    bucket_name = "test-bucket"
    prefix = "content"

    with moto.mock_s3():
        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket=bucket_name)

        def put_key_in_bucket(key, body):
            s3_client.put_object(Bucket=bucket_name, Key=f"{prefix}/{key}", Body=body)
            time.sleep(1)  # Ensure each file has a unique timestamp

        # Create file "A" at timestamp 1
        put_key_in_bucket(key="A", body="initial content")

        # Simulate first sensor run
        initial_keys = get_s3_keys(bucket=bucket_name, prefix=prefix)
        assert len(initial_keys) == 1
        assert initial_keys[0].endswith("A")

        # Create files "B" and "C", and modify "A" between sensor runs
        put_key_in_bucket(key="B", body="content B")
        put_key_in_bucket(key="C", body="content C")
        put_key_in_bucket(key="A", body="modified content")

        # Simulate second sensor run
        new_keys = get_s3_keys(bucket=bucket_name, prefix=prefix, since_key=initial_keys[0])

        # Because `since_key` has been modified, and our files are sorted by last modified date, we
        # will _not_ get keys for objecfts B and C
        assert len(new_keys) == 0
