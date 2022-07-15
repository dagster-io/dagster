from dagster import Float, InputDefinition, Int, List, OutputDefinition, composite_solid
from dagster.legacy import pipeline, solid


@solid(output_defs=[OutputDefinition(Int)])
def emit_one(_):
    return 1


@solid(input_defs=[InputDefinition("numbers", List[Int])], output_defs=[OutputDefinition(Int)])
def add(_, numbers):
    return sum(numbers)


@solid(input_defs=[InputDefinition("num", Float)], output_defs=[OutputDefinition(Float)])
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


@solid(input_defs=[InputDefinition("num", Int)], output_defs=[OutputDefinition(Float)])
def int_to_float(_, num):
    return float(num)


@pipeline(description="Demo pipeline that makes use of composite solids.")
def composition():
    div_four(int_to_float(add_four()))
