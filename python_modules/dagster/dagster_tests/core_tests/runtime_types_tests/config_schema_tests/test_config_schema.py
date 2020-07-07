import pytest

from dagster import String
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.types.config_schema import input_hydration_config, output_materialization_config


def test_input_hydration_config_one():
    @input_hydration_config(String)
    def _foo(_, hello):
        return hello


def test_input_hydration_config_missing_context():

    with pytest.raises(DagsterInvalidDefinitionError):

        @input_hydration_config(String)
        def _foo(hello):
            return hello


def test_input_hydration_config_missing_variable():

    with pytest.raises(DagsterInvalidDefinitionError):

        @input_hydration_config(String)
        def _foo(_):
            return 1


def test_input_hydration_config_backcompat_args():
    @input_hydration_config(config_cls=String)
    def _foo(_, hello):
        return hello


def test_output_materialization_config_backcompat_args():
    @output_materialization_config(config_cls=String)
    def _foo(_, _a, _b):
        pass
