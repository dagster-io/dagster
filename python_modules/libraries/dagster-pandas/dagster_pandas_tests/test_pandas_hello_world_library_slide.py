from dagster_pandas import DataFrame

from dagster import In, Out, graph, op
from dagster._utils import file_relative_path


def test_hello_world():
    @op(ins={"num_csv": In(DataFrame)}, out=Out(DataFrame))
    def hello_world_op(num_csv):
        num_csv["sum"] = num_csv["num1"] + num_csv["num2"]
        return num_csv

    @graph
    def hello_world():
        hello_world_op()

    result = hello_world.execute_in_process(
        run_config={
            "ops": {
                "hello_world_op": {
                    "inputs": {
                        "num_csv": {"csv": {"path": file_relative_path(__file__, "num.csv")}}
                    }
                }
            }
        }
    )
    assert result.success
    assert result.output_for_node("hello_world_op").to_dict("list") == {
        "num1": [1, 3],
        "num2": [2, 4],
        "sum": [3, 7],
    }
