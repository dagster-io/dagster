---
title: "Components"
sidebar_position: 100
---

Welcome to Dagster Components.

Dagster Components is a new way to structure your Dagster projects. It aims to provide:

- An opinionated project layout that supports ongoing scaffolding from "Hello world" to the most advanced projects
- A class-based interface for dynamically constructing definitions
- A toolkit to build YAML DSL frontends for components so that components can be constructed in a low-code fashion.
- A format for components to provide their own scaffolding, in order to organize and reference integration-specific artifacts files.

## Project Setup

First let's install the `dg` command line tool. This lives in the published Python package `dagster-dg`. `dg` is designed to be globally installed and has no dependency on `dagster` itself. We will use the tool feature of Python package manager `uv` to install a globally available `dg`. `dg` will also be use `uv` internally to manage the Python environment associated with your project.

```bash
brew install uv && uv tool install -e -e $DAGSTER_GIT_REPO_DIR/python_modules/libraries/dagster-dg/
```

Let's have a look at what's available:

```bash
dg --help

Usage: dg [OPTIONS] COMMAND [ARGS]...

  CLI tools for working with Dagster components.

Commands:
  code-location   Commands for operating code location directories.
  component       Commands for operating on components.
  component-type  Commands for operating on components types.
  deployment      Commands for operating on deployment directories.

Options:
  --builtin-component-lib TEXT  Specify a builitin component library to use.
  --verbose                     Enable verbose output for debugging.
  --disable-cache               Disable caching of component registry data.
  --clear-cache                 Clear the cache before running the command.
  --rebuild-component-registry  Recompute and cache the set of available component types for the current environment.
                                Note that this also happens automatically whenever the cache is detected to be stale.
  --cache-dir PATH              Specify a directory to use for the cache.
  -v, --version                 Show the version and exit.
  -h, --help                    Show this message and exit.
```

We're going to generate a new code location.

```bash
dg code-location generate jaffle_platform
```

Let's have a look at what it generated:

```bash
cd jaffle_platform && tree
```

You can see that we have a basic project structure with a few non-standard files/directories:

- `jaffle_platform/components`: this is where we will define our components
- `jaffle_platform/lib`: this is where we can put custom component types
- `definitions.py`: this comes preloaded with some basic code that will scrape up and merge all the Dagster definitions from our components.

## Hello Platform

We are going to set up a data platform using sling to ingest data, dbt to process the data, and Python to do AI.

### Ingest

First we set up sling. If we query the available component-types in our code location, we don't see anything sling-related:

```bash
dg component-type list

dagster_components.pipes_subprocess_script_collection
    Assets that wrap Python scripts executed with Dagster's PipesSubprocessClient.
```

This is because the basic `dagster-components` package is lightweight and doesn't include components for specific tools. We can get access to a `sling` component by installing the `sling` extra:

```bash
uv add 'dagster-components[sling]' dagster-sling
```

Now let's see what's available:

```bash
dg component-type list

dagster_components.pipes_subprocess_script_collection
    Assets that wrap Python scripts executed with Dagster's PipesSubprocessClient.
dagster_components.sling_replication`
```

Great-- we now have the `dagster_components.sling_replication` component type available. Let's create a new instance of this component:

```bash
dg component generate dagster_components.sling_replication ingest_files

Creating a Dagster component instance folder at /Users/smackesey/stm/code/elementl/tmp/jaffle_platform/jaffle_platform/components/ingest_files.
```

This adds a component instance to the project at `jaffle_platform/components/ingest_files`:

```bash
tree jaffle_platform

jaffle_platform/
├── __init__.py
├── __pycache__
│   └── __init__.cpython-312.pyc
├── components
│   └── ingest_files
│       ├── component.yaml
│       └── replication.yaml
├── definitions.py
└── lib
    ├── __init__.py
    └── __pycache__
        └── __init__.cpython-312.pyc

6 directories, 7 files
```

Notice that our component has two files: `component.yaml` and `replication.yaml`. The `component.yaml` file is common to all Dagster components, and specifies the component type and any associated parameters. Right now the parameters are empty:

```yaml
### jaffle_platform/components/ingest_files/component.yaml
component_type: dagster_components.sling_replication

params: {}
```

The `replication.yaml` file is a sling-specific file.

We want to replicate data on the public internet into DuckDB:

```bash
uv run sling conns set DUCKDB type=duckdb instance=/tmp/jaffle_platform.duckdb

4:55PM INF connection `DUCKDB` has been set in /Users/smackesey/.sling/env.yaml. Please test with `sling conns test DUCKDB`
```

```bash
uv run sling conns test DUCKDB

4:55PM INF success!
```

Now let's download a file locally (sling doesn't support reading from the public internet):

```bash
curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv &&
curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv &&
curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv
```

And copy-paste the below code into `replication.yaml`:

```yaml
source: LOCAL
target: DUCKDB

defaults:
  mode: full-refresh
  object: "{stream_table}"

streams:
  file://raw_customers.csv:
    object: "main.raw_customers"
  file://raw_orders.csv:
    object: "main.raw_orders"
  file://raw_payments.csv:
    object: "main.raw_payments"
```

Let's load up our code location in the Dagster UI to see what we've got:

```bash
uv run dagster dev # will be dg dev in the future
```

Click "Materialize All", and we should now have tables in the DuckDB instance. Let's verify on the command line:

```
brew install duckdb
duckdb /tmp/jaffle_platform.duckdb -c "SELECT * FROM raw_customers LIMIT 5;"
┌───────┬────────────┬───────────┬──────────────────┐
│  id   │ first_name │ last_name │ _sling_loaded_at │
│ int32 │  varchar   │  varchar  │      int64       │
├───────┼────────────┼───────────┼──────────────────┤
│     1 │ Michael    │ P.        │       1734732030 │
│     2 │ Shawn      │ M.        │       1734732030 │
│     3 │ Kathleen   │ P.        │       1734732030 │
│     4 │ Jimmy      │ C.        │       1734732030 │
│     5 │ Katherine  │ R.        │       1734732030 │
└───────┴────────────┴───────────┴──────────────────┘
```
