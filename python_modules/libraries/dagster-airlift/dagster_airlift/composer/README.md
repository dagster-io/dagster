# Google Cloud Composer Integration for Dagster Airlift

This module provides integration between Dagster Airlift and Google Cloud Composer, Google's managed Airflow service on Google Cloud Platform (GCP).

## Installation

```bash
pip install 'dagster-airlift[composer]'
```

## Usage

The `ComposerSessionAuthBackend` class provides authentication to Google Cloud Composer instances. It can be used with `AirflowInstance` to interact with Airflow running on Cloud Composer.

### Basic Usage

```python
from dagster_airlift.composer import ComposerSessionAuthBackend
from dagster_airlift.core import AirflowInstance

# Create an AirflowInstance pointed at a Composer environment
af_instance = AirflowInstance(
    name="my-composer-instance",
    auth_backend=ComposerSessionAuthBackend(
        project_id="my-gcp-project",
        region="us-central1", 
        environment_name="my-composer-env"
    )
)

# Use the instance to interact with Airflow
dags = af_instance.list_dags()
```

### Using a Service Account

If you need to authenticate using a service account:

```python
from dagster_airlift.composer import ComposerSessionAuthBackend
from dagster_airlift.core import AirflowInstance

# Create an AirflowInstance with service account authentication
af_instance = AirflowInstance(
    name="my-composer-instance",
    auth_backend=ComposerSessionAuthBackend.from_service_account(
        project_id="my-gcp-project",
        region="us-central1", 
        environment_name="my-composer-env",
        service_account_file="/path/to/service-account.json"
    )
)
```

## Prerequisites

- Google Cloud project with Composer enabled
- Appropriate IAM permissions to access the Composer environment
- Google Cloud Composer v1 or higher

## Required Dependencies

This module requires the following packages:
- `google-auth`
- `google-cloud-composer`

These are automatically installed when you install `dagster-airlift[composer]`.