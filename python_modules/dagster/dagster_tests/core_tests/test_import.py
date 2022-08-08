import pytest
from dagster import In, Out, op


def test_no_warnings_on_import():
    with pytest.warns(None) as record:
        import dagster  # pylint: disable=unused-import

    assert len(record) == 0
