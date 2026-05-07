import dagster as dg


@dg.repository
def error_repo():
    a = None
    a()  # ty: ignore[call-non-callable]
