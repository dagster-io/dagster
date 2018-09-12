Custom Contexts
---------------

So far we have used contexts for configuring logging level only. This barely scratched the surface
of its capabilities.

Testing data pipelines, for a number of reasons, is notoriously difficult. One of the reasons is
that as one moves a data pipeline from local development, to unit testing, to integration testing, to CI/CD,
to production, or to whatever environment you need to operate in, the operating environment can
change dramatically.

In order to handle this, whenever the business logic of a pipeline is interacting with external resources
or dealing with pipeline-wide state generally, the dagster user is expected to interact with these resources
and that state via the context object. Examples would include database connections, connections to cloud services,
interactions with scratch directories on your local filesystem, and so on.

Let's imagine a scenario where we want to record some custom state in a key-value store for our execution runs.
A production time, this key-value store is a live store (e.g. DynamoDB in amazon) but we do not want to interact
this store for unit-testing. Contexts will be our tool to accomplish this. Goal.

We're going to have a simple pipeline that does some rudimentary arithmetic, but that wants record
the result computations in that key value store.

# TODO: do this
