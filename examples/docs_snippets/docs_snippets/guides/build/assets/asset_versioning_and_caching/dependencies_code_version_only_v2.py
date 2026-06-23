from dagster import asset


@asset(code_version="v3")
def versioned_number():
    return 15


@asset(code_version="v1")
def multiplied_number(versioned_number):
    return versioned_number * 2
