import uuid
from io import BytesIO

from dagster_gcp.gcs.object_store import GCSObjectStore

from dagster.core.types.marshal import PickleSerializationStrategy


def test_gcs_object_store(gcs_bucket):
    s = GCSObjectStore(gcs_bucket)

    test_str = b'this is a test'
    file_obj = BytesIO()
    file_obj.write(test_str)
    file_obj.seek(0)

    ss = PickleSerializationStrategy()

    key = 'test-file-%s' % uuid.uuid4().hex
    s.set_object(key, file_obj, ss)

    assert s.has_object(key)
    assert s.get_object(key, ss).obj.read() == test_str

    other_key = 'test-file-%s' % uuid.uuid4().hex
    s.cp_object(key, other_key)
    assert s.has_object(other_key)

    s.rm_object(key)
    s.rm_object(other_key)
    assert not s.has_object(key)
    assert not s.has_object(other_key)
