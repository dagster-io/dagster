---
description: Configure job-level timeouts in Dagster to prevent runs from executing indefinitely or overlapping with subsequent scheduled runs.
sidebar_position: 700
title: Configuring job-level timeouts
---

By default, Dagster jobs have no automatic timeout. A stuck or runaway run can execute indefinitely until it's terminated manually. Job-level timeouts let you set a maximum runtime per job so the system can terminate runs that exceed it.

This is especially useful for:

- Scheduled jobs that should not overlap with subsequent ticks
- Jobs that depend on external systems prone to hangs
- Long-running jobs where you want to bound the worst case

## Configuration

Use the `dagster/max_runtime` tag on the job (or run) to set the timeout in seconds. The mechanism is the same in Dagster Open Source and Dagster+, but how you enable it differs slightly between each.

### Dagster Open Source

1. Add the `dagster/max_runtime` tag (in seconds) to your job definition.
2. Enable run monitoring in your `dagster.yaml`:

   ```yaml
   run_monitoring:
     enabled: true
   ```

3. Restart your Dagster instance so the daemon picks up the configuration change.

### Dagster+

1. Add the `dagster/max_runtime` tag (in seconds) to your job definition. Tags can also be applied at run launch time from the [Launchpad](/guides/operate/webserver) or via the Dagster+ deployment settings.

No agent or instance restart is required.

## Choosing a timeout value

Pick a timeout based on observed runtime, with headroom for normal variance:

- Watch a few weeks of completion times for the job.
- Set the timeout above the typical p99 runtime, not just the average.
- Re-evaluate after meaningful changes to data volume, dependencies, or upstream systems.

## Related documentation

- [Run monitoring and timeouts](/deployment/execution/run-monitoring#general-run-timeouts)
- [Run retries](/deployment/execution/run-retries)
