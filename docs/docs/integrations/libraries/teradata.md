---
layout: Integration
status: published
name: Teradata
title: Dagster & Teradata
sidebar_label: Teradata
excerpt: The community-supported `dagster-teradata` package provides an integration with Teradata.
sidebar_custom_props:
  logo: images/integrations/teradata.svg
  community: true
---

The community-supported `dagster-teradata` package provides an integration with Teradata Vantage.

For more information, see the [dagster-teradata GitHub repository](https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-teradata).

# dagster-teradata with Teradata Vantage

To begin integrating Dagster with Teradata Vantage for building and managing ETL pipelines, this guide provides step-by-step instructions on installing and configuring the required packages, setting up a Dagster project, and implementing a pipeline that interacts with Teradata Vantage.

## Prerequisites

* Access to a Teradata Vantage instance.

    :::note
    If you need a test instance of Vantage, you can provision one for free at [https://clearscape.teradata.com](https://clearscape.teradata.com/sign-in?utm_source=dev_portal&utm_medium=quickstart_tutorial&utm_campaign=quickstarts)
    :::

* Python **3.9** or higher, Python **3.12** is recommended.
* pip

## Install dagster-teradata

With your virtual environment active, the next step is to install dagster and the Teradata provider package (dagster-teradata) to interact with Teradata Vantage.

1. Install the Required Packages:

    ```bash
    pip install dagster dagster-webserver dagster-teradata
    ```

2. Note about Optional Dependencies:

   a) `dagster-teradata` relies on dagster-aws for ingesting data from an S3 bucket into Teradata Vantage. Since `dagster-aws` is an optional dependency, users can install it by running:

     ```bash
    pip install dagster-teradata[aws]
    ```
   b) `dagster-teradata` also relies on `dagster-azure` for ingesting data from an Azure Blob Storage container into Teradata Vantage. To install this dependency, run:

     ```bash
    pip install dagster-teradata[azure]
    ```

3. Verify the Installation:

   To confirm that Dagster is correctly installed, run:
     ```bash
    dagster –version
    ```
   If installed correctly, it should show the version of Dagster.


## Initialize a Dagster Project

Now that you have the necessary packages installed, the next step is to create a new Dagster project.

### Scaffold a New Dagster Project

Run the following command:

```bash
dagster project scaffold --name dagster-quickstart
 ```
This command will create a new project named dagster-quickstart. It will automatically generate the following directory structure:

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

