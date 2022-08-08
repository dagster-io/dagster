import re

import pytest

from dagster import op, DagsterInvalidDefinitionError, Dict, List, Noneable, Optional
from dagster._core.errors import DagsterInvalidConfigDefinitionError
from dagster._legacy import solid


def test_invalid_optional_in_config():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            "You have passed an instance of DagsterType Int? to the config system"
        ),
    ):

        @op(config_schema=Optional[int])
        def _op(_):
            pass


def test_invalid_dict_call():
    # prior to 0.7.0 dicts in config contexts were callable
    with pytest.raises(
        TypeError, match=re.escape("'DagsterDictApi' object is not callable")
    ):

        @op(config_schema=Dict({"foo": int}))  # pylint: disable=not-callable
        def _op(_):
            pass


def test_list_in_config():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            "Cannot use List in the context of config. Please use a python "
            "list (e.g. [int]) or dagster.Array (e.g. Array(int)) instead."
        ),
    ):

        @op(config_schema=List[int])
        def _op(_):
            pass


def test_invalid_list_element():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            "Invalid type: dagster_type must be an instance of DagsterType or a Python type: "
        ),
    ):
        _ = List[Noneable(int)]


def test_non_scalar_key_map():
    with pytest.raises(
        DagsterInvalidConfigDefinitionError,
        match=re.escape("Map dict must have a scalar type as its only key."),
    ):

        @op(config_schema={Noneable(int): str})
        def _op(_):
            pass
