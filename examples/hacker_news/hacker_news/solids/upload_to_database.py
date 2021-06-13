from dagster import OutputDefinition, solid
from hacker_news.resources.parquet_pointer import ParquetPointer
from pyspark.sql.types import StructType


def make_upload_to_database_solid(table: str, schema: StructType):
    """
    Returns a solid that takes as input a path to data (with the specified schema) that will be
    uploaded to the specified table in a database.

    The specific implementation of this upload process is left to the db_io_manager resource, and
    can be swapped between modes.
    """

    @solid(
        name=f"upload_{table.split('.')[-1]}",
        output_defs=[
            OutputDefinition(
                io_manager_key="db_io_manager",
                metadata={"table": table},
            )
        ],
    )
    def _solid(_, path: str) -> ParquetPointer:
        return ParquetPointer(path, schema)

    return _solid
