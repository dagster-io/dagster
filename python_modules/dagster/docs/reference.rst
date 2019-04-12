Reference
---------


Solid
^^^^^

A solid is a functional unit of computation. Solids define their (optionally typed) inputs
and outputs and the typed schema by which they can be configured, and can enfore expectations on
their outputs.

Solids can be strung together into `pipelines <#pipeline>`__ by defining
`dependencies <#dependency-definition>`__ between their inputs and outputs.  Solids are reusable
and instances of a solid may appear many times in a given pipeline, or across many different
pipelines.

Solids often wrap code written in or intended to execute in other systems (e.g., SQL statements,
Jupyter notebooks, or Spark jobs written in Scala), providing a common interface for defining,
orchestrating, and managing data processing applications with heterogeneous components

Solids are defined using the :func:`@lambda_solid <dagster.lambda_solid>` or
:func:`@solid <dagster.solid>` decorators, or using the underlying
:class:`SolidDefinition <dagster.SolidDefinition>` class. These APIs wrap an underlying
`transform function`, making its metadata queryable by higher-level tools.

Result
^^^^^^

Solid transform functions are expected to yield a stream of results. Implementers of a solid must
ensure their tranform yields :class:`Result <dagster.Result>` objects.

In the common case where only a single result is yielded, the machinery provides sugar allowing
the user to return a value instead of yielding it, and automatically wrapping the value in the
:class:`Result <dagster.Result>` class.

.. _dependency-definition:

Dependency Definition
^^^^^^^^^^^^^^^^^^^^^

Solids are linked together into `pipelines <#pipeline>`__ by defining the dependencies between
their inputs and outputs. Dependencies are data-driven, not workflow-driven -- they define what
data is required for solids to execute, not how or when they execute.

This reflects an important separation of concerns -- the same pipeline may have very different
execution semantics depending on the environment in which it runs or the way in which it is
scheduled, but these conditions should be expressed separately from its underlying structure.

Dependencies are defined when constructing pipelines, using the
:class:`DependencyDefinition <dagster.DependencyDefinition>` class.

Materialization
^^^^^^^^^^^^^^^

The outputs of solids can be materialized. The dagster engine can materialize outputs in a number
of formats (e.g., json, pickle), and can store materializations locally or on S3.

Materializations make it possible to introspect the intermediate state of a pipeline execution
and ask questions like, "Exactly what output did this solid have on this particular run?" This is
useful when auditing or debugging pipelines, and makes it possible to establish the `provenance` of
data artifacts.

Materializations also enable partial re-execution of pipelines "starting from" a materialized state
of the upstream execution. This is useful when a pipeline fails halfway through, or in order to
explore how new logic in part of a pipeline would have operated on outputs from previous runs of
the pipeline.

Expectation
^^^^^^^^^^^

An expectation is a predicate on a solid’s output. Expectations can be used to enforce runtime data
quality and integrity constraints, so that pipelines fail early -- before any downstream solids
execute on bad data.

Expectations are defined using the :class:`ExpectationDefinition <dagster.ExpectationDefinition>`
class. We also provide a `thin wrapper <https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-ge>`_
around the `great_expectations <https://github.com/great-expectations/great_expectations>`_ library
so you can use its existing repertoire of expectartions with Dagster.

.. _pipeline:

Pipeline
^^^^^^^^
Data pipelines are directed acyclic graphs (DAGs) of solids -- that is, they are made up of a number
of solids which have data `dependencies <#dependency-definition>`__ on each other (but no circular
dependencies), along with a set of associated pipeline context definitions, which declare the various
environments in which a pipeline can execute.

Pipelines are defined using the :class:`PipelineDefinition <dagster.PipelineDefinition>` class, and
their contexts are defined using :class:`PipelineContextDefinition <dagster.PipelineContextDefinition>`.

When a pipeline is combined with a given config conforming to one of its declared contexts, it can
be compiled by the Dagster engine into an execution plan that can be executed on various compute
substrates.

Concretely, a pipeline might include context definitions for local testing (where databases and
other resources will be mocked, in-memory, or local) and for running in production (where resources
will require different credentials and expose configuration options). When a pipeline is compiled
with a config corresponding to one of these contexts, it yields an execution plan suitable for the
given environment.

Repository
^^^^^^^^^^

