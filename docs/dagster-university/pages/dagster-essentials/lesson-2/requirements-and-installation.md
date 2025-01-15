---
title: 'Lesson 2: Requirements and installation'
module: 'dagster_essentials'
lesson: '2'
---

## Requirements

To install Dagster, you’ll need:

- **To install Python**. Dagster supports Python 3.9 through 3.12.
- **A package manager like pip, Poetry, or uv**. If you need to install a package manager, refer to the following installation guides:
  - [pip](https://pip.pypa.io/en/stable/installation/)
  - [Poetry](https://python-poetry.org/docs/)
  - [uv](https://docs.astral.sh/uv/getting-started/installation/)

To check that Python and the package manager are already installed in your environment, run:

```shell
python --version
pip --version
```

---

## Installation

{% callout %}
💡 **Heads up!** We strongly recommend installing Dagster inside a Python virtual environment. If you need a primer on virtual environments, including creating and activating one, check out this [blog post](https://dagster.io/blog/python-packages-primer-2).
{% /callout %}

To install Dagster into your current Python environment:

```shell
pip install dagster~=1.9
```
