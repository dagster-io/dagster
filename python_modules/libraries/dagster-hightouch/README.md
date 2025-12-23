## dagster-hightouch

A Dagster library for triggering syncs in Hightouch.

### Installation

To install the library, use pip alongside your existing Dagster environment.

```bash
pip install dagster-hightouch
```

### Configuration

First, you'll need to specify your [Hightouch API](https://hightouch.com/docs/developer-tools/api-guide/) key as a resource.

```python
# resources.py
from dagster_hightouch.resources import ht_resource as hightouch_resource

ht_resource = hightouch_resource.configured(
    {"api_key": "555555-4444-3333-2222-1111111111"},
)
```

### Ops

The `hightouch_sync_op` will call the Hightouch API to trigger
a sync and monitor it until it completes.

```python
from dagster import ScheduleDefinition, get_dagster_logger, job
from dagster_hightouch.ops import hightouch_sync_op
from .resources import ht_resource

# Sync IDs are set as constants. You can also use
# the sync slug, read the documentation for other
# options.

HT_WS = "23620"
HT_ORG = "39619"

# We define two configured sync ops
run_ht_sync_workspaces = hightouch_sync_op.configured(
    {"sync_id": HT_WS}, name="hightouch_sfdc_workspaces"
)
run_ht_sync_orgs = hightouch_sync_op.configured(
    {"sync_id": HT_ORG}, name="hightouch_sfdc_organizations"
)

# And create a job with the defined resources, specifying the dependencies.
@job(
    resource_defs={
        "hightouch": ht_resource,
    }
)
def ht_sfdc_job():

    ht_orgs = run_ht_sync_orgs(start_after=ht_contacts)
    run_ht_sync_workspaces(start_after=ht_orgs)

# And we schedule it to run every 30 mins.
every_30_schedule = ScheduleDefinition(job=ht_sfdc_job, cron_schedule="*/30 * * * *")
```

### Components (Modern)

You can now use Hightouch as a Dagster Component. This allows you to define syncs in YAML.

```yaml
# code/component.yaml
type: HightouchSyncComponent
attributes:
  sync_id: "12345"
  asset:
    key: ["hightouch", "my_sync_asset"]
```
