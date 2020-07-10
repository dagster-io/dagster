import re

import pytest

from dagster import String
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.types.config_schema import (
    dagster_type_loader,
    input_hydration_config,
    output_materialization_config,
)


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


def test_input_hydration_config_backcompat_args():
    with pytest.warns(
        UserWarning,
        match=re.escape(
            '"input_hydration_config" is deprecated and will be removed in 0.10.0, use '
            '"dagster_type_loader" instead.'
        ),
    ):

        @input_hydration_config(config_cls=String)
        def _foo(_, hello):
            return hello


def test_output_materialization_config_backcompat_args():
    with pytest.warns(
        UserWarning,
        match=re.escape(
            '"output_materialization_config" is deprecated and will be removed in 0.10.0, use '
            '"dagster_type_materializer" instead.'
        ),
    ):

        @output_materialization_config(config_cls=String)
        def _foo(_, _a, _b):
            pass
