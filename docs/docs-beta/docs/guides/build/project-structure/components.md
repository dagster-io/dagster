---
title: "Components"
sidebar_position: 100
unlisted: true
---

Welcome to Dagster Components.

Dagster Components is a new way to structure your Dagster projects. It aims to provide:

- An opinionated project layout that supports ongoing scaffolding from "Hello world" to the most advanced projects.
- A class-based interface (`Component`) for dynamically constructing Dagster definitions from arbitrary data (such as third-party integration configuration files).
- A toolkit for buildng YAML DSLs for `Components`, allowing instances of components to be defined with little to no Python code.
- A Dagster-provided set of component types that provide a simplified user experience for common integrations.

## Project Setup

First let's install some tools. The centerpiece of this tutorial is the `dg` command line tool, which lives in the published Python package `dagster-dg`. `dg` is designed to be globally installed and has no dependency on `dagster` itself. `dg` allows us to quickly scaffold Dagster code locations and populate them with components. We will use Python package manager [`uv`](https://docs.astral.sh/uv/) to install a globally available `dg`.

We'll install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) and install two other tools used in this tutorial: [`duckdb`](https://duckdb.org/docs/installation/?version=stable&environment=cli&platform=macos&download_method=package_manager) for a local database, and [`tree`](https://oldmanprogrammer.net/source.php?dir=projects/tree/INSTALL) for visualizing project structure. We will assume we are on a Mac and install using `brew`-- if you are on another platform, follow the preceding links to see the installation instructions. Note that `tree` is strictly optional and is only used to produce an easily understandable representation of the project structure on the CLI. `find`, `ls` or any other directory listing command will also work.

```bash
$ brew install uv duckdb tree
```

Now that we have `uv`, we can install `dg`:

```bash
$ uv tool install dagster-dg
```

`uv tool install` installs python packages from PyPI into isolated environments and exposes their executables on your shell path. This means the `dg` command should now be available. It will always execute in an isolated environment separate from any project environment.

Let's take a look at the help message for `dg`:

```bash
$ dg --help

Usage: dg [OPTIONS] COMMAND [ARGS]...

  CLI for working with Dagster components.

Commands:
  code-location   Commands for operating code location directories.
  component       Commands for operating on components.
  component-type  Commands for operating on components types.
  deployment      Commands for operating on deployment directories.

Options:
  --clear-cache                 Clear the cache.
  --rebuild-component-registry  Recompute and cache the set of available component types for the current environment.
                                Note that this also happens automatically whenever the cache is detected to be stale.
  -v, --version                 Show the version and exit.
  -h, --help                    Show this message and exit.

Global options:
  --use-dg-managed-environment / --no-use-dg-managed-environment
                                  Enable management of the virtual environment with uv.
  --builtin-component-lib TEXT    Specify a builitin component library to use.
  --verbose                       Enable verbose output for debugging.
  --disable-cache                 Disable the cache..
  --cache-dir PATH                Specify a directory to use for the cache.
```

We want to scaffold a new code location:

```bash
$ dg code-location scaffold jaffle-platform

Creating a Dagster code location at .../jaffle-platform.
Scaffolded files for Dagster project in .../jaffle-platform.
Using CPython 3.12.4
Creating virtual environment at: .venv
Resolved 73 packages in 398ms
   Built jaffle-platform @ file:///.../jaffle-platform
...
```

This built a code location at `jaffle-platform` and initialized a new Python
virtual environment inside of it. When using `dg`'s default environment
management behavior, you won't need to worry about activating this virtual environment yourself.

Let's have a look at the scaffolded files:

```bash
$ cd jaffle-platform && tree

.
├── jaffle_platform
│   ├── __init__.py
│   ├── components
│   ├── definitions.py
│   └── lib
│       ├── __init__.py
├── jaffle_platform.egg-info
│   ├── PKG-INFO
│   ├── SOURCES.txt
│   ├── dependency_links.txt
│   ├── entry_points.txt
│   ├── requires.txt
│   └── top_level.txt
├── jaffle_platform_tests
│   └── __init__.py
├── pyproject.toml
└── uv.lock

8 directories, 15 files
```

