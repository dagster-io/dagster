from dagster import LogicalVersion, Output, asset


@asset(code_version="v4")
def versioned_number():
    value = 20
    return Output(value, logical_version=LogicalVersion(str(value)))


@asset(code_version="v1")
def multiplied_number(versioned_number):
    return versioned_number * 2
