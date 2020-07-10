import pytest


def test_no_warnings_on_import():
    with pytest.warns(None) as record:
        import dagster  # pylint: disable=unused-import

    assert len(record) == 0
