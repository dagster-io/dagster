from dagster import In, Out, op


@op(ins={"arg1": In(metadata={"a": "b"})}, out=Out(metadata={"c": "d"}))
def do_something(arg1: str) -> int:
    return int(arg1)
