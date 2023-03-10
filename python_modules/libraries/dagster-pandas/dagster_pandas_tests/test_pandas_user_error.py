# pylint: disable=W0613

import dagster_pandas as dagster_pd
import pandas as pd
import pytest
from dagster import DagsterTypeCheckDidNotPass, In, Out, graph, op


def test_wrong_output_value():
    @op(ins={"num_csv": In(dagster_pd.DataFrame)}, out=Out(dagster_pd.DataFrame))
    def wrong_output(num_csv):
        return "not a dataframe"

    @op
    def pass_df():
        return pd.DataFrame()

    @graph
    def output_fails():
        return wrong_output(pass_df())

    with pytest.raises(DagsterTypeCheckDidNotPass):
        output_fails.execute_in_process()


def test_wrong_input_value():
    @op(ins={"foo": In(dagster_pd.DataFrame)})
    def wrong_input(foo):
        return foo

    @op
    def pass_str():
        """Not a dataframe."""

    @graph
    def input_fails():
        wrong_input(pass_str())

    with pytest.raises(DagsterTypeCheckDidNotPass):
        input_fails.execute_in_process()
