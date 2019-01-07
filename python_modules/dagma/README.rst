============
dagma
============

Experimental AWS Lambda-based execution engine for dagster pipelines.


TODO
~~~~
- Implement Event (async)
- Log polling for Event execution
- Implement cancellation
- Package common dependencies into the runtime (maybe using
  [layers](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html))
- Move runtime to dagma-runtime bucket
- Only create a single function per run
- Configurable lifecycle rules for lambda execution
- Make lambda parameters all configurable
