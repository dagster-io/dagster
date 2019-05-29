import tempfile
import os

import pytest

from dagster.core.types.marshal import PickleSerializationStrategy


# https://dev.azure.com/elementl/dagster/_build/results?buildId=2941
@pytest.mark.skipif(
    os.name == 'nt', reason='Azure pipelines does not let us use tempfile.NamedTemporaryFile'
)
def test_serialization_strategy():
    serialization_strategy = PickleSerializationStrategy()
    with tempfile.NamedTemporaryFile() as fd:
        serialization_strategy.serialize_to_file('foo', fd.name)
        assert serialization_strategy.deserialize_from_file(fd.name) == 'foo'
