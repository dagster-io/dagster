from random import random

from dagster import DailyPartitionsDefinition, StaticPartitionsDefinition, asset

FAILURE_RATE = 0.5


@asset(partitions_def=DailyPartitionsDefinition(start_date="2023-02-02"))
def failing_time_partitioned():
    if random() < FAILURE_RATE:
        raise ValueError("Failed")


@asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c"]))
def failing_static_partitioned():
    if random() < FAILURE_RATE:
        raise ValueError("Failed")


@asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c"]))
def downstream_of_failing_partitioned(failing_static_partitioned):
    ...