A repository is a collection of pipelines that can be made available to the Dagit UI and other
higher-level tools. Repositories are defined using the
:class:`RepositoryDefinition <dagster.RepositoryDefinition>` class, and made available to
higher-level tools with a special ``repository.yml`` file that tells the tools where to look for a
repository definition.

Config
^^^^^^

Config defines the external environment with which a pipeline will interact for a given execution
plan. Config can be used to change solid behavior, define pipeline- or solid-scoped resources and
data that will be available during execution, or even shim solid inputs.

Config is complementary to data (solid inputs and outputs) -- think of inputs and outputs as
specifying `what` data a pipeline operates on, and config as specifying `how` it operates.

Concretely, imagine a pipeline of solids operating on a data warehouse. The solids might emit and
consume table partition IDs and aggregate statistics as inputs and outputs -- the data on which they
operate. Config might specify how to connect to the warehouse (so that the pipeline could also
operate against a local test database), how to log the results of intermediate computations, or
where to put artifacts like plots and summary tables.

Config Fields
^^^^^^^^^^^^^

Config fields define a schema for how users can config pipelines (using either Python dicts, YAML,
or JSON). They tell the Dagster engine how to type check config provided in one of these formats
against the pipeline context and enable many errors to be caught with rich messaging at compile time.

Config fields are defined using the :class:`Field <dagster.Field>` class.

DAG
^^^

DAG is short for `directed acyclic graph`. In this context, we are concerned with graphs where the
nodes are computations and the edges are dependencies between those computations. The dependencies
are `directed` because the outputs of one computation are the inputs to another.
These graphs are `acyclic` because there are no circular dependencies -- in other words, the graph
has a clear beginning and end, and we can always figure out what order to execute its nodes in.

Execution Plan
^^^^^^^^^^^^^^
An ExecutionPlan is the materialized DAG of ExecutionSteps created from a Pipeline and an Environment Config. The execution plan knows the topological ordering of the execution steps, enabling physical execution on one of the available executor engines.

Execution Step
^^^^^^^^^^^^^^

ExecutionStep(s) are materialized version of a Solid that will be executed. 

Execution steps also include materialization steps, expectation steps.

Dagster Event
^^^^^^^^^^^^^

When a pipeline is executed, DagsterEvents communicate the progress of execution. This includes top level events for the pipeline as well as the progress, materializations, and the results of each ExcecutionStep in an ExecutionPlan.

Execution Step States: start, failure, materialization, output, success, skip

Execution steps may fail, but other branches of the execution plan may continue to execute

InputDefinition
^^^^^^^^^^^^^^^

Optionally typed definition of the data that a solid requires in order to execute. Defined inputs may often also be shimmed through config.

OutputDefinition
^^^^^^^^^^^^^^^^

Optionally typed definition of the results that a solid will produce.

Dagster Types
^^^^^^^^^^^^^

The user-facing interface to the dagster type system

Config Types
^^^^^^^^^^^^

Tell the dagster engine how to translate from config (dict, YAML, JSON) to data that will be available in the context of a pipeline execution

Runtime Types
^^^^^^^^^^^^^

Enable type checking and custom materialization as data flows between execution steps

Resources
^^^^^^^^^

Resources are pipeline-scoped ways to make external resources (like database connections) available to solids during pipeline execution and clean up after execution resolves.
(nb this isn’t true in the multiprocessing or airflow cases)

Context
^^^^^^^

init, solid

IntermediatesManager 
^^^^^^^^^^^^^^^^^^^^

Responsible for managing the data that is being communicated between Solids and persisting them via an ObjectStore if configured to.

Object Store
^^^^^^^^^^^^

Dagster current supports storing intermediates to S3, and will support other object stores in the future.

Run Config
^^^^^^^^^^

Configuration for a particular run of a pipeline, allowing you to control things such as logging and run identification.

Executor
^^^^^^^^

Dagster can execute the execution plan in several modes; currently we support a simple executor (which serially executes the execution plan), and a multiprocessing executor, which runs the execution plan through an out-of-process executor.

Transform Function
^^^^^^^^^^^^^^^^^^

The user-supplied function which forms the heart of a solid definition and will be executed when the solid is invoked by the dagster engine

Thunk
^^^^^

Dagit
^^^^^

Execution Manager
^^^^^^^^^^^^^^^^^

SynchronousExecutionManager
MultiprocessingExecutionManager

