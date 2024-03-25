import boto3
import moto
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
            bucket=bucket_name, prefix=prefix, since_key=thousand_and_one_hundred_keys[1090]
        )
        assert len(keys) == 9, "9 keys should be returned"
