---
title: Dagster & Teradata
sidebar_label: Teradata
sidebar_position: 1
description: The community-supported Teradata package provides an integration with Teradata Vantage.
tags: [community-supported, storage]
source: https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-teradata
pypi: https://pypi.org/project/dagster-teradata
sidebar_custom_props:
  logo: images/integrations/teradata.svg
  community: true
canonicalUrl: '/integrations/libraries/teradata'
slug: '/integrations/libraries/teradata'
---

import CommunityIntegration from '@site/docs/partials/\_CommunityIntegration.md';

<CommunityIntegration />

<p>{frontMatter.description}</p>

For more information, see the [dagster-teradata GitHub repository](https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-teradata).

To begin integrating Dagster with Teradata Vantage for building and managing ETL pipelines, this guide provides step-by-step instructions on installing and configuring the required packages, setting up a Dagster project, and implementing a pipeline that interacts with Teradata Vantage.

## Prerequisites

- Access to a Teradata Vantage instance.

  :::note

  If you need a test instance of Vantage, you can provision one for free at [https://clearscape.teradata.com](https://clearscape.teradata.com/sign-in?utm_source=dev_portal&utm_medium=quickstart_tutorial&utm_campaign=quickstarts)

  :::

- Python **3.9** or higher. Python **3.13** is recommended.
- `pip` installed

## Step 1: Install `dagster-teradata`

With your virtual environment active, the next step is to install dagster and the Teradata provider package (dagster-teradata) to interact with Teradata Vantage.

1. Install the required packages:

   <PackageInstallInstructions packageName="dagster-teradata" />

2. Note about Optional Dependencies:

   a) `dagster-teradata` relies on dagster-aws for ingesting data from an S3 bucket into Teradata Vantage. Since `dagster-aws` is an optional dependency, users can install it by running:

   <PackageInstallInstructions packageName="dagster-teradata[aws]" />

   b) `dagster-teradata` also relies on `dagster-azure` for ingesting data from an Azure Blob Storage container into Teradata Vantage. To install this dependency, run:

   <PackageInstallInstructions packageName="dagster-teradata[azure]" />

3. Verify the installation:

   To confirm that Dagster is correctly installed, run:

   ```bash
   dagster –version
   ```

   If installed correctly, it should show the version of Dagster.

## Step 2: Initialize a Dagster project

Now that you have the necessary packages installed, the next step is to create a new Dagster project.

### Scaffold a new Dagster project

Run the following command:

```bash
dagster project scaffold --name dagster-quickstart
```

This command will create a new project named `dagster-quickstart`. It will automatically generate the following directory structure:

```bash
dagster-quickstart
│   pyproject.toml
│   README.md
│   setup.cfg
│   setup.py
│
├───dagster_quickstart
│       assets.py
│       definitions.py
│       __init__.py
│
└───dagster_quickstart_tests
        test_assets.py
        __init__.py
```

Refer [here](/guides/build/projects/project-structure/project-overview) to know more above this directory structure.

## Step 3: Create sample data

To simulate an ETL pipeline, create a CSV file with sample data that your pipeline will process.

**Create the CSV File:** Inside the dagster_quickstart/data/ directory, create a file named sample_data.csv with the following content:

```bash
id,name,age,city
1,Alice,28,New York
2,Bob,35,San Francisco
3,Charlie,42,Chicago
4,Diana,31,Los Angeles
```

This file represents sample data that will be used as input for your ETL pipeline.

## Step 4: Define assets for the ETL pipeline

Now, we'll define a series of assets for the ETL pipeline inside the assets.py file.

Open the `dagster_quickstart/assets.py` file and add the following code to define the pipeline:

```python
import pandas as pd
from dagster import asset

@asset(required_resource_keys={"teradata"})
def read_csv_file(context):
    df = pd.read_csv("dagster_quickstart/data/sample_data.csv")
    context.log.info(df)
    return df

@asset(required_resource_keys={"teradata"})
def drop_table(context):
    result = context.resources.teradata.drop_table(["tmp_table"])
    context.log.info(result)

@asset(required_resource_keys={"teradata"})
def create_table(context, drop_table):
    result = context.resources.teradata.execute_query('''CREATE TABLE tmp_table (
                                                            id INTEGER,
                                                            name VARCHAR(50),
                                                            age INTEGER,
                                                            city VARCHAR(50));''')
    context.log.info(result)

@asset(required_resource_keys={"teradata"}, deps=[read_csv_file])
def insert_rows(context, create_table, read_csv_file):
    data_tuples = [tuple(row) for row in read_csv_file.to_numpy()]
    for row in data_tuples:
        result = context.resources.teradata.execute_query(
            f"INSERT INTO tmp_table (id, name, age, city) VALUES ({row[0]}, '{row[1]}', {row[2]}, '{row[3]}');"
        )
        context.log.info(result)

@asset(required_resource_keys={"teradata"})
def read_table(context, insert_rows):
    result = context.resources.teradata.execute_query("select * from tmp_table;", True)
    context.log.info(result)

```

