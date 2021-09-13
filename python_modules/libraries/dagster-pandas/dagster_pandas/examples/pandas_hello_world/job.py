import dagster_pandas as dagster_pd
from dagster import (
    In,
    Out,
    config_from_files,
    file_relative_path,
    graph,
    in_process_executor,
    op,
)


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
    ins={"sum_sq_sop": In(dagster_pd.DataFrame)},
    out=Out(dagster_pd.DataFrame),
)
def always_fails_op(**_kwargs):
    raise Exception("I am a programmer and I make error")


@graph
def pandas_hello_world_fails():
    always_fails_op(sum_sq_op=sum_sq_op(sum_df=sum_op()))


pandas_hello_world_fails_test = pandas_hello_world_fails.to_job(executor_def=in_process_executor)


@graph
def pandas_hello_world():
    sum_sq_op(sum_op())


pandas_hello_world_test = pandas_hello_world.to_job(
    config=config_from_files(
        [file_relative_path(__file__, f"environments/pandas_hello_world_test.yaml")]
    ),
    executor_def=in_process_executor,
)

pandas_hello_world_prod = pandas_hello_world.to_job(
    config=config_from_files(
        [file_relative_path(__file__, f"environments/pandas_hello_world_prod.yaml")]
    )
)