# Solid Guide


The core abstraction of Dagster is the *Solid*. A Solid is a functional unit of computation that consumes and produces data assets. It has a number of properties:

* Coarse-grained and for use in batch computations.
* Defines inputs and outputs, optionally typed within the Dagster type system.
* Embeddable in a dependency graph that is constructed by connecting inputs and outputs, rather than just the Solids themselves.
* Emits a stream of typed, structured events -- such as expectations and materializations -- that define the semantics of their computation.
* Defines self-describing, strongly typed configuration.
* Designed for testability and reuse.

This guide will cover these properties in detail, and then compare the Solid to the most analogous abstraction in Airflow, the "operator."


## Solid Concepts


### Data Dependencies

Solids are specialized functions, and as such have inputs and outputs.  Solids are meant to be embedded in a graph of dependencies, and within that graph, dependencies exist between those inputs and outputs rather than between the Solids themselves. In this way, the dependency graph in Dagster encodes not only execution ordering, but also the data or metadata needed by a Solid to execute.

Inputs and outputs can be optionally annotated with a type (defaults to the `Any` type). The type system of Dagster is simple and flexible. The core of a type is a function that takes a value and indicates whether the type check passed or failed. An input to a Solid is guaranteed to have passed that type check, and an output is similariy checked before flowing it to a downstream computation.

Through this dependency system Solids -- and graphs of Solids -- can describe their capabilities in a much richer format than in purely task-based systems. At a glance, a consumer or operator of a Solid can understand the data flowing their system. This parameterization also one of the reasons why these computations are more amenable to testing than in traditional task-based systems

#### Type System

The type system attached to these inputs and outputs is designed to augment rather than replace the existing type system in your target language or runtime. Data application authors are highly encouraged to use their native type system to maximum effect. The Dagster type is primarily concerned with:

* Communicating metadata to within code and to tooling.
* Providing guarantees at runtime and halting computation when those guarantees are violated.
* Defining config-driven hydration (i.e. reading values into memory) and materialization (i.e. writing values to a durable store.)
* Controlling serialization behavior.

We may introduce more formal semantics in the future, for pre-execution verification and more complicated semantic relationships between types, but that is not on our near-term roadmap.

#### Modeling Task Dependencies

Note that data dependencies are a strict superset of pure task dependencies, meaning dependencies at the task- or Solid-level rather than the input- or output-level. Task-level  dependencies (e.g. those supported the Airflow) can be precisely modeled in Dagster by having a single input or output with the type `Nothing`. Sometimes it is difficult to model computations functionally, and sometimes one is moving code from a system that did not encode data dependencies. Dagster is flexible enough to account for these practical realities.

### The Event Stream

Solids interact with the host runtime by emitting an event stream representing the semantics of computation and structured metadata attached to those events. These are designed to both communicate high quality information to authors and operators of data applications, and to be a foundation for tools that can operate on those semantic events. Tools can subscribe to these events via our GraphQL API.

Currently the body of a Solids can emit four event types: `Output`, `Materialization`, `ExpectationResult`, or `Failure` (failures are raised).

Let us define these in detail.

#### Outputs

Outputs emitted during Solid execution should be thought of as signals to follow-on computations within a graph, with optional metadata or data attached. The potential outputs of a Solid are known before execution, and are part of the signature of a Solid definition. These outputs have a name and a type.

Once all upstream outputs have been emitted for all of a particular Solids inputs, the Solid is free to proceed with execution. At this point, execution happens at the discretion of the physical orchestrator or engine, which is free to parallelize or schedule as it wants, provided it respects the semantics of the dependency graph.

Any output emitted by a Solid must conform to the type associated with the output. As noted before, the type check is an arbitrary function. If the type check fails, any Solid depending on that output does *not* execute, and the overall computation will report as failed.

Solids can define more than one output, and they can also be marked as optional, thus allowing branch-like behavior within computational graphs, where only the Solids downstream of the fired output are executed.

#### Materializations

A materialization is an event that indicates that the Solid has produced a data asset -- e.g. a file in an object store, a table in a data warehouse -- in an external system that will outlive the duration of the current execution.

The set of materializations produced by a Solid is *not* known prior to execution. A Solid is free to emit any materialization that it wants, for any reason. Materializations, like any event in the system, can have structured metadata attached. We expect this to be used for cases as varied as rendering links to internal tools in dagit (or other viewers), to infrastructure consuming those materializations and registering the creation of assets in a metastore.

A frequent pattern is to informally link outputs and materializations (this link may be formalized in the future). Take for example the common case of a Solid computing a table or a partition within a data warehouse. The author will likely want to both create a durable data asset as well as communicate metadata information about that asset to downstream Solids. In this case the natural thing to do emit both a materialization and an output, and ensure that the computation is idempotent with respect to the materialization.

#### Expectation Results

Expectation results indicate that an expectation (our name for a data quality test) has been executed. Expectations are an important concept in data applications, because typically an author does not have any control over the inputs to that computation. As a result, there are usually a large number of unexpressed, implicit assumptions about that incoming data in that computation.

Expectations are a mechanism by which data application author can make those *implicit* assumptions *explicit*. They can be an arbitrary computation, from a simple type check, to an existence of a file, all the way to a distributional analysis of an entire data set. The semantics are up to the author, as these expectations are user-defined.

