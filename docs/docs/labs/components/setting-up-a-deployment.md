---
title: "Setting up a deployment"
sidebar_position: 400
pagination_next: null
---

Many users will want to manage multiple code locations within a single coherent
directory structure. `dg` facilitates this with the concept of a _deployment_
directory.

A deployment directory contains a root `pyproject.toml` containing
deployment-level settings and a `code_locations` directory containing one or
more code locations. A deployment does _not_ define a Python environment by
default. Instead, Python environments are defined per code location.

To scaffold a new deployment, run:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/1-deployment-scaffold.txt" />


This will create a new directory `my-deployment`. Let's look at the structure:


<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/2-tree.txt" />


Importantly, the `pyproject.toml` file contains an `is_deployment` setting
marking this directory as a deployment:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/3-pyproject.toml" language="TOML" title="my-deployment/pyproject.toml" />

To add a code location to the deployment, run:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/4-code-location-scaffold.txt" />


This will create a new directory `code-location-1` within the `code_locations`.
It will also setup a new uv-managed Python environment for the code location. Let's have a look:


<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/5-tree.txt" />



:::note
`code-location-1` also contains a virtual environment directory `.venv` that is
not shown above. This environment is managed by `uv` and its contents are
specified in the `uv.lock` file.
:::

The `code-location-1` directory contains a `pyproject.toml` file that defines
it as a code location and component library:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/6-code-location-pyproject.toml" language="TOML" title="my-deployment/code_locations/code-location-1/pyproject.toml" />


Let's enter this directory and search for registered component types:


<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/7-component-type-list.txt"  />


This is the default set of component types available in every new code
location. We can add to it by installing `dagster-components[sling]`:

<CliInvocationExample contents="uv add 'dagster-components[sling]'" />

:::note
Due to a bug in `sling` package metadata, if you are on a macOS machine with
Apple Silicon you may also need to run `uv add sling_mac_arm64`.
:::

And now we have a new available component:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/8-component-type-list.txt"  />


As stated above, environments are scoped per code location.  `dg` commands will
only use the environment of `code-location-1` when we are inside the
`code-location-1` directory.

Let's create another code location to demonstrate this:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/9-code-location-scaffold.txt"  />


Now we have two code locations. We can list them with:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/10-code-location-list.txt"  />



And finally, let's check the available component types in `code-location-2`:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/deployments/11-component-type-list.txt"  />



As you can see, we are back to only the default list of component types. This
is because we are now using the environment of `code-location-2`, in which we
have not installed `dagster-components[sling]`.

For a final step, let's load up our two code locations with `dg dev`. `dg dev`
will automatically recognize the code locations in your deployment and launch
them in their respective environments. Let's run `dg dev` back in the
deployment root directory and load up the Dagster UI in your browser:

<CliInvocationExample contents="cd ../.. && dg dev" />

![](/images/guides/build/projects-and-components/setting-up-a-deployment/two-code-locations.png)
