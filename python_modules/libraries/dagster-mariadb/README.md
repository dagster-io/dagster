# Dagster MariaDB Integration

A Dagster integration for MariaDB that provides first-class support for MariaDB databases in your data pipelines.

## Features

- **MariaDBResource**: Configurable resource for MariaDB database connections using SQLAlchemy
- **MariaDBPandasIOManager**: I/O manager for seamless read/write of Pandas DataFrames to MariaDB
- **OpenFlights ETL Example**: Complete example pipeline demonstrating real-world usage

## Installation

```bash
pip install dagster-mariadb
```

## Quick Start

### 1. Basic Resource Usage

```python
from dagster import Definitions, asset
from dagster_mariadb import MariaDBResource

@asset
def my_table(mariadb: MariaDBResource):
    with mariadb.get_connection() as conn:
        result = conn.execute("SELECT * FROM my_table")
        return result.fetchall()

defs = Definitions(
    assets=[my_table],
    resources={
        "mariadb": MariaDBResource(
            host="localhost",
            port=3306,
            user="dagster",
            password="password",
            database="my_database"
        )
    }
)
```

### 2. Pandas DataFrame I/O Manager

```python
from dagster import Definitions, asset
from dagster_mariadb import MariaDBResource, MariaDBPandasIOManager
import pandas as pd

@asset(io_manager_key="mariadb_io")
def my_dataframe() -> pd.DataFrame:
    return pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})

defs = Definitions(
    assets=[my_dataframe],
    resources={
        "mariadb": MariaDBResource(
            host="localhost",
            user="dagster",
            password="password",
            database="my_database"
        ),
        "mariadb_io": MariaDBPandasIOManager(
            engine_resource_key="mariadb",
            schema="public"
        )
    }
)
```

## Configuration

### MariaDBResource

The `MariaDBResource` supports the following configuration options:

```python
MariaDBResource(
    host="localhost",           # MariaDB server host
    port=3306,                  # MariaDB server port
    user="dagster",             # Database username
    password="password",        # Database password
    database="my_database",      # Database name (optional)
    additional_parameters={      # Additional SQLAlchemy parameters
        "pool_size": 10,
        "max_overflow": 20
    }
)
```

### MariaDBPandasIOManager

The `MariaDBPandasIOManager` supports the following configuration options:

```python
MariaDBPandasIOManager(
    engine_resource_key="mariadb",  # Resource key for MariaDBResource
    schema="public",                # Database schema (optional)
    mode="replace"                  # Write mode: "replace", "append", or "fail"
)
```

## OpenFlights ETL Example

The package includes a complete ETL pipeline example using the OpenFlights dataset. This demonstrates:

- Loading CSV data from files
- Data cleaning and validation
- Storing DataFrames in MariaDB
- Analytics and aggregations

### Running the Example

1. **Start MariaDB**:
   ```bash
   cd example
   docker-compose up -d
   ```

2. **Set environment variable**:
   ```bash
   export MARIADB_PASSWORD=password
   ```

3. **Run the pipeline**:
   ```bash
   dagster dev -f openflights_pipeline.py
   ```

### Example Data

The example includes sample data files:
- `data/airports.dat` - Airport information
- `data/airlines.dat` - Airline information  
- `data/routes.dat` - Flight routes

## Write Modes

The I/O manager supports three write modes:

- **`replace`** (default): Drop and recreate the table
- **`append`**: Add data to existing table
- **`fail`**: Fail if table already exists

## Schema Management

Tables are automatically created based on asset keys. You can specify schemas using:

1. **I/O Manager configuration**:
   ```python
   MariaDBPandasIOManager(schema="analytics")
   ```

2. **Asset metadata**:
   ```python
   @asset(metadata={"schema": "analytics"})
   def my_table() -> pd.DataFrame:
       ...
   ```

3. **Asset key prefix**:
   ```python
   @asset(key_prefix=["analytics"])
   def my_table() -> pd.DataFrame:
       ...
   ```

## Dependencies

- `sqlalchemy>=1.4.0` - Database ORM
- `pymysql>=1.0.0` - MariaDB/MySQL driver
- `pandas>=1.3.0` - Data manipulation


### Running Tests

```bash
cd python_modules/libraries/dagster-mariadb
pip install -e ".[dev]"
pytest
```

