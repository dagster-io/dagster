# pylint: disable=W0613

import dagster_pandas as dagster_pd
import pandas as pd
import pytest
from dagster import (
    DagsterTypeCheckDidNotPass,
    InputDefinition,
    OutputDefinition,
    execute_pipeline,
    lambda_solid,
    pipeline,
)
from dagster.core.utility_solids import define_stub_solid


def test_wrong_output_value():
    csv_input = InputDefinition("num_csv", dagster_pd.DataFrame)

    @lambda_solid(input_defs=[csv_input], output_def=OutputDefinition(dagster_pd.DataFrame))
    def test_wrong_output(num_csv):
        return "not a dataframe"

    pass_solid = define_stub_solid("pass_solid", pd.DataFrame())

    @pipeline
    def test_pipeline():
        return test_wrong_output(pass_solid())

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_pipeline(test_pipeline)


def test_wrong_input_value():
    @lambda_solid(input_defs=[InputDefinition("foo", dagster_pd.DataFrame)])
    def test_wrong_input(foo):
        return foo

    pass_solid = define_stub_solid("pass_solid", "not a dataframe")

    @pipeline
    def test_pipeline():
        test_wrong_input(pass_solid())

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_pipeline(test_pipeline)
