import pytest

from dagster import config


def test_config():
    mat = config.Materialization(solid='some_solid', name='a_mat_type', args={})
    assert isinstance(mat, config.Materialization)
    assert mat.solid == 'some_solid'
    assert mat.name == 'a_mat_type'
    assert mat.args == {}


def test_bad_config():
    with pytest.raises(Exception):
        config.Materialization(solid='name', name=1, args={})
