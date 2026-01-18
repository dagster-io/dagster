import re

import dagster as dg
import pytest


def test_invalid_optional_in_config():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=re.escape("You have passed an instance of DagsterType Int? to the config system"),
    ):

        @dg.op(config_schema=dg.Optional[int])  # pyright: ignore[reportArgumentType]
        def _op(_):
            pass


def test_invalid_dict_call():
    # prior to 0.7.0 dicts in config contexts were callable
    with pytest.raises(TypeError, match=re.escape("'DagsterDictApi' object is not callable")):

        @dg.op(config_schema=dg.Dict({"foo": int}))  # pyright: ignore[reportCallIssue]
        def _op(_):
            pass


def test_list_in_config():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=re.escape(
            "Cannot use List in the context of config. Please use a python "
            "list (e.g. [int]) or dagster.Array (e.g. Array(int)) instead."
        ),
    ):

        @dg.op(config_schema=dg.List[int])  # pyright: ignore[reportArgumentType]
        def _op(_):
            pass


def test_invalid_list_element():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=re.escape(
            "Invalid type: dagster_type must be an instance of DagsterType or a Python type: "
        ),
    ):
        _ = dg.List[dg.Noneable(int)]


def test_non_scalar_key_map():
    with pytest.raises(
        dg.DagsterInvalidConfigDefinitionError,
        match=re.escape("Map dict must have a scalar type as its only key."),
    ):

        @dg.op(config_schema={dg.Noneable(int): str})  # pyright: ignore[reportArgumentType]
        def _op(_):
            pass
