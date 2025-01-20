---
title: Ops
---

The computational core of an [asset definition](assets/) is an op. Collections of ops can also be assembled to create a [graph](graphs). It is not necessary to use ops to use Dagster; most Dagster users will never need to create ops directly. For more information about ops, see the [legacy Dagster documentation](/todo).

An individual op should perform relatively simple tasks, such as:

- Deriving a dataset from other datasets
- Executing a database query
- Initiating a Spark job in a remote cluster
- Querying an API and storing the result in a data warehouse
- Sending an email or Slack message

![ops](/images/guides/build/ops/ops.png)
