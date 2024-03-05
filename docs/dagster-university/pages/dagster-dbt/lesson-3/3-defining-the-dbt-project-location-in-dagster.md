---
title: 'Lesson 3: Defining the dbt project location in Dagster'
module: 'dagster_dbt'
lesson: '3'
---

# Defining the dbt project location in Dagster

As you’ll frequently point your Dagster code to the `target/manifest.json` file and your dbt project in this course, it’ll be helpful to keep a reusable constant to reference where the dbt project is.

In the finished Dagster Essentials project, there should be a file called `assets/constants.py`. Open that file and add the following import at the top:

```python
from pathlib import Path
# import os
```

The `Path` class from the `pathlib` standard library will help us create an accurate pointer to where our dbt project is. At the bottom of `constants.py`, add the following line:

```python
DBT_DIRECTORY = Path(__file__).joinpath("..", "..", "..", "analytics").resolve()
```

This line creates a new constant called `DBT_DIRECTORY`. This line might look a little complicated, so let’s break it down:

- It uses the location of the `constants.py` file (via `__file__`) as a point of reference for finding the dbt project
- The arguments in `joinpath` point us towards our dbt project by appending the following to the current path:
   - Three directory levels up (`"..", "..", ".."`)
   - A directory named `analytics`, which is the directory containing our dbt project
- The `resolve` method turns that path into an absolute file path that points to the dbt project correctly from any file we’re working in

Now that you can access your dbt project from any other file with the `DBT_DIRECTORY` constant, let’s move on to the first place where you’ll use it: creating the Dagster resource that will run dbt.