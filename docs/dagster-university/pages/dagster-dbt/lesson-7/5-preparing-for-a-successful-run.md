---
title: "Lesson 7: Preparing for a successful run"
module: 'dbt_dagster'
lesson: '7'
---

# Preparing for a successful run

{% callout %}
>💡 **Heads up! This section is optional.** The goal of this lesson was to teach you how to successfully **deploy** to Dagster+, which you completed in the last section. Preparing for a successful run in Dagster+ requires using some external services, which may not translate to the external services you prefer to use. As such, we’ve opted to make this section optional.
{% /callout %}

In previous lessons, you followed along by adding our example code to your local project. You successfully materialized the assets in the project and stored the resulting data in a local DuckDB database.

**This section will be a little different.** Production deployment can be complicated and require a lot of setup. To keep things simple we’ll walk you through the steps required to set up the pipeline for a successful run, but not how to set up external services. For this lesson, assume we already have our storage set up and ready to go.

---

## Deployment overview

Since you'll be deploying your project in production, you'll need production systems to read and write your assets. In this case, we'll use:

- **Amazon S3** to store the files we were saving to our local file system. The data will be small enough to fit within AWS's free tier. For more information on how to set up an S3 bucket, see [this guide](https://www.gormanalysis.com/blog/connecting-to-aws-s3-with-python/).
- **Motherduck** to replace our local DuckDB instance and query the data in our S3 bucket. Motherduck is a cloud-based data warehouse that can be used to store and query data that is currently free to setup. For more information on how to set up Motherduck, see [their documentation](https://motherduck.com/docs/getting-started), along with how to [connect it to your AWS S3 bucket](https://motherduck.com/docs/integrations/amazon-s3).

The code you cloned in the starter project already has some logic to dynamically switch between local and cloud storage, along with the paths to reference. To trigger the switch, you can set an environment variable called `DAGSTER_ENVIRONMENT` and set it to `prod`. This will tell the pipeline to use the production paths and storage.

In summary, before you can run this pipeline in Dagster+, you’ll need to:

1. Set up an S3 bucket to store the files/assets that we download and generate
2. Sign up for a free Motherduck account to replace our local DuckDB instance
3. Connect an S3 user with access to the S3 bucket to the Motherduck account
4. Add a new production target to the dbt project
5. Add the environment variables for the S3 user and Motherduck token to Dagster+

We’ll show you how to do 4 and 5 so you can do this with your credentials when you’re ready.

---

## Adding a production target to profiles.yml

The first step we’ll take is to add a second target to the `dagster_dbt_university` profile in our project’s `analytics/profiles.yml`. A [‘target’ in dbt](https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles#understanding-targets-in-profiles) describes a connection to a data warehouse, which up until this point in the course, has been a local DuckDB instance.

To maintain the separation of our development and production environments, we’ll add a `prod` target to our project’s profiles:

```yaml
dagster_dbt_university:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: '../{{ env_var("DUCKDB_DATABASE", "data/staging/data.duckdb") }}'
    prod:
      type: duckdb
      path: '{{ env_var("DUCKDB_DATABASE", "") }}'
```

Because we’re still using a DuckDB-backed database, our `type` will also be `duckdb` for `prod`. Save and commit the file to git before continuing.

**Note:** While dbt supports more platforms than just DuckDB, our project is set up to only work with this database type. If you use a different platform `type` for future projects, the configuration will vary depending on the platform being connected. Refer to [dbt’s documentation](https://docs.getdbt.com/docs/supported-data-platforms) for more information and examples.

---

## Adding a prod target to DbtProject

Next, we need to update the `DbtProject` object in `dagster_university/project.py` to specify what profile to target. To optimize the developer experience, let’s use an environment variable to specify the profile to target.

1. In the `.env` file, define an environment variable named `DBT_TARGET` and set it to `dev`:

   ```python
   DBT_TARGET=dev
   ```

2. Next, import the `os` module at the top of the `project.py` file so the environment variable is accessible:

   ```python
   import os
   ```

3. Finally, scroll to the initialization of the `DbtProject` object, and use the new environment variable to access the profile to target. This should be on or around line 11:

```python
dbt_project = DbtProject(
   project_dir=Path(__file__).joinpath("..", "..", "analytics").resolve(),
   target=os.getenv("DBT_TARGET")
)
```

---

## Adding a prod target to deploy.yml

Next, we need to update the dbt commands in the `.github/workflows/deploy.yml` file to target the new `prod` profile. This will ensure that dbt uses the correct connection details when the GitHub Action runs as part of our Dagster+ deployment.

Open the file, scroll to the environment variable section, and set an environment variable named `DBT_TARGET` to `prod`. This should be on or around line 12:

```bash
env:
  DAGSTER_CLOUD_URL: ${{ secrets.DAGSTER_CLOUD_ORGANIZATION }}
  DAGSTER_CLOUD_API_TOKEN: ${{ secrets.DAGSTER_CLOUD_API_TOKEN }}
  ENABLE_FAST_DEPLOYS: 'true'
  PYTHON_VERSION: '3.12'
  DAGSTER_CLOUD_FILE: 'dagster_cloud.yaml'
  DBT_TARGET: 'prod'
```

Save and commit the file to git. Don’t forget to push to remote!

---

## Adding environment variables to Dagster+

The last step in preparing for a successful run is to move environment variables to Dagster+. These variables were available to us via the `.env` file while we were working locally, but now that we’ve moved to a different environment, we’ll need to make them accessible again.

### Environment variables

The following table contains the environment variables we need to create in Dagster+:

{% table %}

- Variable {% width="30%" %}
- Description

---

- `DUCKDB_DATABASE`
- The service token for a Motherduck database, formatted as `md:?motherduck_token=<insert_token_here>`. Refer to the [Motherduck documentation](https://motherduck.com/docs/authenticating-to-motherduck/#authentication-using-a-service-token) for more info.

---

- `DAGSTER_ENVIRONMENT`
- Set this to `prod`. This will be used by your resources and constants.

---

- `DBT_TARGET`
- Set this to `prod`. This will be used by your dbt project and dbt resource to decide which target to use.

---

- `AWS_ACCESS_KEY_ID`
- The access key ID for the S3 bucket.

---

- `AWS_SECRET_ACCESS_KEY`
- The secret access key associated with the S3 bucket.

---

- `AWS_REGION`
- The region the S3 bucket is located in.

---

- `S3_BUCKET_PREFIX`
- The name of the S3 bucket, by default `"s3://dagster-university/"`, for the S3 bucket where your taxi data will be stored.

{% /table %}

### Creating environment variables

1. In the Dagster+ UI, click **Deployment > Environment variables**.
2. Click the **Add environment variable** button on the right side of the screen.
3. In the **Create environment variable** window, fill in the following:
    1. **Name** - The name of the environment variable. For example: `DUCKDB_DATABASE`
    2. **Value** - The value of the environment variable.
    3. **Code location scope**  - Deselect the **All code locations** option and check only the code location for this course’s project.
4. Click **Save.**

Repeat these steps until all the environment variables have been added.

---

## Running the pipeline

At this point, you're ready to run the pipeline in production! Navigate to the asset graph, click **Materialize all**, and watch as it all comes together.