You can see that we have a fairly standard Python project structure. There is a
python package `jaffle_platform`-- the name is an underscored inflection of the
project root directory (`jaffle_platform`). There is also an (empty)
`jaffle_platform_tests` test package, a `pyproject.toml`, and a `uv.lock`. The
`pyproject.toml` contains a `tool.dagster` and `tool.dg` section that look like
this:

```toml
[tool.dagster]
module_name = "jaffle_platform.definitions"
project_name = "jaffle_platform"

[tool.dg]
is_code_location = true
is_component_lib = true
```

The `tool.dagster` section is not `dg`-specific, it specifies that a set of definitions can be loaded from the `jaffle_platform.definitions` module. The `tool.dg` section contains two settings requiring more explanation.

`is_code_location = true` specifies that this project is a `dg`-managed code location. This is just a regular Dagster code location that has been structured in a particular way. Let's look at the content of `jaffle_platform/definitions.py`:

```python
from pathlib import Path

from dagster_components import build_component_defs

defs = build_component_defs(code_location_root=Path(__file__).parent.parent)
```

This call to `build_component_defs` will:

- discover the set of components defined in the project
- compute a set of `Definitions` from each component
- merge the component-specific definitions into a single `Definitions` object

`is_code_location` is telling `dg` that the project is structured in this way and therefore contains component instances. In the current project, component instances will be placed in the default location at `jaffle_platform/components`.

`is_component_lib = true` specifies that the project is a component library.
This means that the project may contain component types that can be referenced
when generating component instances. In a typical code location most components
are likely to be instances of types defined in external libraries (e.g.
`dagster-components`), but it can also be useful to define custom component
types scoped to the project. That is why `is_component_lib` is set to `true` by
default. Any scaffolded component types in `jaffle_platform` will be placed in
the default location at `jaffle_platform/lib`. You can also see that this
module is registered under the `dagster.components` entry point in
`pyproject.toml`. This is what makes the components discoverable to `dg`:

```toml
[project.entry-points]
"dagster.components" = { jaffle_platform = "jaffle_platform.lib"}
```

Now that we've got a basic scaffold, we're ready to start building components. We are going to set up a data platform using Sling to ingest data and DBT to process the data. We'll then automate the daily execution of our pipeline using Dagster automation conditions.

## Ingest

First let's set up Sling. If we query the available component types in our environment, we don't see anything Sling-related:

```bash
$ dg component-type list

dagster_components.definitions
dagster_components.pipes_subprocess_script_collection
    Assets that wrap Python scripts executed with Dagster's PipesSubprocessClient.
```

This is because the basic `dagster-components` package (which was installed when we scaffolded our code location) is lightweight and doesn't include components for specific integrations (like Sling). We can get access to a Sling component by installing the `sling` extra of `dagster-components`:

:::note
Recall that `dg` always operates in an isolated environment-- so how is it able to access the set of components types available in our project environment? Under the hood, `dg` attempts to resolve a project root whenever it is run. If it finds a `pyproject.toml` file with a `tool.dg.is_code_location = true` setting, then it will by default expect a `uv`-managed virtual environment to be present in the same directory (this can be confirmed by the presence of a `uv.lock` file). When you run commands like `dg component-type list`, `dg` obtains the results by identifying the in-scope project enviroment and querying it. In this case, the project environment was set up for us as part of the `dg code-location scaffold` command.
:::

```bash
$ uv add 'dagster-components[sling]'
```

Now let's see what component types are available:

```bash
$ dg component-type list

dagster_components.definitions
dagster_components.pipes_subprocess_script_collection
    Assets that wrap Python scripts executed with Dagster's PipesSubprocessClient.
dagster_components.sling_replication_collection
```

Great-- now we can see the `dagster_components.sling_replication` component type. Let's create a new instance of this component:

```bash
$ dg component scaffold dagster_components.sling_replication_collection ingest_files

Creating a Dagster component instance folder at .../jaffle_platform/components/ingest_files.
```

