# Databricks and Snowflake Example

A Dagster workspace demonstrating how to build heterogeneous data platforms using multiple code locations. This project showcases production data platform patterns with Databricks Delta Lake and Snowflake dbt medallion architectures as separate projects within a workspace.

## Project Structure

```
project_databricks_and_snowflake/
├── dg.toml                           # Workspace configuration
├── dagster_cloud.yaml                # Dagster+ deployment configuration
├── deployments/
│   └── local/
│       └── pyproject.toml            # Local environment for dg commands
├── projects/
│   ├── databricks-delta/             # Code location 1
│   │   ├── pyproject.toml
│   │   ├── tests/
│   │   └── src/databricks_delta/
│   │       ├── definitions.py
│   │       └── defs/
│   │           ├── components/lakehouse/
│   │           └── resources.py
│   └── snowflake-medallion/          # Code location 2
│       ├── pyproject.toml
│       ├── tests/
│       └── src/snowflake_medallion/
│           ├── definitions.py
│           ├── dbt_project/
│           └── defs/
│               ├── components/medallion/
│               └── resources.py
├── .env.example
├── pyproject.toml
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

1. Set up the local deployment environment:

```bash
cd deployments/local
uv sync
source .venv/bin/activate
```

2. Set up each project environment:

```bash
cd ../../projects/databricks-delta
uv sync

cd ../snowflake-medallion
uv sync
```

3. Copy the environment file and configure credentials:

```bash
cp .env.example .env
# Edit .env with your credentials
```

### Running the Workspace

From the workspace root with the local environment activated:

```bash
cd /path/to/project_databricks_and_snowflake
source deployments/local/.venv/bin/activate
dg dev
```

This starts the Dagster webserver at `http://localhost:3000` and loads both code locations.

## Code Locations (Projects)

### 1. Databricks Delta

**Pattern**: Lakehouse with Medallion Architecture  
**Storage**: Delta Lake tables  
**Technology**: Databricks, Delta Lake

Implements the medallion architecture with:

- **Bronze Layer**: Raw sensor data loaded to Delta tables
- **Silver Layer**: Cleaned and validated sensor data
- **Gold Layer**: Aggregated sensor summaries

### 2. Snowflake Medallion

**Pattern**: ELT with Medallion Architecture  
**Storage**: Snowflake tables  
**Technology**: Snowflake, dbt, SQL transformations

Implements the medallion architecture with:

- **Bronze Layer**: Raw customer data loaded from sources
- **Silver Layer**: Cleaned and validated customer data (dbt models)
- **Gold Layer**: Curated customer summaries (dbt models)

## Demo Mode

Both projects support demo mode for local development without external dependencies:

- **Databricks Delta**: Uses local file system instead of Databricks
- **Snowflake Medallion**: Uses DuckDB adapter instead of Snowflake

Demo mode is automatically enabled when environment variables are not set.

## Environment Variables

### Databricks Configuration

```bash
DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
DATABRICKS_TOKEN=dapi_your_token_here
DELTA_STORAGE_PATH=data/delta
```

### Snowflake Configuration

```bash
SNOWFLAKE_ACCOUNT=your-account.region
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=PUBLIC
```

## Running Tests

Each project has its own tests. Run them from within each project directory:

```bash
# Databricks Delta tests
cd projects/databricks-delta
source .venv/bin/activate
pytest tests/ -v

# Snowflake Medallion tests
cd projects/snowflake-medallion
source .venv/bin/activate
pytest tests/ -v
```

## Deploying to Dagster+

This project includes a `dagster_cloud.yaml` file for deploying to Dagster+. The configuration defines both code locations with their respective environment variables and secrets.

### Setup

1. Configure environment variables in Dagster+:
   - Add non-sensitive variables (account names, hostnames) as environment variables
   - Add sensitive values (tokens, passwords) as secrets

2. Deploy using the Dagster+ CLI or GitHub integration:

```bash
dagster-cloud workspace sync
```

For more details, see the [Dagster+ deployment documentation](https://docs.dagster.io/dagster-plus/deployment/code-locations/dagster-cloud-yaml).
