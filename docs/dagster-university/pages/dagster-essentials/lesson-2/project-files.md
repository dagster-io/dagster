---
title: 'Lesson 2: Project files'
module: 'dagster_essentials'
lesson: '3'
---

# Project files

Now that you’ve created the Dagster project, let’s talk a bit about the files it contains. The project you created in the previous section looks something like this:

```bash
.
├── README.md
├── dagster_university/
│   ├── assets/
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   ├── metrics.py
│   │   └── trips.py
│   ├── jobs/
│   ├── partitions/
│   ├── resources/
│   ├── schedules/
│   ├── sensors/
│   └── __init__.py
├── dagster_university_tests
├── data/
│   ├── outputs/
│   ├── raw/
│   ├── requests/
│   │   └── README.md
│   └── staging/
├── .env
├── .env.example
├── pyproject.toml
├── setup.cfg
└── setup.py
```

**We’re only going to touch on a handful of files for now**, but later lessons will go over additional files in more detail.

The columns in the following table are as follows:

- **File/Directory -** The name of the file/directory
- **Context** - The reason the file/directory is in the project. Indicates that the file/directory is:
  - **Dagster -** Found in every Dagster project
  - **Dagster U** - Specifically for the project you will build during Dagster University
  - **Python** - Highly recommended as software engineering and Python best practices, but not technically required by Dagster
- **Description** - A description of what the file/directory contains or what it’s used for

{% table %}

- File/Directory {% width="20%" %}
- Context {% width="10%" %}
- Description

---

- `README.md`
- Python
- A description and starter guide for the Dagster project.

---

- `dagster_university/`
- Dagster
- A Python module that will contain your Dagster code. This directory also contains the following:
  - `__init__.py` - This file includes a `Definitions` object that defines that is loaded in your project, such as assets and sensors. This allows Dagster to load the definitions in a module. We’ll discuss this topic, and this file, later in this course.
  - Several directories, for example: `/assets`. These directories follow our recommended best practices and will be used to contain the definitions - like assets - you create in the following lessons. We’ll discuss the files they contain later, too.

---

- `dagster_university/__init__.py`
- Dagster
- Each Python module has an `__init__.py`. This root-level `__init__.py` is specifically used to import and combine the different aspects of your Dagster project. This is called defining your Code Location. You’ll learn more about this in a future lesson.

---

- `dagster_university/assets/constants.py`
- Dagster U
- A pre-made file with some string constants that you’ll reference for convenience.

---

- `dagster_university_tests/`
- Dagster
- A Python module that contains unit tests for `dagster_university`

---

- `data/`
- Dagster U
- This directory (and directories within it) is where you’ll store the data assets you’ll make during this course. In production settings, this could be Amazon S3 or a data warehouse.

---

- `.env`
- Python
- A text file containing pre-configured environment variables. We’ll talk more about this file in Lesson 6, when we cover connecting to external services.

---

- `pyproject.toml`
- Python
- A file that specifies package core metadata in a static, tool-agnostic way. This file includes a `tool.dagster` section which references the Python module with your Dagster definitions defined and discoverable at the top level. This allows you to use the `dagster dev` command to load your Dagster code without any parameters.

---

- `setup.py`
- Python
- A build script with Python package dependencies for your new project as a package. This file is used to specify dependencies.

---

- `setup.cfg`
- Python
- A file that contains option defaults for `setup.py` commands.

{% /table %}

For more info about the other files in your Dagster project, check out the [Project file reference in the Dagster Docs](https://docs.dagster.io/guides/understanding-dagster-project-files).
