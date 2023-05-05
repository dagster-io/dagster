from dagster import asset


@asset(code_version="v2")
def versioned_number():
    return 11


@asset(code_version="v1")
def multiplied_number(versioned_number):
    return versioned_number * 2
