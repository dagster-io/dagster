---
title: Installing Dagster | Dagster Docs
description: Install Dagster
---
# {% $markdoc.frontmatter.title %}

## Requirements

{% partial file="DagsterVersion.md" /%}

To check that Python and the pip package manager are already installed in your environment, you can run:

```bash
python --version
pip --version
```

### test right side bar

---

## Installing Dagster into an existing Python environment

<Note>
  <strong>Note</strong>: We strongly recommend installing Dagster inside a
  Python virtualenv. If running Anaconda, install Dagster inside a Conda
  environment.
</Note>

To install the latest stable version of the core Dagster packages in your current Python environment, run:

```bash
pip install dagster dagit
```

**Using a Mac with an M1 or M2 chip**? Some users have reported installation errors due to missing wheels for arm64 Macs when installing the `grpcio` package. You can avoid these errors by installing `dagster` using our pre-built wheel of the `grpcio` package for M1 and M2 machines:

```bash
pip install dagster dagit --find-links=https://github.com/dagster-io/build-grpcio/wiki/Wheels
```

---

## Installing Dagster from source

To install Dagster from source, refer to the [Contributing guide](/community/contributing).

---

## Installing Dagster using Poetry

To install Dagster and Dagit into an existing [Poetry](https://python-poetry.org) project, run:

```bash
poetry add dagster dagit
```

**Using a Mac with an M1 or M2 chip**? Some users have reported installation problems due to missing wheels for arm64 Macs when installing the `grpcio` package. You can avoid these errors by installing `dagster` using our pre-built wheel of the `grpcio` package for M1 and M2 machines:

```bash
poetry source add grpcio https://github.com/dagster-io/build-grpcio/wiki/Wheels
poetry add dagster dagit
```

---

## Related

<ArticleList>
  <ArticleListItem
    title="Creating a new Dagster project"
    href="/getting-started/create-new-project"
  ></ArticleListItem>
  <ArticleListItem
    title="Dagster project files"
    href="/getting-started/project-file-reference"
  ></ArticleListItem>
  <ArticleListItem
    title="Running Dagster locally"
    href="/guides/running-dagster-locally"
  ></ArticleListItem>
  <ArticleListItem
    title="Contributing to Dagster"
    href="/community/contributing"
  ></ArticleListItem>
</ArticleList>
