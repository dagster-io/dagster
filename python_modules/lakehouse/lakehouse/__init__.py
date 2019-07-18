'''
A lakehouse is a dag of computation that defines the relationship
between computed tables in a data lake/data warehouse (get it?).

The user defines solids usings the @lakehouse_table definition.
These "tables" are used interchangeably as both types *and* solids.

The user defines functions with dagster input definitions with contain
those table types. One does this with lakehouse_table_input_def.

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

from .table import lakehouse_table, input_table, InMemTableHandle
from .pipeline import construct_lakehouse_pipeline
from .pyspark import PySparkMemLakehouse
from .house import Lakehouse