Similar to materializations, Dagster provides the mechanism to communicate -- both to the runtime and by extension to tools -- structured metadata about these expectations, for visualization, tracking, or whatever purpose.

#### Failures

Solids can also communicate explicit failure conditions by throwing a Failure. While any arbitrary exception will also terminate computation, the Failure exception allows the user to communicate this very explicitly and attach structured metadata to that Failure.

### Environment vs. Business Logic

Solids are meant to be executed within a variety of environment contexts. Executing in multiple environments is a requirement both for testing and for reusability.

Every Solid is passed a context object representing the environment in which the Solid is executing. This provides a layer of abstraction that allows a data application author or infrastructure provider to separate the operating environment from business logic.

Dagster manages the construction of that context and attaches resources (such as a Spark context, a database connection, or a custom API for specific use cases) to it. It also provides a first-class facility (modes; see `ModeDefintion`) to switch out the implementation of those resources based on configuration. This means one has the means to execute a Solid in the context of, for example, a unit test mode, an integration test mode, and a production mode with multiple configurations within each mode, which leaving the core of the business logic unchanged.

Please see our testing guide for more detail.
 
## Relationship to Airflow

As of this writing, Airflow is the most widely adopted workflow engine in the open source ecosystem. It's useful to understand the relationship of this tool to Airflow.

Dagster is envisioned as separate, higher-level abstraction that can optionally be run *on top of Airflow itself*.

At first blush, The most analogous abstraction in Airflow is the operator. Airflow defines an operator as "a task within a workflow." Note there is also separate concept of Task. 

### Dependencies

Airflow operators are purely concerned with the physical execution of their computation and their order of execution relative to other operators within a given DAG. Once instantiated, they communicate nothing about the semantics and behavior the computations within them.

Dagster’s primary concern is both (a) expressing the semantic meaning of these data computations in a first-class way and (b) having an opinionated structure of those computations to make them more reusable, testable, etc. The direct value is for the user or tool author leveraging the programming model, and by the array of tools made possible by a layer of self-describing data computations.

As noted before in this guide, Solids within Dagster encode their dependencies not just in terms of execution order, but in terms of data.

By constrast, Airflow made a very explicit decision to not encode data dependencies in their core abstractions. 

The documentation is very clear: 

> This is a subtle but very important point: in general, if two operators need to share information, like a filename or small amount of data, you should consider combining them into a single operator.

Dagster takes a different view. We believe that data computation should be constructed to be as functional as is feasible. In reality, there *are* data dependencies between stages in a pipeline: tasks almost always consume the materializations of upstream tasks. Airflow simply makes the decision to not express them.

By contrast Dagster seeks to encode those directly both by linking depending between inputs and outputs, rather than at the Solid-level, and by introducing a type system to describe those inputs and outputs. This has a number of advantages: self-describing data computations, more reusability and testability, more reliable re-execution semantics, and, in the future, fully incremental computation.

Airflow actually ended up implementing a system to communicate out-of-band data between tasks -- called XCom -- but its use is actively discouraged by both the documentation and its original author.

### Signalling

Airflows tasks communicate the *final state* of their computation at runtime: success, failure, up-for-retry, etc. Dagster’s communication with its runtime is far richer. It does not just communicate the state of execution, but the semantics of the data during the computation.

As a result, tooling built on top of Dagster provides an entire new layer of monitoring, communicating expectations (data quality tests), materializations (information regarding data that will outlive the scope of the computation), and outputs (the signal for the follow on computations to execute, along with data or metadata to be passed to those computations).

### Context, Reusability, and Testability:

Instantiated Airflow DAGs have no parameters and no data-sharing between their task instances. Configuration is hard-coded for a particular DAG instantiation, and that instantiation is manually constructed by the DAG author. In traditional programming terms, airflow task instances -- and by extension their composition primitive, the DAG -- are functions without parameters. That makes them bound to a specific parameterization and execution environment, and inherently untestable.

By constrast Dagster is a layered system, where computation and dependency structure is written by the data application author abstractly, with a separate step to configure that computation and bind it to an execution environment. This machine-generated dependency graph, the execution plan, is the artifact bound to an execution environment. 

In Dagster's airflow integration it is actually this execution plan, and not the graph of Solids -- from which the DAG of airflow operators is dynamically generated. This is the concrete ramification of this fact: The Solid is actually a distinct and higher order abstraction than an Airflow operator.

In this model the Airflow DAG is the output of compilation process, so that the testing (and other software constructs) can be expressed in the higher level API concerned with the semantics of data applications, and not just their execution order.

## FAQ

### Why is it called a "Solid"?

It is a long and meandering journey, from a novel concept, to a familiar acronym, and back to a word.

In a data management system there are two broad categories of data: source data -- meaning the data directly inputted by a user, gathered from an uncontrolled external system, or generated directly by a sensor -- and computed data -- meaning data that is either created by computing on source data or on other computed data. Management of computed data is the primary concern of Dagster. Another name for computed data would be software-structured data. Or SSD. Given that SSD is already a well-known acronym for Solid State Drives we named our core concept for software-structured data a Solid.