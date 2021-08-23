from typing import Tuple

from dagster import In, Out, op


@op(
    ins={"arg1": In(metadata={"a": "b"})},
    out={"out1": Out(metadata={"c": "d"}), "out2": Out(metadata={"e": "f"})},
)
def do_something(arg1: str) -> Tuple[int, int]:
    return int(arg1), int(arg1) + 1
