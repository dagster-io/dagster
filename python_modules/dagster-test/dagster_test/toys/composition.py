from dagster import Float, In, Int, List, Out, op
from dagster._legacy import InputDefinition, OutputDefinition, composite_solid, pipeline


@op(out=Out(Int))
def emit_one(_):
    return 1


@op(
    ins={"numbers": In(List[Int])},
    out=Out(Int),
)
def add(_, numbers):
    return sum(numbers)


@op(ins={"num": In(Float)}, out=Out(Float))
def div_two(_, num):
    return num / 2


@composite_solid(output_defs=[OutputDefinition(Int)])
def emit_two():
    return add([emit_one(), emit_one()])


@composite_solid(input_defs=[InputDefinition("num", Int)], output_defs=[OutputDefinition(Int)])
def add_four(num):
    return add([emit_two(), emit_two(), num])


@composite_solid(input_defs=[InputDefinition("num", Float)], output_defs=[OutputDefinition(Float)])
def div_four(num):
    return div_two(num=div_two(num))


@op(ins={"num": In(Int)}, out=Out(Float))
def int_to_float(_, num):
    return float(num)


@pipeline(description="Demo pipeline that makes use of composite solids.")
def composition():
    div_four(int_to_float(add_four()))
