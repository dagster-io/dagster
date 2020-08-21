from dagster import Float, InputDefinition, Int, OutputDefinition, composite_solid, pipeline, solid


@solid(input_defs=[InputDefinition("num", Int)], output_defs=[OutputDefinition(Int)])
def add_one(_, num):
    return num + 1


@solid(input_defs=[InputDefinition("num", Float)], output_defs=[OutputDefinition(Float)])
def div_two(_, num):
    return num / 2


@composite_solid(input_defs=[InputDefinition("num", Int)], output_defs=[OutputDefinition(Int)])
def add_two(num):
    return add_one(num=add_one(num))


@composite_solid(input_defs=[InputDefinition("num", Int)], output_defs=[OutputDefinition(Int)])
def add_four(num):
    return add_two(num=add_two(num))


@composite_solid(input_defs=[InputDefinition("num", Float)], output_defs=[OutputDefinition(Float)])
def div_four(num):
    return div_two(num=div_two(num))


@solid(input_defs=[InputDefinition("num", Int)], output_defs=[OutputDefinition(Float)])
def int_to_float(_, num):
    return float(num)


@pipeline(description="Demo pipeline that makes use of composite solids.")
def composition():
    div_four(int_to_float(add_four()))
