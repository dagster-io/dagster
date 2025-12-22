# dagster-hightouch

A Dagster library for integrating with Hightouch, providing both legacy ops/assets API and modern Declarative Components.

## Installation

Install the library using pip:

```bash
pip install dagster-hightouch
```

## Configuration

Configure your Hightouch API key as a resource:

```python
from dagster_hightouch import HightouchResource

defs = Definitions(
    resources={
        "hightouch": HightouchResource(api_key="your-api-key"),
    },
    # ... other definitions
)
```

## Usage

### Using the HightouchSyncComponent (Declarative Components)

Create a YAML configuration file for your component:

```yaml
# components/hightouch_sync.yaml
type: dagster_hightouch.HightouchSyncComponent
attributes:
  asset:
    key: ["hightouch", "my_sync"]
    description: "Sync data to my destination"
  sync_id_env_var: "HIGHTOUCH_SYNC_ID"
```

Then, load the component in your definitions:

```python
import dagster as dg

defs = dg.components.load_defs("components/hightouch_sync.yaml")
```

Set the environment variable `HIGHTOUCH_SYNC_ID` to the ID of the Hightouch sync you want to trigger.

### Legacy Ops/Assets API

For backward compatibility, you can use the `hightouch_sync_op`:

```python
from dagster_hightouch import hightouch_sync_op, HightouchResource

@dg.job
def my_job():
    hightouch_sync_op.configured({"sync_id": "your-sync-id"})()

defs = dg.Definitions(
    jobs=[my_job],
    resources={"hightouch": HightouchResource(api_key="your-api-key")},
)
```

## API Reference

- `HightouchSyncComponent`: Declarative component for triggering Hightouch syncs.
- `HightouchResource`: Resource for interacting with the Hightouch API.
- `hightouch_sync_op`: Legacy op for triggering syncs.P