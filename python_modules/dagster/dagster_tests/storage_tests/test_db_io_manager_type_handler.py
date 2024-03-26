import uuid
from enum import Enum
from typing import Iterator

import pytest
from dagster import asset, materialize
from dagster._check import CheckError


class DataFrameType(Enum):
    PANDAS = "pandas"
    PYSPARK = "pyspark"
    POLARS = "polars"


class TemplateTypeHandlerTestSuite:
    @property
    def df_format(self) -> DataFrameType:
        """Returns the type of dataframe this test suite will use."""
        raise NotImplementedError("All test suites must implement df_format.")

    def io_managers(self):
        """Returns a list of I/O managers to test. In most cases there will be one pythonic style I/O manager, and one old-stype I/O manager."""
        raise NotImplementedError("All test suites must implement io_managers.")

    def create_temporary_table(self) -> Iterator[str]:
        """Returns the name of the created table."""
        raise NotImplementedError("All test suites must implement create_temporary_table")

    @property
    def temporary_table_name(self):
        return "test_io_manager_" + str(uuid.uuid4()).replace("-", "_")

    def test_not_supported_type(self):
        @asset
        def not_supported() -> int:
            return 1

        for io_manager in self.io_managers():
            with pytest.raises(
                CheckError,
                match="does not have a handler for type '<class 'int'>'",
            ):
                materialize([not_supported], resource_defs={"io_manager": io_manager})