This adds a component instance to the project at `jaffle_platform/components/ingest_files`:

```bash
$ tree jaffle_platform

jaffle_platform/
├── __init__.py
├── components
│   └── ingest_files
│       └── component.yaml
├── definitions.py
└── lib
    ├── __init__.py

6 directories, 7 files
```

A single file, `component.yaml`, was created in the component folder. The `component.yaml` file is common to all Dagster components, and specifies the component type and any parameters used to scaffold definitions from the component at runtime. 

```yaml
### jaffle_platform/components/ingest_files/component.yaml

type: dagster_components.sling_replication_collection

params:
  replications:
  - path: replication.yaml
```

Right now the parameters define a single "replication"-- this is a sling concept that specifies how data should be replicated from a source to a target. The details are specified in a `replication.yaml` file that is read by Sling. This file does not yet exist-- we are going to create it shortly.

:::note
The `path` parameter for a replication is relative to the same folder containing component.yaml. This is a convention for components.
:::

But first, let's set up DuckDB:

```bash
$ uv run sling conns set DUCKDB type=duckdb instance=/tmp/jaffle_platform.duckdb

12:53PM INF connection `DUCKDB` has been set in /Users/smackesey/.sling/env.yaml. Please test with `sling conns test DUCKDB`

$ uv run sling conns test DUCKDB

12:53PM INF success!
```

Now let's download some files locally to use our Sling source (Sling doesn't support reading from the public internet):

```bash
curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv &&
curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv &&
curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv
```

And finally create `replication.yaml` referencing the downloaded files:

```yaml
### jaffle_platform/components/ingest_files/replication.yaml

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

![](/images/guides/build/projects-and-components/components/sling.png)

Click "Materialize All", and we should now have tables in the DuckDB instance. Let's verify on the command line:

```
$ duckdb /tmp/jaffle_platform.duckdb -c "SELECT * FROM raw_customers LIMIT 5;"

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

## Transform

We'll now download a pre-existing sample DBT project from github. We're going to use the data we are ingesting with Sling as an input for the DBT project. Clone the project (and delete the embedded git repo):

```bash
$ git clone --depth=1 https://github.com/dagster-io/jaffle_platform.git dbt && rm -rf dbt/.git
```

We'll need to create a Dagster DBT project component to interface with the dbt project. We can access the DBT project component by installing `dagster-components[dbt]` and `dbt-duckdb`:

```bash
$ uv add "dagster-components[dbt]" dbt-duckdb 
$ dg component-type list

dagster_components.dbt_project
dagster_components.definitions
dagster_components.pipes_subprocess_script_collection
    Assets that wrap Python scripts executed with Dagster's PipesSubprocessClient.
dagster_components.sling_replication_collection
```

There it is: `dagster_components.dbt_project`. We can access detailed info about a component type using the `dg component-type info` command. Let's have a look at the `dagster_components.dbt_project` component type:

```bash
$ dg component-type info dagster_components.dbt_project

dagster_components.dbt_project

Scaffold params schema:

{
    "properties": {
        "init": {
            "default": false,
            "title": "Init",
            "type": "boolean"
        },
        "project_path": {
            "anyOf": [
                {
                    "type": "string"
                },
                {
                    "type": "null"
                }
            ],
            "default": null,
            "title": "Project Path"
        }
    },
    "title": "DbtScaffoldParams",
    "type": "object"
}

Component params schema:

...
```

The output of the above command shows the parameters (in JSON schema format) for both component generation and runtime loading of the component (the runtime parameters have been truncated here due to length).

Let's scaffold a new instance of the `dagster_components.dbt_project` component, providing the path to the dbt project we cloned earlier as the `project_path` scaffold paramater. We can pass this on the command line:

```bash
$ dg component scaffold dagster_components.dbt_project jdbt --project-path dbt/jdbt

Creating a Dagster component instance folder at .../jaffle_platform/components/jdbt.
```

