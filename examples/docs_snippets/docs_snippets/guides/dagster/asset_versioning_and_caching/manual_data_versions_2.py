from dagster import DataVersion, Output, asset


@asset(code_version="v5")
def versioned_number():
    value = 10 + 10
    return Output(value, data_version=DataVersion(str(value)))


@asset(code_version="v1")
def multiplied_number(versioned_number):
    return versioned_number * 2
