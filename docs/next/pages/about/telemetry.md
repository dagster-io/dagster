---
title: 'Dagster telemetry | Dagster Docs'
---

# Dagster telemetry

As an open source project, we collect usage statistics to better understand how users engage with Dagster and to inform development priorities. Telemetry data will motivate projects such as adding functionality in frequently-used parts of the product and will help us understand adoption of new features.

The following is an example telemetry blob:

```python
def a():
  return 1
```

---

```json
{
  "location_name_hash": "94ca34d0fb35a5612a30090cac5caef430f7ce377368177da02fd8e0535752f6",
  "num_assets_in_repo": "1",
  "num_dynamic_partitioned_assets_in_repo": "0",
  "num_pipelines_in_repo": "1",
  "num_schedules_in_repo": "0",
  "num_sensors_in_repo": "0",
  "pipeline_name_hash": "",
  "repo_hash": "f17e9128abe12b4ff329425c469a7c5abc06bace32a2237848bc3a71cf9ef808",
  "source": "dagster-webserver"
}
```

We will not see or store any data that is processed within ops and jobs. We will not see or store op definitions (including generated context) or job definitions (including resources).

To see the logs we send, open `$DAGSTER_HOME/logs/` if `$DAGSTER_HOME` is set or `~/.dagster/logs/` if not set.

If you'd like to opt-out, you can add the following to `$DAGSTER_HOME/dagster.yaml` (creating that file if necessary):

```yaml
telemetry:
  enabled: false
```
