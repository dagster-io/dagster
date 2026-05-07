from dagster import DataVersion, Output, asset


@asset(code_version="v2")
def versioned_number():
    value = 11
    return Output(value, DataVersion(str(value)))
