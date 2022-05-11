from dagster import Float, In, Int, List, MetadataValue, Out, graph, op


@op(out=Out(Int))
def emit_one():
    return 1


@op(ins={"numbers": In(List[Int])}, out=Out(Int))
def add(numbers):
    return sum(numbers)


@op(ins={"num": In(Float)}, out=Out(Float))
def div_two(num):
    return num / 2


@graph
def emit_two():
    return add([emit_one(), emit_one()])


@graph
def add_four(num):
    return add([emit_two(), emit_two(), num])


@graph
def div_four(num):
    return div_two(num=div_two(num))


@op(ins={"num": In(Int)}, out=Out(Float))
def int_to_float(num):
    return float(num)


@graph
def composition():
    div_four(int_to_float(add_four()))


composition_job = composition.to_job(
    description="Demo job that makes use of composite ops.",
    job_tags={"owner": "person_1", "team": "core", "other": "info"},
    metadata={
        "owner": "jamie",
        "baz": MetadataValue.text("bbbb"),
        "a_link": MetadataValue.url(url="https://dagster.io"),
    },
)
