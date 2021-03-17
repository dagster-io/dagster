import re

import pytest
from dagster import DagsterInvalidDefinitionError, Dict, List, Noneable, Optional, solid


def test_invalid_optional_in_config():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape("You have passed an instance of DagsterType Int? to the config system"),
    ):

        @solid(config_schema=Optional[int])
        def _solid(_):
            pass


def test_invalid_dict_call():
    # prior to 0.7.0 dicts in config contexts were callable
    with pytest.raises(TypeError, match=re.escape("'DagsterDictApi' object is not callable")):

        @solid(config_schema=Dict({"foo": int}))  # pylint: disable=not-callable
        def _solid(_):
            pass


def test_list_in_config():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            "Cannot use List in the context of config. Please use a python "
            "list (e.g. [int]) or dagster.Array (e.g. Array(int)) instead."
        ),
    ):

        @solid(config_schema=List[int])
        def _solid(_):
            pass


def test_invalid_list_element():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            "Invalid type: dagster_type must be an instance of DagsterType or a Python type: "
        ),
    ):
        _ = List[Noneable(int)]
