import dagster as dg


@dg.asset(metadata={"foo": "bar"})  # removing a tag should be detected
def upstream():
    return 1


@dg.asset(metadata={"baz": "foo"})  # changing a tag value should be detected
def downstream(upstream):
    return upstream + 1


@dg.asset(metadata={"green": "apple", "yellow": "banana"})  # changing a tag key should be detected
def fruits():
    return 1


@dg.asset(metadata={"a": "A", "b": "B", "c": "C"})  # adding a tag value should be detected
def letters():
    return 1


@dg.asset(
    metadata={"three": "3", "one": "1", "two": "2"}
)  # ordering changes should not be detected
def numbers():
    return 1


defs = dg.Definitions(assets=[upstream, downstream, numbers, letters, fruits])
