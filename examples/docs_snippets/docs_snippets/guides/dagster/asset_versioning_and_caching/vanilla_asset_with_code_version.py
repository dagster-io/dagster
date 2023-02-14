from dagster import asset


@asset(code_version="v1")
def versioned_number():
    return 1
