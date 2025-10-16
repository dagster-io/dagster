---
title: Dagster & Teradata
sidebar_label: Teradata
description: The community-supported Teradata package provides an integration with Teradata Vantage.
tags: [community-supported, storage]
source: https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-teradata
pypi: https://pypi.org/project/dagster-teradata
sidebar_custom_props:
  logo: images/integrations/teradata.svg
  community: true
---

<p>{frontMatter.description}</p>

For more information, see the [dagster-teradata GitHub repository](https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-teradata).

# dagster-teradata with Teradata Vantage

To begin integrating Dagster with Teradata Vantage for building and managing ETL pipelines, this guide provides step-by-step instructions on installing and configuring the required packages, setting up a Dagster project, and implementing a pipeline that interacts with Teradata Vantage.

## Prerequisites

- Access to a Teradata Vantage instance.

  :::note
  If you need a test instance of Vantage, you can provision one for free at [https://clearscape.teradata.com](https://clearscape.teradata.com/sign-in?utm_source=dev_portal&utm_medium=quickstart_tutorial&utm_campaign=quickstarts)
  :::

- Python **3.9** or higher, Python **3.13** is recommended.
- pip

## Install dagster-teradata

With your virtual environment active, the next step is to install dagster and the Teradata provider package (dagster-teradata) to interact with Teradata Vantage.

1. Install the Required Packages:

   <PackageInstallInstructions packageName="dagster-teradata" />

2. Note about Optional Dependencies:

   a) `dagster-teradata` relies on dagster-aws for ingesting data from an S3 bucket into Teradata Vantage. Since `dagster-aws` is an optional dependency, users can install it by running:

   <PackageInstallInstructions packageName="dagster-teradata[aws]" />

   b) `dagster-teradata` also relies on `dagster-azure` for ingesting data from an Azure Blob Storage container into Teradata Vantage. To install this dependency, run:

   <PackageInstallInstructions packageName="dagster-teradata[azure]" />

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

Refer [here](/guides/build/projects/dagster-project-file-reference) to know more above this directory structure.

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

1. It imports necessary modules, including pandas, Dagster, and dagster-teradata.
2. It imports asset functions (read_csv_file, read_table, create_table, drop_table, insert_rows) from the assets.py module.
3. It registers these assets with Dagster using Definitions, allowing Dagster to track and execute them.
4. It defines a Teradata resource (TeradataResource) that reads database connection details from environment variables (TERADATA_HOST, TERADATA_USER, TERADATA_PASSWORD, TERADATA_DATABASE).

## Running the Pipeline

After setting up the project, you can now run your Dagster pipeline:

1. **Start the Dagster Dev Server:** In your terminal, navigate to the root directory of your project and run:
   dagster dev
   After executing the command dagster dev, the Dagster logs will be displayed directly in the terminal. Any errors encountered during startup will also be logged here. Once you see a message similar to:

   ```bash
   2025-02-04 09:15:46 +0530 - dagster-webserver - INFO - Serving dagster-webserver on http://127.0.0.1:3000 in process 32564,
   ```

   It indicates that the Dagster webserver is running successfully. At this point, you can proceed to the next step.

   <br />

2. **Access the Dagster UI:** Open a web browser and navigate to http://127.0.0.1:3000. This will open the Dagster UI where you can manage and monitor your pipelines.
   <br />
3. **Run the Pipeline:**

- In the top navigation of the Dagster UI, click Assets > View global asset lineage.
- Click Materialize to execute the pipeline.
- In the popup window, click View to see the details of the pipeline run.
  <br />

4. **Monitor the Run:** The Dagster UI allows you to visualize the pipeline's progress, view logs, and inspect the status of each step. You can switch between different views to see the execution logs and metadata for each asset.

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

```python
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

```python
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

