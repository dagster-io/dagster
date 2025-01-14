---
title: "Dagster telemetry"
sidebar_position: 40
---

As open source project maintainers, we collect usage statistics to better understand how users engage with Dagster and to inform development priorities. Telemetry data motivates projects such as adding functionality in frequently used parts of the product, and helps us understand adoption of new features.

We collect telemetry from both the frontend and backend. We do not collect any data processed by Dagster pipelines, and we do not collect any identifiable information about your Dagster definitions, including the names of your assets, ops, or jobs.

Front end telemetry is collected from a JavaScript bundle hosted unminified at `https://dagster.io/oss-telemetry.js`. This bundle may change over time.

Backend telemetry collection is logged at `$DAGSTER_HOME/logs/` if `$DAGSTER_HOME` is set or `~/.dagster/logs/` if not set.

Use of telemetry data is governed by the [Dagster Privacy Policy](https://dagster.io/privacy).

If you’d like to opt out, you can add the following to `$DAGSTER_HOME/dagster.yaml` (creating that file if necessary):

```yaml
telemetry:
  enabled: false
```
