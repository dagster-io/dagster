from dagster import asset


@asset(code_version="v2")
def versioned_number():
    return 11
