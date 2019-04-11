Reference
---------


Solid
^^^^^

A solid is a functional unit of computation in a data pipeline, created by writing a SolidDefinition in client code.

Solids are reusable

Solids define their (optionally typed) inputs and outputs, and can enforce expectations on their outputs

Solid transform functions often wrap code written in or to execute on other systems (e.g., SQL, Jupyter notebooks, Spark jobs), providing a common interface

Result
^^^^^^

Solid transform functions are expected to yield (not return) a stream of Results. Implementers of a SolidDefinition must provide a transform that yields objects of this type. In the common case, we sugar return to match this interface.

Dependency Definition
^^^^^^^^^^^^^^^^^^^^^

Solids are linked together by defining dependencies between their inputs and outputs. Dependencies are data driven, not workflow driven -- they define what data is required for transforms to execute, not how or when they execute.

Materialization
^^^^^^^^^^^^^^^

Solids can materialize their outputs, which happens during execution planning where the dagster engine adds execution steps that handle materializing solid outputs to one of “value”, “json”, or “pickle” (the latter two expect to be used with file system paths)

Materializations make it possible to introspect the intermediate state of a pipeline execution and ask questions like, exactly what output did this solid have on this particular run? They enable audit, debugging, and provenance.

Expectation
^^^^^^^^^^^

An expectation is a predicate on a solid’s output which can be used to enforce data quality and integrity constraints before any downstream solids execute

Pipeline
^^^^^^^^

A pipeline is the combination of (1) a list of solid definitions, (2) dependencies, and (3) pipeline contexts, which,  together with a context, can be compiled by the dagster engine into an execution plan.

Repository
^^^^^^^^^^

A repository is a collection of pipelines configured by a repository.yml file, which can be made available to the dagster UI.

Config
^^^^^^

Config defines the external environment with which a pipeline will interact for a given execution plan: it can be used to change solid behavior, shim solid inputs, or define pipeline- or solid-scoped resources and data that will be available during execution.

Config Fields
^^^^^^^^^^^^^

Config fields define a schema for how users can config pipelines (in Python dicts, YAML, or JSON). They tell the dagster engine how to translate config into the pipeline context and enable many errors to be caught with rich messaging at  compile time.

DAG
^^^

DAG is short for Directed Acyclic Graph. In this context we are talking about a graph where the nodes are computations (Solid or ExecutionStep) and the edges are dependencies between those computations. The dependencies are directed, representing the outputs of one computation being the inputs to another. These graphs have no cycles, which means we have a clear beginning and end. 

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

