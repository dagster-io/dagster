## Dagster University: Dagster + dbt

This is the **starter** version of the [Dagster](https://dagster.io/) project made to accompany Dagster University's [Dagster + dbt course](https://courses.dagster.io/courses/dagster-dbt).

> **Looking for the finished project for the Dagster + dbt course?** Use the [`module/dagster-and-dbt` branch](https://github.com/dagster-io/project-dagster-university/tree/module/dagster-and-dbt).

## Getting started

First, install your Dagster code location as a Python package. By using the --editable flag, pip will install your Python package in ["editable mode"](https://pip.pypa.io/en/latest/topics/local-project-installs/#editable-installs) so that as you develop, local code changes will automatically apply.

```bash
pip install -e ".[dev]"
```

Duplicate the `.env.example` file and rename it to `.env`. Then, fill in the values for the environment variables in the file.

Then, start the Dagster UI web server:

```bash
dagster dev
```

Open http://localhost:3000 with your browser to see the project.

## Development

### Adding new Python dependencies

You can specify new Python dependencies in `setup.py`.

### Unit testing

Tests are in the `dagster_university_tests` directory and you can run tests using `pytest`:

```bash
pytest dagster_university_tests
```

### Schedules and sensors

If you want to enable Dagster [Schedules](https://docs.dagster.io/guides/automate/schedules/) or [Sensors](https://docs.dagster.io/guides/automate/sensors/) for your jobs, the [Dagster Daemon](https://docs.dagster.io/guides/deploy/execution/dagster-daemon) process must be running. This is done automatically when you run `dagster dev`.

Once your Dagster Daemon is running, you can start turning on schedules and sensors for your jobs.

## Deploy on Dagster+

The easiest way to deploy your Dagster project is to use Dagster+.

Check out the [Dagster+ documentation](https://docs.dagster.io/dagster-plus/) to learn more.
