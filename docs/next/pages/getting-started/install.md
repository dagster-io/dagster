---
title: Installing Dagster | Dagster Docs
description: Install Dagster
---

# Installing Dagster

## Requirements

{% partial file="DagsterVersion.md" /%}

To check that Python and the pip package manager are already installed in your environment, you can run:

```bash
python --version
pip --version
```

Refer to the [Releases guide](/about/releases#python-version-support) for more info about how Dagster handles support for Python versions.

---

## Installing Dagster into an existing Python environment

{% note %}
**Note**: We strongly recommend installing Dagster inside a
Python virtualenv. If running Anaconda, install Dagster inside a Conda
environment.
{% /note %}

To install the latest stable version of the core Dagster packages in your current Python environment, run:

```bash
pip install dagster dagster-webserver
```

---

## Installing Dagster from source

To install Dagster from source, refer to the [Contributing guide](/community/contributing).

---

## Installing Dagster using Poetry

To install Dagster and the Dagster webserver/UI into an existing [Poetry](https://python-poetry.org) project, run:

```bash
poetry add dagster dagster-webserver
```

---

## Related

{% table %}

---

- [Creating a new Dagster project](/getting-started/create-new-project)
- [Dagster project files](/guides/understanding-dagster-project-files)

---

- [Running Dagster locally](/guides/running-dagster-locally)
- [Contributing to Dagster](/community/contributing)

{% /table %}
