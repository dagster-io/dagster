import dagster as dg


@dg.repository  # pyright: ignore[reportArgumentType]
def error_repo():
    a = None
    a()  # pyright: ignore[reportOptionalCall]
