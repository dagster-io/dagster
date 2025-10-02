---
title: Sharing code across code locations
description: How to share modules across code locations.
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/dagster-primary-mark.svg
---

In this example, we'll explore strategies for sharing code across Dagster [code locations](/deployment/code-locations). This is useful when you have utility functions, factories, or helpers that are used in multiple places and you want to avoid duplication.

### Problem: Sharing modules across code locations

Imagine you’ve implemented a factory function that generates assets. This function is needed in multiple code locations, but you don’t want to re-implement it in every repo.

Suppose the shared module has the following structure:

```
.
├── pyproject.toml
└── src
    └── shared
        ├── __init__.py
        └── factory.py
```

With a single function `asset_factory`:

<CodeExample
  path="docs_projects/project_mini/shared/src/shared/factory.py"
  language="python"
  title="src/shared/factory.py"
/>

To reuse this factory function in multiple code locations, you can either colocate the code if it lives in the same repo, or use Git submodules or an external repository if it doesn't.

### Solution 1: Colocate the code

If your code locations live in the same repository, the simplest solution is to colocate the shared code in the repo itself.

This works best when:

- All code locations live in a single repo.
- You want fast iteration without versioning overhead.

You can add the shared module as a local dependency in your `pyproject.toml`:

<CodeExample
  path="docs_projects/project_mini/pyproject.toml"
  language="yaml"
  title="pyproject.toml"
  startAfter="start_dependencies"
  endBefore="end_dependencies"
/>

And reference it as a path dependency:

<CodeExample
  path="docs_projects/project_mini/pyproject.toml"
  language="yaml"
  title="pyproject.toml"
  startAfter="start_uv_sources"
  endBefore="end_uv_sources"
/>

Then, inside your code location, you can import and use the shared factory:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/shared_module/shared_module.py"
  language="python"
  title="src/project_mini/defs/assets.py"
/>

### Solution 2: Include the code as a Git submodule

If each code location exists in its own repository, colocating isn’t an option. Instead, you can maintain the shared library in a separate repository and include it as a Git submodule in each code location repo.

This works best when:

- Each code location lives in its own repo.
- You want to ensure the shared library is always available but don’t need fine-grained versioning.

To add the submodule:

```bash
git submodule add git@github.com:my-org/shared.git shared
git commit -am "Add shared submodule"
```

When cloning a repo with submodules:

```bash
git clone --recurse-submodules <repo-url>
```

Or, if you already cloned:

```bash
git submodule update --init --recursive
```

During image builds, the submodule code will be packaged alongside the code location.

### Solution 3: Publish the code to a private package registry

For more flexibility and the ability to version the shared code, you can treat your shared module like a standalone library and publish it to a private package registry, such as [AWS CodeArtifact](https://aws.amazon.com/codeartifact/), [GCP Artifact Registry](https://cloud.google.com/artifact-registry/docs), or [Azure Artifacts](https://azure.microsoft.com/en-us/products/devops/artifacts) (compared to a public registry such as [PyPI](https://pypi.org/)).

This works best when:

- You want semantic versioning and upgrade control.
- Teams or projects consume the shared library independently.
- You need a single source of truth for shared code.

Then, in each code location’s `pyproject.toml`, you can pin a specific version:

```
[project]
dependencies = [
    "shared==0.1.3",
]
```

When you release a new version of the shared module, code locations can explicitly upgrade to it without risk of breaking existing deployments.
