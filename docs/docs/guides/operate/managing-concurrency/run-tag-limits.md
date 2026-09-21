---
title: Run tag concurrency limits
description: How to limit the number of runs in progress by run tag.
sidebar_position: 400
---

## Limit the number of runs that can be in progress by run tag

You can limit the number of in-progress runs by [run tag](/guides/build/assets/metadata-and-tags/tags#run-tags). This is useful for limiting sets of runs independent of which assets or ops it is executing. For example, you might want to limit the number of in-progress runs for a particular schedule. Or, you might want to limit the number of in-progress runs for all backfills.

```yaml
concurrency:
  runs:
    tag_concurrency_limits:
      - key: 'dagster/sensor_name'
        value: 'my_cool_sensor'
        limit: 5
      - key: 'dagster/backfill'
        limit: 10
```

### Limit the number of runs that can be in progress by unique tag value

To apply separate limits to each unique value of a [run tag](/guides/build/assets/metadata-and-tags/tags#run-tags), set a limit for each unique value using `applyLimitPerUniqueValue`. For example, instead of limiting the number of backfill runs across all backfills, you may want to limit the number of runs for each backfill in progress:

```yaml
concurrency:
  runs:
    tag_concurrency_limits:
      - key: 'dagster/backfill'
        value:
          applyLimitPerUniqueValue: true
        limit: 10
```

### Limit the number of runs that can be in progress by code location

Every run is automatically [tagged](/guides/build/assets/metadata-and-tags/tags#run-tags) with its code location using the `dagster/code_location` tag. You can use this tag to control run concurrency at the code location level. This is useful in multi-team environments where each team has their own code location and you want to ensure fair resource allocation.

To apply a limit per code location, combine the `dagster/code_location` tag with `applyLimitPerUniqueValue`:

```yaml
concurrency:
  runs:
    tag_concurrency_limits:
      - key: 'dagster/code_location'
        value:
          applyLimitPerUniqueValue: true
        limit: 10
```

This configuration limits each code location to 10 concurrent runs. For example, if you have three code locations (`team_a`, `team_b`, and `team_c`), each can have up to 10 runs in progress simultaneously.
