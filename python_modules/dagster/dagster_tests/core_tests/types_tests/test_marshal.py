import tempfile
import os

import pytest

from dagster.core.types.marshal import (
    PickleSerializationStrategy,
    serialize_to_file,
    deserialize_from_file,
)
from dagster.utils.test import yield_empty_pipeline_context


# https://dev.azure.com/elementl/dagster/_build/results?buildId=2941
@pytest.mark.skipif(
    os.name == 'nt', reason='Azure pipelines does not let us use tempfile.NamedTemporaryFile'
)
def test_serialize_deserialize():
    with yield_empty_pipeline_context() as context:
        with tempfile.NamedTemporaryFile() as fd:
            serialize_to_file(context, PickleSerializationStrategy(), 'foo', fd.name)
            assert deserialize_from_file(context, PickleSerializationStrategy(), fd.name) == 'foo'
