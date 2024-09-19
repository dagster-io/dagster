---
title: 'Lesson 3: Representing the dbt project in Dagster'
module: 'dagster_dbt'
lesson: '3'
---

# Representing the dbt project in Dagster

As you’ll frequently point your Dagster code to the `target/manifest.json` file and your dbt project in this course, it’ll be helpful to keep a reusable representation of the dbt project. This can be easily done using the `DbtProject` class.

In the `dagster_university` directory, create a new `project.py` file and add the following imports:

```python
from pathlib import Path

from dagster_dbt import DbtProject
```

The `Path` class from the `pathlib` standard library will help us create an accurate pointer to where our dbt project is. The `DbtProject` class is imported from the `dagster_dbt` package that we installed earlier. 

After the import, add the following code: 

```python
dbt_project = DbtProject(
  project_dir=Path(__file__).joinpath("..", "..", "analytics").resolve(),
)
```

This code creates a representation of the dbt project called `dbt_project`. The code defining the location of the project directory might look a little complicated, so let’s break it down:

- The location of the `project.py` file (via `__file__`) is used as a point of reference for finding the dbt project
- The arguments in `joinpath` point us towards our dbt project by appending the following to the current path:
   - Three directory levels up (`"..", "..", ".."`)
   - A directory named `analytics`, which is the directory containing our dbt project
- The `resolve` method turns that path into an absolute file path that points to the dbt project correctly from any file we’re working in

Now that you can access your dbt project from any other file with the `dbt_project` representation, let’s move on to the first place where you’ll use it: creating the Dagster resource that will run dbt.