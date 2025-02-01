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

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/1-deployment-scaffold.txt" language="Bash" />


This will create a new directory `my-deployment`. Let's look at the structure:


<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/2-tree.txt" language="Bash" />


Importantly, the `pyproject.toml` file contains an `is_deployment` setting
marking this directory as a deployment:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/3-pyproject.toml" language="TOML" name="pyproject.toml" />

To add a code location to the deployment, run:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/4-code-location-scaffold.txt" language="Bash" />


This will create a new directory `code-location-1` within the `code_locations`.
It will also setup a new uv-managed Python environment for the code location. Let's have a look:


<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/5-tree.txt" language="Bash" />



:::note
`code-location-1` also contains a virtual environment directory `.venv` that is
not shown above. This environment is managed by `uv` and its contents are
specified in the `uv.lock` file.
:::

The `code-location-1` directory contains a `pyproject.toml` file that defines
it as a code location and component library:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/6-code-location-pyproject.toml" language="TOML" name="code_locations/code-location-1/pyproject.toml" />


Let's enter this directory and search for registered component types:


<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/7-component-type-list.txt" language="Bash" />


This is the default set of component types available in every new code
location. We can add to it by installing `dagster-components[sling]`:

```bash
$ uv add dagster-components[sling]
```

And now we have a new available component:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/8-component-type-list.txt" language="Bash" />


As stated above, environments are scoped per code location.  `dg` commands will
only use the environment of `code-location-1` when we are inside the
`code-location-1` directory.

Let's create another code location to demonstrate this:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/9-code-location-scaffold.txt" language="Bash" />


Now we have two code locations. We can list them with:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/10-code-location-list.txt" language="Bash" />



And finally, let's check the available component types in `code-location-2`:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/11-component-type-list.txt" language="Bash" />



As you can see, we are back to only the default list of component types. This
is because we are now using the environment of `code-location-2`, in which we
have not installed `dagster-components[sling]`.

For a final step, let's load up our two code locations with `dagster dev`.
We'll need a workspace.yaml to do this. Create a new file `workspace.yaml` in
the `my-deployment` directory:


<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/12-workspace.yaml" language="YAML" name="workspace.yaml" />



And finally we'll run `dagster dev` to see your two code locations loaded up in the
UI. You may already have `dagster` installed in the ambient environment, in
which case plain `dagster dev` will work. But in case you don't, we'll run
`dagster dev` using `uv`, which will pull down and run `dagster` for you in
an isolated environment:

```
uv tool run --with=dagster-webserver dagster dev
```


![](/images/guides/build/projects-and-components/setting-up-a-deployment/two-code-locations.png)

:::note
`dg` scaffolding functionality is currently under heavy development. In the
future we will construct this workspace.yaml file for you automatically in the
course of scaffolding code locations, and provide a `dg dev` command that
handles pulling down `dagster` for you in the background.
:::
