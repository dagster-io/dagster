---
title: "Setting up a deployment"
sidebar_position: 200
unlisted: true
displayed_sidebar: 'components'
---

Many users will want to manage multiple code locations within a single coherent
directory structure. `dg` facilitates this with the concept of a _deployment_
directory.

A deployment directory contains a root `pyproject.toml` containing
deployment-level settings and a `code-locations` directory containing one or
more code locations. A deployment does _not_ define a Python environment by
default-- instead, Python environments are defined per code location.

To scaffold a new deployment, run:

```bash
$ dg deployment scaffold my-deployment

Creating a Dagster deployment at my-deployment.
Scaffolded files for Dagster project in my-deployment.
```

This will create a new directory `my-deployment`. Let's look at the structure:

```bash
$ cd my-deployment && tree

.
├── code-locations
└── pyproject.toml
```

Importantly, the `pyproject.toml` file contains an `is_deployment` setting
marking this directory as a deployment:

```toml
### pyproject.toml

[tool.dg]
is_deployment = true
```

To add a code location to the deployment, run:

```bash
$ dg code-location scaffold code-location-1

Creating a Dagster code location at .../my-deployment/code-locations/code-location-1.
Scaffolded files for Dagster project in .../my-deployment/code-locations/code-location-1.
...
```

This will create a new directory `code-location-1` within the `code-locations`.
It will also setup a new uv-managed Python environment for the code location. Let's have a look:

```bash
$ tree

├── code-locations
│   └── code-location-1
│       ├── code_location_1
│       │   ├── __init__.py
│       │   ├── components
│       │   ├── definitions.py
│       │   └── lib
│       │       ├── __init__.py
│       ├── code_location_1_tests
│       │   └── __init__.py
│       ├── pyproject.toml
│       └── uv.lock
└── pyproject.toml
```

The `code-location-1` directory contains a `pyproject.toml` file that defines
it as a code location and component library:

```toml
[tool.dagster]
module_name = "code_location_1.definitions"
project_name = "code_location_1"

[tool.dg]
is_code_location = true
is_component_lib = true
```

Let's enter this directory and search for registered component types:

```bash
$ cd code_locations/code-location-1 && dg component-type list

dagster_components.definitions
dagster_components.pipes_subprocess_script_collection
    Assets that wrap Python scripts executed with Dagster's PipesSubprocessClient.
```

This is the default set of component types available in every new code
location. We can add to it by installing `dagster-components[dbt]`:

```bash
$ uv add dagster-components[sling]
```

And now we have a new available component:

```bash
$ dg component-type list

dagster_components.definitions
dagster_components.pipes_subprocess_script_collection
    Assets that wrap Python scripts executed with Dagster's PipesSubprocessClient.
dagster_components.sling_replication_collection
```

As stated above, environments are scoped per code location.  `dg` commands will
only use the environment of `code-location-1` when we are inside the
`code-location-1` directory.

Let's create another code location to demonstrate this:

```bash
$ cd ../.. && dg code-location scaffold code-location-2

Creating a Dagster code location at .../my-deployment/code-locations/code-location-2.
Scaffolded files for Dagster project in .../my-deployment/code-locations/code-location-2.
```

Now we have two code locations. We can list them with:

```bash
$ dg code-location list

code-location-1
code-location-2
```

And finally, let's check the available component types in `code-location-2`:

```bash
$ cd code-locations/code-location-2 && dg component-type list

dagster_components.definitions
dagster_components.pipes_subprocess_script_collection
    Assets that wrap Python scripts executed with Dagster's PipesSubprocessClient.
```

As you can see, we are back to only the default list of component types. This
is because we are now using the environment of `code-location-2`, in which we
have not installed `dagster-components[sling]`.
