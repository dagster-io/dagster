from dagster._record import record


@record
class OrderBy:
    """General class for specifying sort order for queries."""

    column_name: str
    ascending: bool = True
