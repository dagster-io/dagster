---
title: "Lesson 2: Requirements"
module: 'dagster_dbt'
lesson: '2'
---

## Requirements

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

## Pre-requisite experience

- **dbt familiarity** An understanding of the basics of dbt is required to complete this course. We recommend that you first complete dbt's Fundamentals course if you're a new dbt user.

- **Dagster familiarity** You'll need to know the basics of Dagster to complete this course. If you've never used Dagster before or want a refresher before getting started, check out the Dagster Essentials course.

- **Python & SQL knowledge** While you don’t need to be a Python expert to get started, you do need some Python familiarity to complete this course and use Dagster. Here are some Pythonic skills that you’ll be using, along with resources to learn about them: [Functions](https://realpython.com/defining-your-own-python-function/), [Packages and Modules](https://dagster.io/blog/python-packages-primer-1), [Decorators](https://realpython.com/primer-on-python-decorators/), and [Type Hints](https://dagster.io/blog/python-type-hinting). You won’t be writing complex SQL, but you will need to understand the concept of SELECT statements, what tables are, and how to make them. If you’d like a 5-minute crash course, here’s a short article and cheatsheet on using SQL.

## Need help?

If you'd like some assistance while working through this course, you can reach out to the Dagster community on [Slack](https://dagster.io/slack) in the `#dagster-university` channel.

---

## Clone the Dagster University project

Even if you’ve already completed the Dagster Essentials course, you should still clone the project as some things may have changed.

Run the following to clone the project:

```bash
git clone https://github.com/dagster-io/project-dagster-university -b module/dagster-and-dbt-starter dagster-and-dbt
```