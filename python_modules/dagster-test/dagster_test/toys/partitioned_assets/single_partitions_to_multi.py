from dagster import MultiPartitionsDefinition, StaticPartitionsDefinition, asset

abc_def = StaticPartitionsDefinition(["a", "b", "c"])

composite = MultiPartitionsDefinition(
    {
        "abc": abc_def,
        "123": StaticPartitionsDefinition(["1", "2", "3"]),
    }
)


@asset(partitions_def=abc_def)
def single_partitions(context):
    return 1


@asset(partitions_def=composite)
def multi_partitions(single_partitions):
    return 1
