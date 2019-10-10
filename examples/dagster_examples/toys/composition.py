from dagster import InputDefinition, Int, composite_solid, pipeline, solid


@solid(input_defs=[InputDefinition('num', Int)])
def add_one(_, num):
    return num + 1


@solid(input_defs=[InputDefinition('num')])
def div_two(_, num):
    return num / 2


@composite_solid
def add_two(num):
    return add_one(num=add_one(num))


@composite_solid
def add_four(num):
    return add_two(num=add_two(num))


@composite_solid
def div_four(num):
    return div_two(num=div_two(num))


@pipeline
def composition():
    div_four(add_four())
