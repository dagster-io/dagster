---
title: "Loading a CSV file to Snowflake"
description: "This use case demonstrates how to load a CSV file into a Snowflake table using Dagster. The objective is to automate the process of reading a CSV file and writing its contents to a Snowflake table using a COPY INTO query."
tags: ["snowflake", "csv"]
---

# Loading a CSV File to Snowflake

Learn to load a CSV file into a Snowflake table using Dagster by making use of the `COPY INTO` query.

---

## What You'll Learn

You will learn how to:

- Configure the Snowflake resource in Dagster
- Use the Snowflake resource from a Dagster asset
- Write the contents of the CSV file to Snowflake using a `COPY INTO` query

---

## Prerequisites

To follow the steps in this guide, you will need:

- To have Dagster installed. Refer to the [Dagster Installation Guide](https://docs.dagster.io/getting-started/installation) for instructions.
- A basic understanding of Dagster. Refer to the [Dagster Documentation](https://docs.dagster.io/getting-started/what-why-dagster) for more information.
- A Snowflake account and the necessary credentials to connect to your Snowflake instance.
- A CSV file that you want to load into Snowflake.

---

## Steps to Implement With Dagster

By following these steps, you will have a Dagster asset that successfully reads a CSV file and writes its contents to a Snowflake table.

### Step 1: Install the Snowflake Integration

```bash
pip install dagster-snowflake
```

### Step 2: Define the Snowflake Resource

First, define the Snowflake resource in Dagster. This resource will be used to connect to your Snowflake instance.

```python
from dagster import EnvVar
from dagster_snowflake import SnowflakeResource


snowflake = SnowflakeResource(
    account=EnvVar("SNOWFLAKE_ACCOUNT"),
    user=EnvVar("SNOWFLAKE_USER"),
    password=EnvVar("SNOWFLAKE_PASSWORD"),
    warehouse=EnvVar("SNOWFLAKE_WAREHOUSE"),
    database=EnvVar("SNOWFLAKE_DATABASE"),
    schema=EnvVar("SNOWFLAKE_SCHEMA"),
    role=EnvVar("SNOWFLAKE_ROLE"),
)
```

### Step 3: Define the Asset to Read and Load the CSV File

Next, define the Dagster asset that reads the CSV file and writes its contents to a Snowflake table using a COPY INTO query.

```python
from dagster import AssetExecutionContext, Definitions, EnvVar, asset
from dagster_snowflake import SnowflakeResource


@asset
def load_csv_to_snowflake(context: AssetExecutionContext, snowflake: SnowflakeResource):

    file_name = "example.csv"
    file_path = Path(__file__).parent / file_name
    table_name = "example_table"

    create_format = """
    create or replace file format csv_format
        type = 'CSV',
        field_optionally_enclosed_by = '"'
    """

    create_stage = """
    create or replace stage temporary_stage
        file_format = csv_format
    """

    put_file = f"""
    put 'file://{file_path}' @temporary_stage
        auto_compress=TRUE
    """

    create_table = f"""
    create table if not exists {table_name} (
        user_id INT,
        first_name VARCHAR,
        last_name VARCHAR,
        occupation VARCHAR
    )
    """

    copy_into = f"""
    copy into {table_name}
    from @temporary_stage/{file_name}.gz
    file_format = csv_format;
    """

    with snowflake.get_connection() as conn:
        with conn.cursor() as curs:
            curs.execute(create_format)
            curs.execute(create_stage)
            curs.execute(put_file)
            curs.execute(create_table)
            curs.execute(copy_into)

    context.log.info(f"Loaded data from {file_path} into {table_name}")


defs = Definitions(assets=[load_csv_to_snowflake], resources={"snowflake": snowflake})
```

### Step 4: Configure and Run the Asset

Finally, run the asset in the Dagster UI to load the CSV file into the Snowflake table.

1. Start Dagster by running:

   ```sh
   dagster dev
   ```

2. Open the Dagster UI at [http://127.0.0.1:3000](http://127.0.0.1:3000).

3. On the Assets tab, click the `load_csv_to_snowflake` asset.

4. In the top right click the "Materialize" button.

---

## Expected Outcomes

By following these steps, you will have successfully loaded a CSV file into a Snowflake table using Dagster. The data from the CSV file will be available in the specified Snowflake table for further processing or analysis.

---

## Troubleshooting

- Ensure that the Snowflake credentials and connection details are correct.
- Verify that the CSV file path is correct and accessible.
- Check the Snowflake table schema to ensure it matches the CSV file structure.

---

## Next Steps

- Explore more advanced data loading techniques with Dagster and Snowflake.
- Integrate additional data sources and transformations into your Dagster pipeline.

---

## Additional Resources

- [Dagster Documentation](https://docs.dagster.io/)
- [Snowflake Documentation](https://docs.snowflake.com/)
- [Dagster Snowflake Integration](https://docs.dagster.io/integrations/snowflake/using-snowflake-with-dagster)
