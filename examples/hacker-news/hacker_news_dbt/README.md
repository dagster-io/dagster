> This is the dbt project for the HackerNews pipelines.

# How To Run dbt

## Getting Started

**Install** the `dbt` CLI.

```bash
pip install dbt
dbt --version  # Check your dbt version. You should have dbt>=0.19.0
```

dbt will store config files in `~/.dbt`. **Edit** your dbt `profiles.yml` with a profile for this
project.

```bash
touch ~/.dbt/profiles.yml
# Copy the contents of `config/profiles.yml` into `~/.dbt/profiles.yml`.
```

## Development

dbt models are like tables, views, materialized views, etc. in an SQL database. You can use the
`{{ ref('model_name') }}` macro in your SQL files to reference other dbt models. This allows you
to build a DAG of models and dbt will know how to create them from source models.

**Run your models** with the following command:

```bash
dbt run
```

## Testing

[dbt Documentation on Testing](https://docs.getdbt.com/docs/building-a-dbt-project/tests)

dbt allows you to test your models in two ways:

- **Schema Tests**: specify a schema for each column in your model. See `models/schema.yml` for an
example.
- **Data Tests**: write SQL statements that returns 0 rows to signal that a test has passed. See
`tests/*.sql` for examples.

**Run your tests** with the following command:

```bash
dbt test
```
