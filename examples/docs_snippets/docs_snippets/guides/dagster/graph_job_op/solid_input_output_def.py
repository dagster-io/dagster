from dagster import InputDefinition, OutputDefinition
from dagster._legacy import solid


@solid(
    input_defs=[InputDefinition("arg1", metadata={"a": "b"})],
    output_defs=[OutputDefinition(metadata={"c": "d"})],
)
def do_something(arg1: str) -> int:
    return int(arg1)
