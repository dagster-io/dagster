from dagster.core.storage.object_store import DEFAULT_SERIALIZATION_STRATEGY
from dagster_aws.s3 import S3ObjectStore


def test_s3_object_store(mock_s3_bucket, caplog):
    key = "foo"

    s3_obj_store = S3ObjectStore(mock_s3_bucket.name)
    res_key = s3_obj_store.set_object(key, True, DEFAULT_SERIALIZATION_STRATEGY)
    assert res_key == "s3://{s3_bucket}/{key}".format(s3_bucket=mock_s3_bucket.name, key=key)

    s3_obj_store.set_object(key, True, DEFAULT_SERIALIZATION_STRATEGY)
    assert "Removing existing S3 key" in caplog.text

    assert s3_obj_store.has_object(key)
    assert s3_obj_store.get_object(key, DEFAULT_SERIALIZATION_STRATEGY)[0] == True

    s3_obj_store.cp_object(key, "bar")
    assert s3_obj_store.has_object("bar")

    s3_obj_store.rm_object(key)
    assert not s3_obj_store.has_object(key)

    assert s3_obj_store.uri_for_key(key) == "s3://{s3_bucket}/{key}".format(
        s3_bucket=mock_s3_bucket.name, key=key
    )
