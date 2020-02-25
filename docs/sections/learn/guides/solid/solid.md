# Solid Guide

The core abstraction of Dagster is the _solid_. A solid is a functional unit of computation that
consumes and produces data assets. It has a number of properties:

- Coarse-grained and for use in batch computations.
- Defines inputs and outputs, optionally typed within the Dagster type system.
- Embeddable in a dependency graph that is constructed by connecting the inputs and outputs of
  multiple solids.
- Emits a stream of typed, structured events -- such as expectations and materializations --
  corresponding to the semantics of its computation.
- Exposes self-describing, strongly typed configuration.
- Testable and reusable.

## Solid Concepts

### Data Dependencies

Solids are functions, and as such have inputs and outputs. Solids are meant to be embedded in a
graph of dependencies constructed by connecting the inputs and outputs of multiple solids. This
dependency graph, or _pipeline_, explicitly encodes the data or metadata required by a solid in
order to execute, and implicitly encodes the order in which solids will execute.

#### Type System

A solid's inputs and outputs can be optionally annotated with a type (defaults to `Any`). The
Dagster type system is simple and flexible. Dagster types are primarily concerned with:

- Providing guarantees ("type checks") at runtime and halting computation when those guarantees
  are violated.
- Providing a configuration schema that allows values to be stubbed in from and written out to
  durable storage (the "input hydration config" and "output materialization config").
- Communicating metadata about type checks, hydration, and materializations to framework code and
  to tooling.

The core of a type is a type check function that takes a value, checks that the value satisfies
some condition, and communicates success or failure. Inputs to a solid are guaranteed to have
passed their corresponding type checks, and outputs are checked in turn before they flow to
downstream solids.

This type system is designed to augment rather than replace the existing type systems of Dagster's
target language or runtime (for now, Python). Data application authors are highly
encouraged to use their native type system to maximum effect.
We may introduce more formal semantics in the future, to enable pre-execution verification and more
complicated semantic relationships between types.

#### Modeling Task Dependencies

Note that data dependencies are a strict superset of the "task" dependencies that drive many related
graph execution systems, such as Airflow or Azkaban. Dependencies between solids that don't depend
on any semantically specified outputs can be modeled in Dagster using inputs and outputs with the
type `Nothing`. This facility acknowledges that it can sometimes be difficult to model computations
functionally, for instance when interfacing with or migrating code from a system that does not
encode data dependencies. Dagster is flexible enough to account for these practical realities.

### The Event Stream

Solids interact with the host runtime by emitting a stream of events that represent the semantics of
computation, as well as structured metadata attached to those events. These are designed to
communicate high quality, human-readable information to the authors and operators of data
applications, as well as to support tools that can operate on the event streams. Tools can subscribe
to these events via our GraphQL API.

Currently the body of a solid can emit four event types: `Output`, `Materialization`,
`ExpectationResult`, or `Failure` (failures are emitted using `raise` rather than `yield`). In the
simplest case, where a solid has a single output, the framework provides sugar allowing the solid
to simply `return` a single value.

#### Outputs

Outputs emitted during solid execution should be thought of as signals to downstream computations
within a graph, with optional metadata or data attached. The potential outputs of a solid are
known before execution, and are part of the signature of a solid definition. Each output has a name
and a type.

Once all the upstream outputs on which all of a solid's inputs depend have been emitted, the solid
is available for execution. The execution of solids proceeds at the discretion of the executor,
which is free to parallelize or schedule computation as it wants, provided it respects the semantics
of the pipeline's dependency graph.

Any output emitted by a solid must conform to the type associated with the output. As noted before,
the type check is an arbitrary function. If the type check for an output fails, any solid depending
on that output will _not_ execute, and the overall pipeline will report as failed.

Solids can define more than one output, and outputs may also be marked as optional. This enables
branch-like behavior within pipelines, where solids that are downstream of optional outputs are
skipped.

#### Materializations

A materialization indicates that a solid has produced a data asset -- e.g. a file in an object
store, a table in a data warehouse -- in an external system that will outlive the current
computation.

The set of materializations produced by a solid is _not_ known prior to execution. A solid is free
to emit any materialization that it wants, for any reason. Materializations, like any event in the
system, can have structured metadata attached. We expect this to be used for cases as varied as
rendering links to internal tools in Dagit (or other viewers), to infrastructure consuming those
materializations and registering the creation of assets in a metastore.

A frequent pattern is to informally link outputs and materializations (this link may be formalized
in the future). Take for example the common case of a solid computing a table or a partition within
a data warehouse. The author will likely want to both create a durable data asset as well as
communicate metadata about that asset to downstream solids so they can operate on it. In this case
the natural thing to do emit both a materialization and an output, and ensure that computation
is idempotent with respect to the materialized data asset.

#### Expectation Results

Expectation results indicate that an expectation (our name for a data quality test) has been
executed. Expectations are an important concept in data applications, since data typically flows
into a computation from processes over which the author of an application has no control. As a
result, data applications usually contain a large number of unexpressed, implicit assumptions about
the structure of their inputs.

Expectations are a mechanism by which data application author can make those _implicit_ assumptions
_explicit_. Expectations can encapsulate arbitrary computation: perhaps a simple type check, or
asserting the existence of a file on disk, or a distributional analysis of an entire data set.

As with materializations, Dagster provides the mechanism to communicate -- to the runtime
and by extension to tools -- structured metadata about these expectations, for visualization,
tracking, or whatever purpose. In future, we intend to expand the tooling built on top of structured
expectation metadata.

#### Failures

Solids can also communicate explicit failure conditions by throwing a Failure, which lets user code
terminate computation explicitly and with structured metadata attached.

### Environment vs. Business Logic

Solids are meant to be executed within a variety of environments. Executability in multiple
environments is a requirement both for testing and for reuse.

Every solid execution is passed a context object which represents the environment in which the solid
is currently being executed. This provides a layer of abstraction that allows a data application
author or infrastructure provider to separate the operating environment from business logic.

Dagster manages the construction of that context and provides facilities to inject values into and
attach resources (such as a Spark context, a database connection, or a custom API for specific use
cases) to it. It also provides a first-class facility (the `ModeDefintion`) that lets users swap
out the implementation of those resources based on configuration. This lets the same solid code
execute in the context of, for example, a unit test mode, an integration test mode, and a production
mode, while leaving the business logic encoded in the solid unchanged.

Please see our testing guide for more detail.

## FAQ

### Why is it called a "solid"?

It is a long and meandering journey, from a novel concept, to a familiar acronym, and back to a
word.

In a data management system there are two broad categories of data: source data -- meaning the data
directly inputted by a user, gathered from an uncontrolled external system, or generated directly
by a sensor -- and computed data -- meaning data that is either created by computing on source data
or on other computed data. Management of computed data is the primary concern of Dagster. Another
name for computed data would be software-structured data. Or SSD. Given that SSD is already a
well-known acronym for Solid State Drives we named our core concept for software-structured data
a solid.
