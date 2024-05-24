from dagster import Definitions, asset


@asset(tags={"foo": "bar"})  # removing a tag should be detected
def upstream():
    return 1


@asset(tags={"baz": "foo"})  # changing a tag value should be detected
def downstream(upstream):
    return upstream + 1


@asset(tags={"green": "apple", "yellow": "banana"})  # changing a tag key should be detected
def fruits():
    return 1


@asset(tags={"a": "A", "b": "B", "c": "C"})  # adding a tag value should be detected
def letters():
    return 1


@asset(tags={"three": "3", "one": "1", "two": "2"})  # ordering changes should not be detected
def numbers():
    return 1


defs = Definitions(assets=[upstream, downstream, numbers, letters, fruits])
