import dagster_pandas as dagster_pd
import dagstermill

from dagster import In, Out, file_relative_path, op

from ...data_frame import DataFrame


@op(
    ins={"num": In(dagster_pd.DataFrame)},
    out=Out(dagster_pd.DataFrame),
)
def sum_op(num):
    sum_df = num.copy()
    sum_df["sum"] = sum_df["num1"] + sum_df["num2"]
    return sum_df


@op(
    ins={"sum_df": In(dagster_pd.DataFrame)},
    out=Out(dagster_pd.DataFrame),
)
def sum_sq_op(sum_df):
    sum_sq_df = sum_df.copy()
    sum_sq_df["sum_sq"] = sum_df["sum"] ** 2
    return sum_sq_df


@op(
    ins={"sum_sq_op": In(dagster_pd.DataFrame)},
    out=Out(dagster_pd.DataFrame),
)
def always_fails_op(**_kwargs):
    raise Exception("I am a programmer and I make error")


def nb_test_path(name):
    return file_relative_path(__file__, "../notebooks/{name}.ipynb".format(name=name))


papermill_pandas_hello_world = dagstermill.factory.define_dagstermill_op(
    name="papermill_pandas_hello_world",
    notebook_path=nb_test_path("papermill_pandas_hello_world"),
    ins={"df": In(DataFrame)},
    outs={"result": Out(DataFrame)},
)