This creates a new component instance in the project at `jaffle_platform/components/jdbt`. Open `component.yaml` and you'll see:

```yaml
type: dagster_components.dbt_project

params:
  dbt:
    project_dir: ../../../dbt/jdbt
```

Let’s see the project in the Dagster UI:

```bash
uv run dagster dev
```

![](/images/guides/build/projects-and-components/components/dbt-1.png)

You can see at first glance that there appear to be two copies of the `raw_customers`, `raw_orders`, and `raw_payments` tables. This isn't right-- if you click on the assets you can see their full asset keys. The keys generated by the DBT component are of the form `main/*` where the keys generated by the Sling component are of the form `target/main/*`. We need to update the configuration of the `dagster_components.dbt_project` component to match the keys generated by the Sling component. Update `components/jdbt/component.yaml` with the below:

```yaml
type: dagster_components.dbt_project

params:
  dbt:
    project_dir: ../../../dbt/jdbt
  asset_attributes:
    key: "target/main/{{ node.name }}"
```

Reload the code location in Dagster UI and now the keys will connect properly:

![](/images/guides/build/projects-and-components/components/dbt-2.png)

Now the keys generated by the Sling and DBT project components match, and our
asset graph is correct. Click "Materialize All" to materialize the new assets
defined via the DBT project component. We can verify that this worked by
viewing a sample of the newly materialized assets from the command line:

```
$ duckdb /tmp/jaffle_platform.duckdb -c "SELECT * FROM orders LIMIT 5;"

┌──────────┬─────────────┬────────────┬───────────┬────────────────────┬───────────────┬──────────────────────┬──────────────────┬────────┐
│ order_id │ customer_id │ order_date │  status   │ credit_card_amount │ coupon_amount │ bank_transfer_amount │ gift_card_amount │ amount │
│  int32   │    int32    │    date    │  varchar  │       double       │    double     │        double        │      double      │ double │
├──────────┼─────────────┼────────────┼───────────┼────────────────────┼───────────────┼──────────────────────┼──────────────────┼────────┤
│        1 │           1 │ 2018-01-01 │ returned  │               10.0 │           0.0 │                  0.0 │              0.0 │   10.0 │
│        2 │           3 │ 2018-01-02 │ completed │               20.0 │           0.0 │                  0.0 │              0.0 │   20.0 │
│        3 │          94 │ 2018-01-04 │ completed │                0.0 │           1.0 │                  0.0 │              0.0 │    1.0 │
│        4 │          50 │ 2018-01-05 │ completed │                0.0 │          25.0 │                  0.0 │              0.0 │   25.0 │
│        5 │          64 │ 2018-01-05 │ completed │                0.0 │           0.0 │                 17.0 │              0.0 │   17.0 │
└──────────┴─────────────┴────────────┴───────────┴────────────────────┴───────────────┴──────────────────────┴──────────────────┴────────┘
```

## Automation

Now that we've defined some assets, let automate them to keep them up to date. We can do this via declarative automation directly in our yaml DSL. Navigate to `components/ingest_files/component.yaml` and update with the below:

```yaml
type: dagster_components.sling_replication_collection

params:
  replications:
    - path: replication.yaml
  asset_attributes:
    - target: "*"
	    attributes:
        automation_condition: "{{ automation_condition.on_cron('@daily') }}"
        metadata: 
          automation_condition: "on_cron(@daily)" 
```

This will automatically pull in data with sling each day. Now we want to make
the dbt project execute after our sling replication runs. Update
`components/jdbt/component.yaml` with the below:

```yaml
type: dagster_components.dbt_project

params:
  dbt:
    project_dir: ../../../dbt/jdbt
  asset_attributes:
    key: "target/main/{{ node.name }}"
  transforms:
    - target: "*"
      attributes:
        automation_condition: "{{ automation_condition.eager() }}"
      metadata: 
        automation_condition: "eager"
```

Now the DBT project will update automatically after the Sling replication runs.

---

This concludes the Components tutorial. Components is under heavy development and more documentation is coming soon.
