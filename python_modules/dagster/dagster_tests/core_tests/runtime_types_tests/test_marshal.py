from dagster.core.types.marshal import PickleSerializationStrategy
from dagster.utils import safe_tempfile_path


def test_serialization_strategy():
    serialization_strategy = PickleSerializationStrategy()
    with safe_tempfile_path() as tempfile_path:
        serialization_strategy.serialize_to_file("foo", tempfile_path)
        assert serialization_strategy.deserialize_from_file(tempfile_path) == "foo"
