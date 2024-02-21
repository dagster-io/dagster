---
title: 'Lesson 6: Practice partitioning a new dbt model'
module: 'dagster_dbt'
lesson: '6'
---

# Practice: Partitioning a new dbt model

Let’s pretend that you have a new model called `dim_zones`  that looks like the following:

```python
TODO:
```

You noticed that it is getting slow to compute because of the many zones some boroughs have, like Manhattan.

**Refactor this model to be partitioned by borough.**

---

## Hints

- Define a static partition for each borough:
  - TODO: ADD BOROUGHS
- Instead of a continuous, time-based partition, this uses a discrete set of partitions. In this case, use `context.partition_key` to get the partition key you want to work with.

---

## Check your work

The updated model should look similar to the following code snippet. Click **View answer** to view it.

```python {% obfuscated="true" %}
TODO: ADD ANSWER
```