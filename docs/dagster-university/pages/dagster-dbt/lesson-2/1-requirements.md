---
title: "Lesson 2: Setup requirements"
module: 'dagster_dbt'
lesson: '2'
---

## Setup requirements

To complete this course, you’ll need:

- **To install git.** Refer to the [Git documentation](https://github.com/git-guides/install-git) if you don’t have this installed.
- **To have Python installed.**  Dagster supports Python 3.9 - 3.12.
- **To install a package manager like pip or poetry**. If you need to install a package manager, refer to the following installation guides:
  - [pip](https://pip.pypa.io/en/stable/installation/)
  - [Poetry](https://python-poetry.org/docs/)

   To check that Python and the pip or Poetry package manager are already installed in your environment, run:

   ```shell
   python --version
   pip --version
   ```
- **To install `dagster` locally.** We'll be using part of the Dagster CLI to generate a project for us, so we'll need to install it first. Run the following:

  ```shell
  pip install dagster
  dagster --version
  ```

---

## Clone the Dagster University project

Even if you’ve already completed the Dagster Essentials course, you should still clone the project as some things may have changed.

Run the following to clone the project:

```bash
dagster project from-example --name dagster-and-dbt --example project_du_dbt_starter
```