Refer [here](https://docs.dagster.io/guides/build/projects/dagster-project-file-reference) to know more above this directory structure

## Create Sample Data

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

## Define Assets for the ETL Pipeline

Now, we'll define a series of assets for the ETL pipeline inside the assets.py file.

Edit the assets.py File: Open the dagster_quickstart/assets.py file and add the following code to define the pipeline:

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

## Define the Pipeline Definitions

The next step is to configure the pipeline by defining the necessary resources and jobs.

**Edit the definitions.py File**: Open dagster_quickstart/definitions.py and define your Dagster pipeline as follows:

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

This code sets up a Dagster project that interacts with Teradata by defining assets and resources

1.	It imports necessary modules, including pandas, Dagster, and dagster-teradata.
2.	It imports asset functions (read_csv_file, read_table, create_table, drop_table, insert_rows) from the assets.py module.
3.	It registers these assets with Dagster using Definitions, allowing Dagster to track and execute them.
4.	It defines a Teradata resource (TeradataResource) that reads database connection details from environment variables (TERADATA_HOST, TERADATA_USER, TERADATA_PASSWORD, TERADATA_DATABASE).

## Running the Pipeline

After setting up the project, you can now run your Dagster pipeline:

1.	**Start the Dagster Dev Server:** In your terminal, navigate to the root directory of your project and run:
dagster dev
After executing the command dagster dev, the Dagster logs will be displayed directly in the terminal. Any errors encountered during startup will also be logged here. Once you see a message similar to:
        ```bash
        2025-02-04 09:15:46 +0530 - dagster-webserver - INFO - Serving dagster-webserver on http://127.0.0.1:3000 in process 32564,
        ```
        It indicates that the Dagster webserver is running successfully. At this point, you can proceed to the next step.
<br />
2.	**Access the Dagster UI:** Open a web browser and navigate to http://127.0.0.1:3000. This will open the Dagster UI where you can manage and monitor your pipelines.
<br />
3.	**Run the Pipeline:**
* In the top navigation of the Dagster UI, click Assets > View global asset lineage.
* Click Materialize to execute the pipeline.
* In the popup window, click View to see the details of the pipeline run.
<br />
4.	**Monitor the Run:** The Dagster UI allows you to visualize the pipeline's progress, view logs, and inspect the status of each step. You can switch between different views to see the execution logs and metadata for each asset.

## Below are some of the operations provided by the TeradataResource:

### 1. Execute a Query (`execute_query`)

This operation executes a SQL query within Teradata Vantage.

**Args:**
- `sql` (str) – The query to be executed.
- `fetch_results` (bool, optional) – If True, fetch the query results. Defaults to False.
- `single_result_row` (bool, optional) – If True, return only the first row of the result set. Effective only if `fetch_results` is True. Defaults to False.

### 2. Execute Multiple Queries (`execute_queries`)

This operation executes a series of SQL queries within Teradata Vantage.

**Args:**
- `sql_queries` (Sequence[str]) – List of queries to be executed in series.
- `fetch_results` (bool, optional) – If True, fetch the query results. Defaults to False.
- `single_result_row` (bool, optional) – If True, return only the first row of the result set. Effective only if `fetch_results` is True. Defaults to False.

### 3. Drop a Database (`drop_database`)

This operation drops one or more databases from Teradata Vantage.

**Args:**
- `databases` (Union[str, Sequence[str]]) – Database name or list of database names to drop.

### 4. Drop a Table (`drop_table`)

This operation drops one or more tables from Teradata Vantage.

**Args:**
- `tables` (Union[str, Sequence[str]]) – Table name or list of table names to drop.

---
## Data Transfer from AWS S3 to Teradata Vantage Using dagster-teradata:

``` python
import os

from dagster import job, op, Definitions, EnvVar, DagsterError
from dagster_aws.s3 import S3Resource, s3_resource
from dagster_teradata import TeradataResource, teradata_resource

s3_resource = S3Resource(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
)

td_resource = TeradataResource(
    host=os.getenv("TERADATA_HOST"),
    user=os.getenv("TERADATA_USER"),
    password=os.getenv("TERADATA_PASSWORD"),
    database=os.getenv("TERADATA_DATABASE"),
)

@op(required_resource_keys={"teradata"})
def drop_existing_table(context):
     context.resources.teradata.drop_table("people")
     return "Tables Dropped"

@op(required_resource_keys={"teradata", "s3"})
def ingest_s3_to_teradata(context, status):
    if status == "Tables Dropped":
        context.resources.teradata.s3_to_teradata(s3_resource, os.getenv("AWS_S3_LOCATION"), "people")
    else:
        raise DagsterError("Tables not dropped")

@job(resource_defs={"teradata": td_resource, "s3": s3_resource})
def example_job():
     ingest_s3_to_teradata(drop_existing_table())

defs = Definitions(
    jobs=[example_job]
)
```
The `s3_to_teradata` method is used to load data from an S3 bucket into a Teradata table. It leverages Teradata Vantage Native Object Store (NOS), which allows direct querying and loading of external object store data (like AWS S3) into Teradata tables.

### Arguments Supported by `s3_blob_to_teradata`

- **s3 (S3Resource)**:
  The `S3Resource` object used to interact with the S3 bucket.

- **s3_source_key (str)**:
  The URI specifying the location of the S3 bucket. The URI format is:
  `/s3/YOUR-BUCKET.s3.amazonaws.com/YOUR-BUCKET-NAME`
  For more details, refer to:
  [Teradata Documentation - Native Object Store](https://docs.teradata.com/search/documents?query=native+object+store&sort=last_update&virtual-field=title_only&content-lang=en-US)

- **teradata_table (str)**:  
  The name of the Teradata table to which the data will be loaded.

- **public_bucket (bool)**:  
  Indicates whether the provided S3 bucket is public. If `True`, the objects within the bucket can be accessed via a URL without authentication. If `False`, the bucket is considered private, and authentication must be provided.  
  Defaults to `False`.

- **teradata_authorization_name (str)**:  
  The name of the Teradata Authorization Database Object, which controls access to the S3 object store.  
  For more details, refer to:
  [Teradata Vantage Native Object Store - Setting Up Access](https://docs.teradata.com/r/Enterprise_IntelliFlex_VMware/Teradata-VantageTM-Native-Object-Store-Getting-Started-Guide-17.20/Setting-Up-Access/Controlling-Foreign-Table-Access-with-an-AUTHORIZATION-Object)

---
## Data Transfer from Azure Blob to Teradata Vantage Using dagster-teradata:

``` python
import os

from dagster import job, op, Definitions, EnvVar, DagsterError
from dagster_azure.adls2 import ADLS2Resource, ADLS2SASToken
from dagster_teradata import TeradataResource, teradata_resource

azure_resource = ADLS2Resource(
    storage_account="",
    credential=ADLS2SASToken(token=""),
)

td_resource = TeradataResource(
    host=os.getenv("TERADATA_HOST"),
    user=os.getenv("TERADATA_USER"),
    password=os.getenv("TERADATA_PASSWORD"),
    database=os.getenv("TERADATA_DATABASE"),
)

@op(required_resource_keys={"teradata"})
def drop_existing_table(context):
     context.resources.teradata.drop_table("people")
     return "Tables Dropped"

@op(required_resource_keys={"teradata", "azure"})
def ingest_azure_to_teradata(context, status):
    if status == "Tables Dropped":
        context.resources.teradata.azure_blob_to_teradata(azure_resource, "/az/akiaxox5jikeotfww4ul.blob.core.windows.net/td-usgs/CSVDATA/09380000/2018/06/", "people", True)
    else:
        raise DagsterError("Tables not dropped")

@job(resource_defs={"teradata": td_resource, "azure": azure_resource})
def example_job():
     ingest_azure_to_teradata(drop_existing_table())

defs = Definitions(
    jobs=[example_job]
)
```

The `azure_blob_to_teradata` method is used to load data from Azure Data Lake Storage (ADLS) into a Teradata table. This method leverages Teradata Vantage Native Object Store (NOS) to directly query and load external object store data (such as Azure Blob Storage) into Teradata.

### Arguments Supported by `azure_blob_to_teradata`

- **azure (ADLS2Resource)**:  
  The `ADLS2Resource` object used to interact with the Azure Blob Storage.

- **blob_source_key (str)**:  
  The URI specifying the location of the Azure Blob object. The format is:
  `/az/YOUR-STORAGE-ACCOUNT.blob.core.windows.net/YOUR-CONTAINER/YOUR-BLOB-LOCATION`  
  For more details, refer to the Teradata documentation:  
  [Teradata Documentation - Native Object Store](https://docs.teradata.com/search/documents?query=native+object+store&sort=last_update&virtual-field=title_only&content-lang=en-US)

- **teradata_table (str)**:  
  The name of the Teradata table where the data will be loaded.

- **public_bucket (bool, optional)**:  
  Indicates whether the Azure Blob container is public. If `True`, the objects in the container can be accessed without authentication.  
  Defaults to `False`.

- **teradata_authorization_name (str, optional)**:  
  The name of the Teradata Authorization Database Object used to control access to the Azure Blob object store. This is required for secure access to private containers.  
  Defaults to an empty string.  
  For more details, refer to the documentation:  
  [Teradata Vantage Native Object Store - Setting Up Access](https://docs.teradata.com/r/Enterprise_IntelliFlex_VMware/Teradata-VantageTM-Native-Object-Store-Getting-Started-Guide-17.20/Setting-Up-Access/Controlling-Foreign-Table-Access-with-an-AUTHORIZATION-Object)

### Transfer data from Private Blob Storage Container to Teradata instance
To successfully transfer data from a Private Blob Storage Container to a Teradata instance, the following prerequisites are necessary.

* An Azure account. You can start with a [free account](https://azure.microsoft.com/free/).
* Create an [Azure storage account](https://docs.microsoft.com/en-us/azure/storage/common/storage-quickstart-create-account?tabs=azure-portal)
* Create a [blob container](https://learn.microsoft.com/en-us/azure/storage/blobs/blob-containers-portal) under Azure storage account
* [Upload](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-portal) CSV/JSON/Parquest format files to blob container
* Create a Teradata Authorization object with the Azure Blob Storage Account and the Account Secret Key

    ``` sql
    CREATE AUTHORIZATION azure_authorization USER 'azuretestquickstart' PASSWORD 'AZURE_BLOB_ACCOUNT_SECRET_KEY'
    ```

    :::note
    Replace `AZURE_BLOB_ACCOUNT_SECRET_KEY` with Azure storage account `azuretestquickstart`  [access key](https://learn.microsoft.com/en-us/azure/storage/common/storage-account-keys-manage?toc=%2Fazure%2Fstorage%2Fblobs%2Ftoc.json&bc=%2Fazure%2Fstorage%2Fblobs%2Fbreadcrumb%2Ftoc.json&tabs=azure-portal)
    :::

---
## Manage VantageCloud Lake Compute Clusters with dagster-teradata:
```python
from dagster import Definitions, DagsterError, op, materialize, job
from dagster_dbt import DbtCliResource
from dagster_teradata import teradata_resource, TeradataResource

from .assets import jaffle_shop_dbt_assets
from .project import jaffle_shop_project
from .schedules import schedules

@op(required_resource_keys={"teradata"})
def create_compute_cluster(context):
    context.resources.teradata.create_teradata_compute_cluster(
        "ShippingCG01",
        "Shipping",
        "STANDARD",
        "TD_COMPUTE_MEDIUM",
        "MIN_COMPUTE_COUNT(1) MAX_COMPUTE_COUNT(1) INITIALLY_SUSPENDED('FALSE')",
    )
    return "Compute Cluster Created"

@op(required_resource_keys={"teradata", "dbt"})
def run_dbt(context, status):
    if status == "Compute Cluster Created":
        materialize(
            [jaffle_shop_dbt_assets],
            resources={
                "dbt": DbtCliResource(project_dir=jaffle_shop_project)
            }
        )
        return "DBT Run Completed"
    else:
        raise DagsterError("DBT Run Failed")

@op(required_resource_keys={"teradata"})
def drop_compute_cluster(context, status):
    if status == "DBT Run Completed":
        context.resources.teradata.drop_teradata_compute_cluster("ShippingCG01", "Shipping", True)
    else:
        raise DagsterError("DBT Run Failed")

@job(resource_defs={"teradata": teradata_resource, "dbt": DbtCliResource})
def example_job():
    drop_compute_cluster(run_dbt(create_compute_cluster()))

defs = Definitions(
    assets=[jaffle_shop_dbt_assets],
    jobs=[example_job],
    schedules=schedules,
    resources={
        "dbt": DbtCliResource(project_dir=jaffle_shop_project),
        "teradata": TeradataResource(),
    },
)
```

Teradata VantageCloud Lake provides robust compute cluster management capabilities, enabling users to dynamically allocate, suspend, resume, and delete compute resources. These operations are fully supported through **`dagster-teradata`**, allowing users to manage compute clusters directly within their Dagster pipelines. This integration ensures optimal performance, scalability, and cost efficiency. The following operations facilitate seamless compute cluster management within Dagster:

### 1. Create a Compute Cluster (`create_teradata_compute_cluster`)

This operation provisions a new compute cluster within Teradata VantageCloud Lake using `dagster-teradata`. It enables users to define the cluster's configuration, including compute profiles, resource allocation, and query execution strategies, directly within a Dagster job.

**Args:**
- `compute_profile_name` (str) – Specifies the name of the compute profile.
- `compute_group_name` (str) – Identifies the compute group to which the profile belongs.
- `query_strategy` (str, optional, default="STANDARD") – Defines the method used by the Teradata Optimizer to execute SQL queries efficiently. Acceptable values:
  - `STANDARD` – The default strategy at the database level, optimized for general query execution.
  - `ANALYTIC` – Optimized for complex analytical workloads.
- `compute_map` (Optional[str], default=None) – Maps compute resources to specific nodes within the cluster.
- `compute_attribute` (Optional[str], default=None) – Specifies additional configuration attributes for the compute profile, such as:
  - `MIN_COMPUTE_COUNT(1) MAX_COMPUTE_COUNT(5) INITIALLY_SUSPENDED('FALSE')`
- `timeout` (int, optional, default=constants.CC_OPR_TIME_OUT) – The maximum duration (in seconds) to wait for the cluster creation process to complete. Default: 20 minutes.

### 2. Suspend a Compute Cluster (`suspend_teradata_compute_cluster`)

This operation temporarily suspends a compute cluster within Teradata VantageCloud Lake using **`dagster-teradata`**, reducing resource consumption while retaining the compute profile for future use.

**Args:**
- `compute_profile_name` (str) – Specifies the name of the compute profile.
- `compute_group_name` (str) – Identifies the compute group associated with the profile.
- `timeout` (int, optional, default=constants.CC_OPR_TIME_OUT) – The maximum wait time for the suspension process to complete. Default: 20 minutes.

### 3. Resume a Compute Cluster (`resume_teradata_compute_cluster`)

This operation restores a previously suspended compute cluster using **`dagster-teradata`**, allowing workloads to resume execution within a Dagster pipeline.

**Args:**
- `compute_profile_name` (str) – Specifies the name of the compute profile.
- `compute_group_name` (str) – Identifies the compute group associated with the profile.
- `timeout` (int, optional, default=constants.CC_OPR_TIME_OUT) – The maximum wait time for the resumption process to complete. Default: 20 minutes.

### 4. Delete a Compute Cluster (`drop_teradata_compute_cluster`)

This operation removes a compute cluster from Teradata VantageCloud Lake using **`dagster-teradata`**, with an option to delete the associated compute group. You can run this operation directly from your Dagster workflow.

**Args:**
- `compute_profile_name` (str) – Specifies the name of the compute profile.
- `compute_group_name` (str) – Identifies the compute group associated with the profile.
- `delete_compute_group` (bool, optional, default=False) – Determines whether the compute group should be deleted:
  - `True` – Deletes the compute group.
  - `False` – Retains the compute group without modifications.

These operations are designed to be fully integrated into **`dagster-teradata`** for managing compute clusters in Teradata VantageCloud Lake. By utilizing these operations within Dagster jobs, users can optimize resource allocation, perform complex transformations, and automate compute cluster management to align with workload demands.

---

## Further reading
* [dagster-teradata with Teradata Vantage](https://developers.teradata.com/quickstarts/manage-data/use-dagster-with-teradata-vantage/)
* [Data Transfer from AWS S3 to Teradata Vantage Using dagster-teradata](https://developers.teradata.com/quickstarts/manage-data/dagster-teradata-s3-to-teradata-transfer/)
* [Data Transfer from Azure Blob to Teradata Vantage Using dagster-teradata](https://developers.teradata.com/quickstarts/manage-data/dagster-teradata-azure-to-teradata-transfer/)
* [Manage VantageCloud Lake Compute Clusters with dagster-teradata](https://developers.teradata.com/quickstarts/vantagecloud-lake/vantagecloud-lake-compute-cluster-dagster/)
* [Teradata Authorization](https://docs.teradata.com/r/Enterprise_IntelliFlex_VMware/SQL-Data-Definition-Language-Syntax-and-Examples/Authorization-Statements-for-External-Routines/CREATE-AUTHORIZATION-and-REPLACE-AUTHORIZATION)
* [Teradata VantageCloud Lake Compute Clusters](https://docs.teradata.com/r/Teradata-VantageCloud-Lake/Managing-Compute-Resources/Compute-Clusters)