This Dagster pipeline defines a series of assets that interact with Teradata. It starts by reading data from a CSV file, then drops and recreates a table in Teradata. After that, it inserts rows from the CSV into the table and finally retrieves the data from the table.

## Step 5: Define the pipeline definitions

The next step is to configure the pipeline by defining the necessary resources and jobs.

**Edit the definitions.py file**: Open `dagster_quickstart/definitions.py` and define your Dagster pipeline as follows:

```python
from dagster import EnvVar, Definitions
from dagster_teradata import TeradataResource

from .assets import read_csv_file, read_table, create_table, drop_table, insert_rows

# Define the pipeline and resources
defs = Definitions(
    assets=[read_csv_file, read_table, create_table, drop_table, insert_rows],
    resources={
        "teradata": TeradataResource(
            host=EnvVar("TERADATA_HOST"),
            user=EnvVar("TERADATA_USER"),
            password=EnvVar("TERADATA_PASSWORD"),
            database=EnvVar("TERADATA_DATABASE"),
        )
    }
)
```

This code sets up a Dagster project that interacts with Teradata by defining assets and resources:

1. It imports necessary modules, including pandas, Dagster, and dagster-teradata.
2. It imports asset functions (read_csv_file, read_table, create_table, drop_table, insert_rows) from the assets.py module.
3. It registers these assets with Dagster using Definitions, allowing Dagster to track and execute them.
4. It defines a Teradata resource (TeradataResource) that reads database connection details from environment variables (TERADATA_HOST, TERADATA_USER, TERADATA_PASSWORD, TERADATA_DATABASE).

## Step 6: Run the pipeline

After setting up the project, you can now run your Dagster pipeline:

1. **Start the Dagster dev server:** In your terminal, navigate to the root directory of your project and run:
   dagster dev
   After executing the command dagster dev, the Dagster logs will be displayed directly in the terminal. Any errors encountered during startup will also be logged here. Once you see a message similar to:

   ```bash
   2025-02-04 09:15:46 +0530 - dagster-webserver - INFO - Serving dagster-webserver on http://127.0.0.1:3000 in process 32564,
   ```

   It indicates that the Dagster webserver is running successfully. At this point, you can proceed to the next step.

2. **Access the Dagster UI:** Open a web browser and navigate to http://127.0.0.1:3000. This will open the Dagster UI where you can manage and monitor your pipelines.

3. **Run the pipeline:**

- In the top navigation of the Dagster UI, click Assets > View global asset lineage.
- Click Materialize to execute the pipeline.
- In the popup window, click View to see the details of the pipeline run.

4. **Monitor the run:** The Dagster UI allows you to visualize the pipeline's progress, view logs, and inspect the status of each step. You can switch between different views to see the execution logs and metadata for each asset.

## Further reading

- [dagster-teradata with Teradata Vantage](https://developers.teradata.com/quickstarts/manage-data/use-dagster-with-teradata-vantage)
- [Data Transfer from AWS S3 to Teradata Vantage Using dagster-teradata](https://developers.teradata.com/quickstarts/manage-data/dagster-teradata-s3-to-teradata-transfer)
- [Data Transfer from Azure Blob to Teradata Vantage Using dagster-teradata](https://developers.teradata.com/quickstarts/manage-data/dagster-teradata-azure-to-teradata-transfer)
- [Manage VantageCloud Lake Compute Clusters with dagster-teradata](https://developers.teradata.com/quickstarts/vantagecloud-lake/vantagecloud-lake-compute-cluster-dagster)
- [Teradata Authorization](https://docs.teradata.com/r/Enterprise_IntelliFlex_VMware/SQL-Data-Definition-Language-Syntax-and-Examples/Authorization-Statements-for-External-Routines/CREATE-AUTHORIZATION-and-REPLACE-AUTHORIZATION)
- [Teradata VantageCloud Lake Compute Clusters](https://docs.teradata.com/r/Teradata-VantageCloud-Lake/Managing-Compute-Resources/Compute-Clusters)
