import hashlib

import pytest

from dagster import String
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.types.config_schema import dagster_type_loader


def test_dagster_type_loader_one():
    @dagster_type_loader(String)
    def _foo(_, hello):
        return hello


def test_dagster_type_loader_missing_context():

    with pytest.raises(DagsterInvalidDefinitionError):

        @dagster_type_loader(String)
        def _foo(hello):
            return hello


def test_dagster_type_loader_missing_variable():

    with pytest.raises(DagsterInvalidDefinitionError):

        @dagster_type_loader(String)
        def _foo(_):
            return 1


def test_dagster_type_loader_default_version():
    @dagster_type_loader(String)
    def _foo(_, hello):
        return hello

    assert _foo.loader_version is None
    assert _foo.compute_loaded_input_version({}) is None


def test_dagster_type_loader_provided_version():
    def _get_ext_version(dict_param):
        return dict_param["version"]

    @dagster_type_loader(String, loader_version="5", external_version_fn=_get_ext_version)
    def _foo(_, hello):
        return hello

    dict_param = {"version": "42"}

    assert _foo.loader_version == "5"
    assert _foo.compute_loaded_input_version(dict_param) == hashlib.sha1(b"542").hexdigest()
