# dagster-ibis

This package provides an integration with Ibis, allowing you to read and write data through the Ibis API to any supported database backend.

## Installation

```bash
pip install dagster-ibis
```

## Usage

```python
from dagster import Definitions, asset
from dagster_ibis import IbisIOManager
import ibis
import ibis.expr.types as ir
import pandas as pd

@asset
def my_table() -> ir.Table:
    # Create your Ibis expression
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    return ibis.memtable(df)

# Configure the I/O manager with your connection details
defs = Definitions(
    assets=[my_table],
    resources={
        "io_manager": IbisIOManager(
            backend="duckdb",
            database="mydb.duckdb",
            schema="my_schema"
        )
    }
)
```
