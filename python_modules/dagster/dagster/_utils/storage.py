import os


def get_materialization_chunk_size() -> int:
    """Get the chunk size for fetching materializations after a cursor.

    Returns:
        int: The chunk size for materialization queries, configurable via
        DAGSTER_FETCH_MATERIALIZATIONS_AFTER_CURSOR_CHUNK_SIZE environment variable.
        Defaults to 1000.
    """
    return int(os.getenv("DAGSTER_FETCH_MATERIALIZATIONS_AFTER_CURSOR_CHUNK_SIZE", "1000"))
