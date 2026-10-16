# Dagster quickstart: HackerNews ETL

A starter Dagster project. It fetches the current top stories from HackerNews, pulls their details
into a DataFrame, and plots the most frequent words in their titles.

## Getting started

Install the dependencies:

```bash
uv sync
```

Start the Dagster UI:

```bash
dg dev
```

Open http://localhost:3000 and click **Materialize all** to run the pipeline. Fetching the stories
takes a minute or two.

## What's in this project

| Path                                   | Contents                                |
| -------------------------------------- | --------------------------------------- |
| `src/quickstart_etl/defs/assets.py`    | The three HackerNews assets             |
| `src/quickstart_etl/defs/schedules.py` | A daily schedule that materializes them |
| `src/quickstart_etl/definitions.py`    | Autoloads everything under `defs/`      |
| `tests/`                               | Tests                                   |

The assets, in dependency order:

- **`topstory_ids`** — fetches the top 100 story IDs from the HackerNews API.
- **`topstories`** — pulls the details for each story.
- **`most_frequent_words`** — counts the words in the story titles and attaches a bar chart to the
  materialization as Markdown metadata, so the plot is viewable in the UI.

## Adding to the project

Everything under `src/quickstart_etl/defs/` is loaded automatically — you do not edit
`definitions.py` to register new work. Add a Python file with assets in it, or scaffold one:

```bash
dg scaffold defs dagster.asset my_new_asset.py
```

To add a Python dependency, add it to `[project.dependencies]` in `pyproject.toml` and re-run
`uv sync`.

### Components

A component is a reusable, configurable piece of a pipeline. See which types the project can use:

```bash
dg list components
```

Scaffold an instance of one under `defs/`:

```bash
dg scaffold defs dagster.PythonScriptComponent ingest_csv
```

That writes `defs/ingest_csv/defs.yaml`, which you then fill in. Because `defs/` is autoloaded, the
component is live on the next start with no change to `definitions.py` — and the same is true of a
component added from the Dagster+ UI, which lands in this directory as a `defs.yaml` too.

Component types you write yourself live in `src/quickstart_etl/components/` and are picked up
through `registry_modules` in `pyproject.toml`, which is what makes them appear in `dg list
components` and in the Dagster+ picker.

## Testing

```bash
pytest
```

## Deploying to Dagster+

Pushing to the default branch deploys the project; opening a pull request creates a branch
deployment for it. Both are handled by `.github/workflows/dagster-plus-deploy.yml`, which runs
`dg plus deploy`.

## Learn more

- [Dagster documentation](https://docs.dagster.io/)
- [Dagster University](https://courses.dagster.io/)
- [Dagster Slack community](https://dagster.io/slack)
