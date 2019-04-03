Principles
-------------------------
Dagster is opinionated about how data pipelines should be built and structured. What do we think
is important?

Functional
^^^^^^^^^^
Data pipelines should be expressed as DAGs (directed acyclic graphs) of functional, idempotent
computations. Individual nodes in the graph consume their inputs, perform some computation, and
yield outputs, either with no side effects or with clearly advertised side effects. Given the
same inputs and configuration, the computation should always produce the same output. If these 
computations have external dependencies, these should be parametrizable, so that the computations
may execute in different environments.

   * See Maxime Beauchemin's Medium article on `Functional Data Engineering <https://bit.ly/2LxDgnr>`_
     for an excellent overview of functional programing in batch computations.

Self-describing
^^^^^^^^^^^^^^^
Data pipelines should be self-describing, with rich metadata and types. Users should be able to
approach an unfamiliar pipeline and use tooling to inspect it and discover its structure,
capabilities, and requirements. Pipeline metadata should be co-located with the pipeline's actual
code: documentation and code should be delivered as a single artifact.

Compute-agnostic
^^^^^^^^^^^^^^^^
Heterogeneity in data pipelines is the norm, rather than the exception. Data pipelines are written
collaboratively by many people in different personas -- data engineers, machine-learning engineers,
data scientists, analysts and so on -- who have different needs and tools, and are particular about
those tools.

Dagster has opinions about best practices for structuring data pipelines. It has no opinions
about what libraries and engines should do actual compute. Dagster pipelines can be made up of
any Python computations, whether they use Pandas, Spark, or call out to SQL or any other DSL or
library deemed appropriate to the task.

Testable
^^^^^^^^
Testing data pipelines is notoriously difficult. Because testing is so difficult, it is often never
done, or done poorly. Dagster pipelines are designed to be tested. Dagster provides explicit support
for pipeline authors to manage and maintain multiple execution environments -- for example, unit
testing, integration testing, and production environments. Dagster can also execute arbitrary
subsets and nodes of pipelines, which is critical for testability (and useful in operational
contexts as well).

Verifiable data quality
^^^^^^^^^^^^^^^^^^^^^^^
Testing code is important in data pipelines, but it is not sufficient. Data quality tests -- run
during every meaningful stage of computation in production -- are critical to reduce the
maintenance burden of data pipelines. Pipeline authors generally do not have control over their
input data, and make many implicit assumptions about that data. Data formats can also change
over time. In order to control this entropy, Dagster encourages users to computationally verify
assumptions (known as expectations) about the data as part of the pipeline process. This way, when
those assumptions break, the breakage can be reported quickly, easily, and with rich metadata
and diagnostic information. These expectations can also serve as contracts between teams.

   * See https://bit.ly/2mxDS1R for a primer on pipeline tests for data quality.

Gradual, optional typing
^^^^^^^^^^^^^^^^^^^^^^^^
Dagster contains a type system to describe the values flowing through the pipeline and the
configuration of the pipeline. As pipelines mature, gradual typing lets nodes in a pipeline
know if they are properly arranged and configured prior to execution, and provides rich
documentation and runtime error checking.
