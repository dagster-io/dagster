'''
A lakehouse is a dag of computation that defines the relationship
between computed tables in a data lake/data warehouse (get it?).

The user defines solids usings decorators for how the computation
is performed ie @pyspark_table. These "tables" are used
interchangeably as both types *and* solids.

By having a 1:1 mapping between output type and solid lakehouse, and
by using these types as input types in dagster space, we can automatically
construct the dependency graph on the users behalf.

The user is also responsible for building a class that implements the
Lakehouse interface. This allows the user to totally customize where
these tables are actually materialized, and thus can be grafted on to
arbitrary data lake layouts.

See lakehouse_tests/__init__.py for a description of the use cases
implemented so far.
'''

from .house import Lakehouse
from .pipeline import construct_lakehouse_pipeline
from .pyspark import PySparkMemLakehouse, pyspark_table
from .snowflake_table import SnowflakeLakehouse, snowflake_table
from .sqlite import SqlLiteLakehouse, sqlite_table
from .table import ITableHandle, InMemTableHandle, input_table
