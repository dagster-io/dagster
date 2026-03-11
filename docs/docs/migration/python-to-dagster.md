---
title: Python to Dagster
description: Bring cron-scheduled Python scripts into Dagster as assets.
last_update:
  author: Dennis Hume
sidebar_position: 600
---

Many pipelines start as plain Python scripts scheduled with cron. Bringing them into Dagster gives you a UI, run history, alerting, and retries without rewriting the script itself.

<Tabs>
<TabItem value="before" label="Before">

A script invoked by cron with a date argument:

```python
# crontab: 0 2 * * * python /opt/scripts/extract_data.py --date $(date +%F)
```

```python
#!/usr/bin/env python3
# extract_data.py
import json
from datetime import datetime
from pathlib import Path

def main():
    output_dir = Path("/tmp/data")
    output_dir.mkdir(exist_ok=True)
    data = {"extracted_at": datetime.now().isoformat(), "records": [1, 2, 3]}
    (output_dir / "data.json").write_text(json.dumps(data))
    print(f"Extracted {len(data['records'])} records")

if __name__ == "__main__":
    main()
```

</TabItem>
<TabItem value="after" label="After">

A Dagster asset that executes the unchanged script via `subprocess`:

<CodeExample
  path="docs_projects/project_mini/src/project_mini/defs/migrating_to_dagster/python_script.py"
  language="python"
  title="src/project_mini/defs/migrating_to_dagster/python_script.py"
/>

</TabItem>
</Tabs>

The `run_python_script` asset accepts a `ScriptConfig` with the script path and any extra arguments. The script runs unchanged. Stdout and return code are captured as [asset metadata](/guides/build/assets/metadata-and-tags).

Because `run_python_script` requires config, you can't materialize it with a single click—you need to supply the script path. Do this via the config editor in the Dagster UI when triggering a manual run, or by passing a `RunConfig` in a job definition:

```python
job = dg.define_asset_job(
    "my_script_job",
    selection=[run_python_script],
    config=dg.RunConfig(
        ops={"run_python_script": ScriptConfig(script_path="/opt/scripts/extract_data.py")}
    ),
)
```

The `run_daily_script` variant uses [daily partitions](/guides/build/partitions-and-backfills/partitioning-assets) to pass a `--date` argument automatically, replacing the need to construct dates in cron commands.

## Changes

**The script runs unchanged.** Unlike migrating from Airflow or Prefect, you don't rewrite your logic into Dagster primitives. The asset wraps the script via `subprocess`, so the existing code, dependencies, and behavior stay exactly the same.

**Cron expressions become `@schedules`.** A crontab entry like `0 2 * * *` becomes a `@dg.schedule` wrapping a `define_asset_job`. The schedule is version-controlled alongside your asset code and visible in the Dagster UI, replacing the invisible cron entry.

**Hardcoded arguments become Dagster run configuration.** Arguments previously passed on the command line (dates, paths, environment flags) become `RunConfig` fields. This makes each run's inputs explicit in the run history. For more information, see the [run configuration docs](/guides/operate/configuration/run-configuration).

**Stdout and exit codes become observable.** Output that previously disappeared into cron logs is captured as asset metadata, giving you a searchable, linkable record of every run.

**Secrets and environment variables remain in place.** Environment variables or config files read by the script continue to work as written, since the subprocess inherits the environment. For secrets that need per-environment configuration in Dagster, consider wrapping them in a Dagster [resource](/guides/build/external-resources/) and passing values through environment variables set on the resource.