- An Azure account. You can start with a [free account](https://azure.microsoft.com/free).
- Create an [Azure storage account](https://docs.microsoft.com/en-us/azure/storage/common/storage-quickstart-create-account?tabs=azure-portal)
- Create a [blob container](https://learn.microsoft.com/en-us/azure/storage/blobs/blob-containers-portal) under Azure storage account
- [Upload](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-portal) CSV/JSON/Parquest format files to blob container
- Create a Teradata Authorization object with the Azure Blob Storage Account and the Account Secret Key

  ```sql
  CREATE AUTHORIZATION azure_authorization USER 'azuretestquickstart' PASSWORD 'AZURE_BLOB_ACCOUNT_SECRET_KEY'
  ```

  :::note
  Replace `AZURE_BLOB_ACCOUNT_SECRET_KEY` with Azure storage account `azuretestquickstart` [access key](https://learn.microsoft.com/en-us/azure/storage/common/storage-account-keys-manage?toc=%2Fazure%2Fstorage%2Fblobs%2Ftoc.json&bc=%2Fazure%2Fstorage%2Fblobs%2Fbreadcrumb%2Ftoc.json&tabs=azure-portal)
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

# Teradata Operators Documentation

## BTEQ Operator

The `bteq_operator` method enables execution of SQL statements or BTEQ (Basic Teradata Query) scripts using the Teradata BTEQ utility.
It supports running commands either on the local machine or on a remote machine over SSH — in both cases, the BTEQ utility must be installed on the target system.

### Key Features

- Executes SQL provided as a string or from a script file (only one can be used at a time).
- Supports custom encoding for the script or session.
- Configurable timeout and return code handling.
- Remote execution supports authentication using a password or an SSH key.
- Works in both local and remote setups, provided the BTEQ tool is installed on the system where execution takes place.

> Ensure that the Teradata BTEQ utility is installed on the machine where the SQL statements or scripts will be executed.
>
> This could be:
>
> - The local machine where Dagster runs the task, for local execution.
> - The remote host accessed via SSH, for remote execution.
> - If executing remotely, also ensure that an SSH server (e.g., sshd) is running and accessible on the remote machine.

### Parameters

- `sql`: SQL statement(s) to be executed using BTEQ. (optional, mutually exclusive with `file_path`)
- `file_path`: If provided, this file will be used instead of the `sql` content. This path represents remote file path when executing remotely via SSH, or local file path when executing locally. (optional, mutually exclusive with `sql`)
- `remote_host`: Hostname or IP address for remote execution. If not provided, execution is assumed to be local. _(optional)_
- `remote_user`: Username used for SSH authentication on the remote host. Required if `remote_host` is specified.
- `remote_password`: Password for SSH authentication. Optional, and used as an alternative to `ssh_key_path`.
- `ssh_key_path`: Path to the SSH private key used for authentication. Optional, and used as an alternative to `remote_password`.
- `remote_port`: SSH port number for the remote host. Defaults to `22` if not specified. _(optional)_
- `remote_working_dir`: Temporary directory location on the remote host (via SSH) where the BTEQ script will be transferred and executed. Defaults to `/tmp` if not specified. This is only applicable when `remote_host` is provided.
- `bteq_script_encoding`: Character encoding for the BTEQ script file. Defaults to ASCII if not specified.
- `bteq_session_encoding`: Character set encoding for the BTEQ session. Defaults to ASCII if not specified.
- `bteq_quit_rc`: Accepts a single integer, list, or tuple of return codes. Specifies which BTEQ return codes should be treated as successful, allowing subsequent tasks to continue execution.
- `timeout`: Timeout (in seconds) for executing the BTEQ command. Default is 600 seconds (10 minutes).
- `timeout_rc`: Return code to use if the BTEQ execution fails due to a timeout. To allow Ops execution to continue after a timeout, include this value in `bteq_quit_rc`. If not specified, a timeout will raise an exception and stop the Ops.

### Returns

- Output of the BTEQ execution, or `None` if no output was produced.

### Raises

- `ValueError`: For invalid input or configuration
- `DagsterError`: If BTEQ execution fails or times out

### Notes

- Either `sql` or `file_path` must be provided, but not both.
- For remote execution, provide either `remote_password` or `ssh_key_path` (not both).
- Encoding and timeout handling are customizable.
- Validates remote port and authentication parameters.

### Example Usage

```python
# Local execution with direct SQL
output = bteq_operator(sql="SELECT * FROM table;")

# Remote execution with file
output = bteq_operator(
    file_path="script.sql",
    remote_host="example.com",
    remote_user="user",
    ssh_key_path="/path/to/key.pem"
)
```

---

## DDL Operator

The `ddl_operator` method executes DDL (Data Definition Language) statements on Teradata using the Teradata Parallel Transporter (TPT).
It supports both local and remote execution (via SSH), allowing you to manage Teradata schema objects seamlessly within Dagster pipelines.

### Key Features

- Executes one or more DDL statements in a single operation.
- Supports both local and remote execution via SSH.
- Handles custom error codes to allow continued workflow execution.
- Allows configuration of remote working directory and SSH credentials.
- Supports custom job naming for easier tracking and debugging.
- Provides robust validation for input parameters and execution environment.

> Ensure that the Teradata Parallel Transporter (TPT) is installed on the system where DDL execution will occur.
> This could be:
>
> - The local machine running Dagster (for local execution).
> - A remote host accessible via SSH (for remote execution).
> - For remote setups, ensure an SSH server (e.g., sshd) is active and reachable.

### Parameters

| Parameter            | Type                 | Description                                                                                                  | Required | Default |
| -------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------ | -------- | ------- |
| `ddl`                | `list[str]`          | List of DDL statements to be executed. Each entry must be a valid SQL string.                                | ✅       | —       |
| `error_list`         | `int` \| `List[int]` | Single integer or list of integers representing error codes to ignore.                                       | ❌       | —       |
| `remote_working_dir` | `str`                | Directory on the remote host used as a working directory for temporary DDL files or logs.                    | ❌       | `/tmp`  |
| `ddl_job_name`       | `str`                | A descriptive name for the DDL job to assist in tracking and logging.                                        | ❌       | —       |
| `remote_host`        | `str`                | Hostname or IP address of the remote machine where the DDL should run. If not specified, execution is local. | ❌       | —       |
| `remote_user`        | `str`                | SSH username for authentication on the remote host. Required if `remote_host` is provided.                   | ❌       | —       |
| `remote_password`    | `str`                | Password for SSH authentication. Used as an alternative to `ssh_key_path`.                                   | ❌       | —       |
| `ssh_key_path`       | `str`                | Path to the SSH private key file used for authentication. Used as an alternative to `remote_password`.       | ❌       | —       |
| `remote_port`        | `int`                | SSH port for the remote host. Must be within range `1–65535`.                                                | ❌       | `22`    |

### Returns

- **`Optional[int]`** — Return code from the DDL execution.  
  Returns `None` if no return code is applicable or produced.

### Raises

- **`ValueError`** — If input validation fails (e.g., missing DDL list, invalid SSH configuration, or bad port number).
- **`Exception`** — If the DDL execution fails and the resulting error code is not part of the `error_list`.

### Notes

- The `ddl` parameter **must** be a non-empty list of valid SQL DDL statements.
- For remote execution, either `remote_password` or `ssh_key_path` **must** be provided (but not both).
- Invalid or missing SSH configuration parameters will raise validation errors before execution.
- Ensures strong validation for parameters like SSH port and DDL syntax structure.

### Example Usage

#### Local Execution with Multiple DDL Statements

```python
return_code = ddl_operator(
    ddl=[
        "CREATE TABLE employees (id INT, name VARCHAR(100));",
        "CREATE INDEX idx_name ON employees(name);"
    ]
)
```

#### Remote Execution Using SSH Key Authentication

```python
return_code = ddl_operator(
    ddl=["DROP TABLE IF EXISTS sales;"],
    remote_host="td-server.example.com",
    remote_user="td_admin",
    ssh_key_path="/home/td_admin/.ssh/id_rsa",
    ddl_job_name="drop_sales_table"
)
```

#### Remote Execution Using Password Authentication with Ignored Error Codes

```python
return_code = ddl_operator(
    ddl=["CREATE DATABASE reporting;"],
    remote_host="192.168.1.100",
    remote_user="teradata",
    remote_password="password123",
    error_list=[3807],  # Ignore 'database already exists' error
    ddl_job_name="create_reporting_db"
)
```

#### Integration with Dagster

```python
from dagster import asset
from dagster_teradata import DdlOperator

@asset
def create_tables(context):
    context.resources.teradata.ddl_operator(
        ddl=[
            "CREATE TABLE sales (id INTEGER, amount DECIMAL(10,2));",
            "CREATE TABLE customers (cust_id INTEGER, name VARCHAR(100));"
        ]
    )
```

---

## TDLoad Operator

The `tdload_operator` method enables execution of **TDLoad** jobs for transferring data between Teradata tables or between Teradata and external files.  
It provides a unified interface to run **TDLoad** operations either **locally** or **remotely via SSH**, allowing data ingestion and export tasks to be seamlessly integrated within Dagster pipelines.

### Key Features

- Executes TDLoad operations for data import/export between Teradata and external files.
- Supports both local and remote execution via SSH.
- Allows custom job configuration, variable files, and TDLoad command options.
- Handles multiple data source and target formats (e.g., CSV, TEXT, PARQUET).
- Supports text delimiters for structured data handling.
- Provides strong validation for remote execution parameters and ports.

> Ensure that the **TDLoad utility** is installed on the machine where execution will occur.
>
> This could be:
>
> - The local machine running Dagster (for local execution).
> - A remote host accessible via SSH (for remote execution).
> - For remote setups, ensure that an SSH server (e.g., `sshd`) is active and reachable.

### Parameters

| Parameter               | Type  | Description                                                                                 | Required | Default |
| ----------------------- | ----- | ------------------------------------------------------------------------------------------- | -------- | ------- |
| `source_table`          | `str` | Name of the source table in Teradata.                                                       | ❌       | —       |
| `select_stmt`           | `str` | SQL `SELECT` statement for extracting data.                                                 | ❌       | —       |
| `insert_stmt`           | `str` | SQL `INSERT` statement for loading data.                                                    | ❌       | —       |
| `target_table`          | `str` | Name of the target table in Teradata.                                                       | ❌       | —       |
| `source_file_name`      | `str` | Source file path for input data.                                                            | ❌       | —       |
| `target_file_name`      | `str` | Target file path for output data.                                                           | ❌       | —       |
| `source_format`         | `str` | Format of the source file (e.g., CSV, TEXT).                                                | ❌       | —       |
| `source_text_delimiter` | `str` | Field delimiter for the source file.                                                        | ❌       | —       |
| `target_format`         | `str` | Format of the target file (e.g., CSV, TEXT).                                                | ❌       | —       |
| `target_text_delimiter` | `str` | Field delimiter for the target file.                                                        | ❌       | —       |
| `tdload_options`        | `str` | Additional TDLoad options to customize execution.                                           | ❌       | —       |
| `tdload_job_name`       | `str` | Name assigned to the TDLoad job.                                                            | ❌       | —       |
| `tdload_job_var_file`   | `str` | Path to the TDLoad job variable file.                                                       | ❌       | —       |
| `remote_working_dir`    | `str` | Directory on remote host for temporary TDLoad job files.                                    | ❌       | `/tmp`  |
| `remote_host`           | `str` | Hostname or IP of the remote machine for execution.                                         | ❌       | —       |
| `remote_user`           | `str` | Username for SSH authentication on the remote host. Required if `remote_host` is specified. | ❌       | —       |
| `remote_password`       | `str` | Password for SSH authentication. Alternative to `ssh_key_path`.                             | ❌       | —       |
| `ssh_key_path`          | `str` | Path to SSH private key used for authentication. Alternative to `remote_password`.          | ❌       | —       |
| `remote_port`           | `int` | SSH port for the remote connection (1–65535).                                               | ❌       | `22`    |

### Return Value

- **`int | None`** — Return code from the TDLoad operation.  
  Returns `None` if no return code is applicable or produced.

### Raises

- **`ValueError`** — For invalid parameter combinations (e.g., both password and key provided, invalid port, or missing SSH credentials).
- **`Exception`** — If the TDLoad execution fails for reasons not covered by user configuration.

### Notes

- Either a `source_table`/`select_stmt` **or** a `source_file_name` must be provided as the input source.
- Either a `target_table`/`insert_stmt` **or** a `target_file_name` must be provided as the target.
- For remote execution, only one authentication method can be used — either `remote_password` or `ssh_key_path`.
- The `remote_port` must be a valid port number between `1` and `65535`.
- The `tdload_job_name` and `tdload_job_var_file` can help manage reusable or parameterized load operations.

### Examples

#### 1. File to Table

Load data from a file into a Teradata table.

```python
@asset
def file_to_table_load(context):
    context.resources.teradata.tdload_operator(
        source_file_name="/data/customers.csv",
        target_table="customers",
        source_format="Delimited",
        source_text_delimiter="|"
    )
```

#### 2. Table to File

Export data from a Teradata table to a file.

```python
@asset
def table_to_file_export(context):
    context.resources.teradata.tdload_operator(
        source_table="sales",
        target_file_name="/data/sales_export.csv",
        target_format="Delimited",
        target_text_delimiter=","
    )
```

#### 3. Table to Table

Transfer data between Teradata tables.

```python
@asset
def table_to_table_transfer(context):
    context.resources.teradata.tdload_operator(
        source_table="staging_sales",
        target_table="prod_sales",
        insert_stmt="INSERT INTO prod_sales SELECT * FROM staging_sales WHERE amount > 1000"
    )
```

#### 4. Custom SELECT to File

Export data using a custom SQL query.

```python
@asset
def custom_export(context):
    context.resources.teradata.tdload_operator(
        select_stmt="SELECT customer_id, SUM(amount) FROM sales GROUP BY customer_id",
        target_file_name="/data/customer_totals.csv"
    )
```

#### 5. Using Job Variable Files

```python
@asset
def use_job_var_file(context):
    context.resources.teradata.tdload_operator(
        tdload_job_var_file="/config/load_job_vars.txt",
        tdload_options="-j my_load_job"
    )
```

#### 6. Remote Execution with SSH Key

```python
@asset
def remote_tpt_operation(context):
    context.resources.teradata.tdload_operator(
        source_file_name="/remote/data/input.csv",
        target_table="remote_table",
        remote_host="td-prod.company.com",
        remote_user="tdadmin",
        ssh_key_path="/home/user/.ssh/td_key",
        remote_working_dir="/tmp/tpt_work"
    )
```

#### 7. Custom TPT Options

```python
@asset
def custom_tpt_options(context):
    context.resources.teradata.tdload_operator(
        source_table="large_table",
        target_file_name="/data/export.csv",
        tdload_options="-f CSV -m 4 -s ,",  # Format: CSV, 4 streams, comma separator
        tdload_job_name="custom_export_job"
    )
```

### Error Handling

Both operators include comprehensive error handling:

- **Connection errors:** Automatic retry and cleanup
- **SSH failures:** Graceful degradation with detailed logging
- **TPT execution errors:** Proper exit code handling and error messages
- **Resource cleanup:** Automatic cleanup of temporary files

### Best Practices

- Use `error_list` for idempotent DDL operations
- Specify `remote_working_dir` for SSH operations
- Use meaningful job names for monitoring and debugging
- Test with small datasets before scaling up
- Monitor TPT job logs for performance optimization

## Further reading

- [dagster-teradata with Teradata Vantage](https://developers.teradata.com/quickstarts/manage-data/use-dagster-with-teradata-vantage)
- [Data Transfer from AWS S3 to Teradata Vantage Using dagster-teradata](https://developers.teradata.com/quickstarts/manage-data/dagster-teradata-s3-to-teradata-transfer)
- [Data Transfer from Azure Blob to Teradata Vantage Using dagster-teradata](https://developers.teradata.com/quickstarts/manage-data/dagster-teradata-azure-to-teradata-transfer)
- [Manage VantageCloud Lake Compute Clusters with dagster-teradata](https://developers.teradata.com/quickstarts/vantagecloud-lake/vantagecloud-lake-compute-cluster-dagster)
- [Teradata Authorization](https://docs.teradata.com/r/Enterprise_IntelliFlex_VMware/SQL-Data-Definition-Language-Syntax-and-Examples/Authorization-Statements-for-External-Routines/CREATE-AUTHORIZATION-and-REPLACE-AUTHORIZATION)
- [Teradata VantageCloud Lake Compute Clusters](https://docs.teradata.com/r/Teradata-VantageCloud-Lake/Managing-Compute-Resources/Compute-Clusters)
