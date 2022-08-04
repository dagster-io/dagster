from dagster import make_values_resource

partition_bounds = make_values_resource(start=str, end=str)
