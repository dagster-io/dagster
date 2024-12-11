from dagster import repository


@repository  # pyright: ignore[reportArgumentType]
def error_repo():
    a = None
    a()  # pyright: ignore[reportOptionalCall]
