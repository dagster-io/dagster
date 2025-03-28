---
title: 'Customizing run queue priority'
sidebar_position: 400
---

You can define custom prioritization rules for your Dagster instance using concurrency settings.

By the end of this guide, you’ll:

- Understand how run concurrency works
- Learn how to define custom prioritization rules
- Understand how prioritization rules and concurrency limits work together

## Understanding the run queue

The run queue is a sequence of Dagster runs waiting to be executed. Dagster pulls runs from the queue and calls `launch_run` on submitted runs. It operates as a first-in, first-out priority queue.

For example, if three runs are submitted in the following order:

1. Run `A`
2. Run `B`
3. Run `C`

Then the runs will be launched in the same order: Run `A`, then `B`, then `C`. This will be true unless there are [pool or run tag concurrency limits](/guides/operate/managing-concurrency) in place. The launch order can also be customized using prioritization rules, which we’ll cover later in this guide.

By default, all runs have a priority of `0`. Dagster launches runs with higher priority first. If multiple runs have the same priority, Dagster will launch the runs in the order they're submitted to the queue.

Negative priorities are also allowed and can be useful for de-prioritizing sets of runs, such as backfills.

## Defining queue prioritization rules

Custom priority is specified using the `dagster/priority` tag, which can be set in code on definitions or in the launchpad of the Dagster UI.

When defining a priority value, note that:

- Values must be integers specified as a string. For example: `"1"`
- Negative values are allowed. For example: `"-1"`

<Tabs>
<TabItem value="In Python" label="In Python">

**In Python**

In this example, the priority is set to `-1` with a `dagster/priority` tag value of `"-1"`:

<CodeExample
  startAfter="start_marker_priority"
  endBefore="end_marker_priority"
  path="docs_snippets/docs_snippets/deploying/concurrency_limits/concurrency_limits.py"
/>

</TabItem>
<TabItem value="In the Dagster UI" label="In the Dagster UI">

**In the Dagster UI**

Using the launchpad in the Dagster UI, you can also override priority tag values. In this example, we clicked the **Edit tags** button to display the following modal:

![Add tags to run modal in Dagster UI Launchpad](/images/guides/deploy/execution/dagster-priority-in-launchpad.png)

</TabItem>
</Tabs>

**Understanding prioritization rules and concurrency limits**

Unless tag concurrency limits and/or prioritization rules are in place, queued runs are executed in the order they’re submitted to the queue. However, a run blocked by tag concurrency limits won’t block runs submitted after it.

Let’s walk through an example to demonstrate. In this example, three runs are submitted in the following order:

1. Run `A`, tagged as `team: docs`
2. Run `B`, tagged as `team: docs`
3. Run `C`, which isn’t tagged

Without configured limits, these runs will be launched in the order they were submitted, or run `A`, then `B`, then `C`.

Before any more runs are launched, let’s add the following configuration to our instance’s settings:

```yaml
concurrency:
  runs:
    tag_concurrency_limits:
      - key: 'team'
        limit: 1
```

Now, runs `A` and `B` can’t execute concurrently, while there isn’t a limit on run `C`. Assuming each run executes for a minimum of five minutes, the order in which the runs are launched will change.

If the runs are submitted in the same order as before - that is, `A`, `B`, `C` - then the following will occur:

- Run `A` launches
- Run `B` B is skipped, as run `A` is in progress and concurrent runs are limited to `1` for the `team` tag
- Run `C` launches
- Run `B` launches after run `A` finishes

To summarize, due to the concurrency limit, this configuration will change the run launching order to `A`, `C`, `B`.
