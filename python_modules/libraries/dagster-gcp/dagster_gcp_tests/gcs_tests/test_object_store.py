import uuid
from io import BytesIO

from dagster.core.types.marshal import PickleSerializationStrategy
from dagster_gcp.gcs.object_store import GCSObjectStore


def test_gcs_object_store(gcs_bucket):
    object_store = GCSObjectStore(gcs_bucket)

    test_str = b"this is a test"
    file_obj = BytesIO()
    file_obj.write(test_str)
    file_obj.seek(0)

    serialization_strategy = PickleSerializationStrategy()

    key = "test-file-%s" % uuid.uuid4().hex
    object_store.set_object(key, file_obj, serialization_strategy)

    assert object_store.has_object(key)
    assert object_store.get_object(key, serialization_strategy)[0].read() == test_str

    other_key = "test-file-%s" % uuid.uuid4().hex
    object_store.cp_object(key, other_key)
    assert object_store.has_object(other_key)

    object_store.rm_object(key)
    object_store.rm_object(other_key)
    assert not object_store.has_object(key)
    assert not object_store.has_object(other_key)
