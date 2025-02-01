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
deployment-level settings and a `code_locations` directory containing one or
more code locations. A deployment does _not_ define a Python environment by
default. Instead, Python environments are defined per code location.

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
├── code_locations
└── pyproject.toml
└── workspace.yaml
```

Importantly, the `pyproject.toml` file contains an `is_deployment` setting
marking this directory as a deployment:

```toml
### pyproject.toml

[tool.dg]
is_deployment = true
```

The workspace.yaml file specifies the code locations to load when running
`dagster dev`. Because we don't have any code locations yet, it's empty except
for an example comment:

```yaml
# This file contains the configuration for the workspace-- it should contain an entry in `load_from`
# for each code location.
#
# ##### EXAMPLE
# 
# load_from:
#   - python_file:
#       relative_path: code_locations/my-code-location/my_code_location/definitions.py
#       location_name: my_code_location
#       executable_path: code_locations/my-code-location/.venv/bin/python
```

To add a code location to the deployment, run:

```bash
$ dg code-location scaffold code-location-1

Creating a Dagster code location at .../my-deployment/code_locations/code-location-1.
Scaffolded files for Dagster project in .../my-deployment/code_locations/code-location-1.
...
```

This will create a new directory `code-location-1` within the `code_locations`.
It will also setup a new uv-managed Python environment for the code location. Let's have a look:

```bash
$ tree

├── code_locations
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

:::note
`code-location-1` also contains a virtual environment directory `.venv` that is
not shown above. This environment is managed by `uv` and its contents are
specified in the `uv.lock` file.
:::

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

We can also see that the `workspace.yaml` file has been updated to include the
new code location:

```yaml
load_from:
  - python_file:
      relative_path: code_locations/code-location-1/code_location_1/definitions.py
      location_name: code_location_1
      executable_path: code_locations/code-location-1/.venv/bin/python
```

Let's enter this directory and search for registered component types:

```bash
$ cd code_locations/code-location-1 && dg component-type list

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component Type                                        ┃ Summary                                                         ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ dagster_components.definitions                        │ Wraps an arbitrary set of Dagster definitions.                  │
│ dagster_components.pipes_subprocess_script_collection │ Assets that wrap Python scripts executed with Dagster's         │
│                                                       │ PipesSubprocessClient.                                          │
└───────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────┘
```

This is the default set of component types available in every new code
location. We can add to it by installing `dagster-components[sling]`:

```bash
$ uv add dagster-components[sling]
```

And now we have a new available component:

```bash
$ dg component-type list

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component Type                                        ┃ Summary                                                         ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ dagster_components.definitions                        │ Wraps an arbitrary set of Dagster definitions.                  │
│ dagster_components.pipes_subprocess_script_collection │ Assets that wrap Python scripts executed with Dagster's         │
│                                                       │ PipesSubprocessClient.                                          │
│ dagster_components.sling_replication_collection       │ Expose one or more Sling replications to Dagster as assets.     │
└───────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────┘
```

As stated above, environments are scoped per code location.  `dg` commands will
only use the environment of `code-location-1` when we are inside the
`code-location-1` directory.

Let's create another code location to demonstrate this:

```bash
$ cd ../.. && dg code-location scaffold code-location-2

Creating a Dagster code location at .../my-deployment/code_locations/code-location-2.
Scaffolded files for Dagster project in .../my-deployment/code_locations/code-location-2.
```

Now we have two code locations. We can list them with:

```bash
$ dg code-location list

code-location-1
code-location-2
```

And finally, let's check the available component types in `code-location-2`:

```bash
$ cd code_locations/code-location-2 && dg component-type list

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component Type                                        ┃ Summary                                                         ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ dagster_components.definitions                        │ Wraps an arbitrary set of Dagster definitions.                  │
│ dagster_components.pipes_subprocess_script_collection │ Assets that wrap Python scripts executed with Dagster's         │
│                                                       │ PipesSubprocessClient.                                          │
└───────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────┘
```

As you can see, we are back to only the default list of component types. This
is because we are now using the environment of `code-location-2`, in which we
have not installed `dagster-components[sling]`.

For a final step, let's load up our two code locations with `dagster dev`.
Since `dg code-location scaffold` automatically updates it, our
`workspace.yaml` should already look like this:

```yaml
load_from:
  - python_file:
      relative_path: code_locations/code-location-1/code_location_1/definitions.py
      location_name: code_location_1
      executable_path: code_locations/code-location-1/.venv/bin/python
  - python_file:
      relative_path: code_locations/code-location-2/code_location_2/definitions.py
      location_name: code_location_2
      executable_path: code_locations/code-location-2/.venv/bin/python
```

And finally we'll run `dagster dev` to see your two code locations loaded up in the
UI. You may already have `dagster` installed in the ambient environment, in
which case plain `dagster dev` will work. But in case you don't, we'll run
`dagster dev` using `uv`, which will pull down and run `dagster` for you in
an isolated environment. Make sure you are in the code location root directory
and run (it will automatically pick up your `workspace.yaml`):

```
uv tool run --with=dagster-webserver dagster dev
```


![](/images/guides/build/projects-and-components/setting-up-a-deployment/two-code-locations.png)

:::note
`dg` is currently under heavy development. In the future we will provide a `dg
dev` command that handles pulling down `dagster` for you in the background.
:::
