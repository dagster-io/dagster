Priniciples
-----------

As noted above Dagster has a point of view and values regarding how data pipelines should be built and structured. We list them in no particular order:

Functional
^^^^^^^^^^
We believe that data pipelines should be organized as DAGs of functional, idempotent computations.
These computations injest input, do computation, and produce output, either with no side effects
or well-known, un-externalized side effects. Given the same inputs and configuration, the
computation should always produce the same output. These computations should also be
parameterizable, so that they can execute in different environments.

   * See https://bit.ly/2LxDgnr for an excellent overview of functional programing in batch computations.

Self-describing
^^^^^^^^^^^^^^^
Pipelines should be self-describing with rich metadata and types. Users should be able to approach
a pipeline, and use tooling to inspect the pipelines for their structure and capabilities. This
metadata should be co-located with actual code of the pipeline. Documentation and code is delivered
as a single artifact.

Compute-agnostic
^^^^^^^^^^^^^^^^
Heterogeneity in data pipelines is the norm, rather than the exception. Data pipelines are written
by many people in different personas -- data engineers, machine-learning engineers, data
scientists, analysts and so on -- who have different needs and tools, and are particular about
those tools.

Dagster has opinions about the structure and best practices of data pipelines. It has no opinions
about what libraries and engines use to do actual compute. Dagster pipelines can be comprised of
any python computation, which could be Pandas, Spark, or it could in turn invoke SQL or any
other DSL or library deemed appropriate to the task.

Testable 
^^^^^^^^
Testing data pipelines is notoriously difficult. Because it is so difficult it is often never
done, or done poorly. Dagster pipelines are designed to be tested. They have explicit support 
for pipeline authors to manage and maintain multiple operating environments -- for example, unit
testing, integration testing, and production environments, among others. In addition dagster can
execute arbitrary subsets and nodes of the pipeline, critical testability. (This capability
happens to be useful in operational contexts as well).

Verifiable data quality
^^^^^^^^^^^^^^^^^^^^^^^
Testing code is important in data pipelines, but it is not sufficient. Data quality tests -- run
during every meaningful stage of computation in production -- are critical to reduce the
maintenance burden of data pipelines. Pipeline authors generally do not have control of their
input data, and make many implicit assumptions about that data. The data formats can also change
over time. In order to control this entropy, Dagster encourages users to computationally verify
assumptions (known as expectations) about the data as part of the piplien process. This way if
those assumptions are broken, the breakage can be reported quickly, easily, and with rich metadata
and diagnostic information. These expectations can also serve as contracts between teams.

   * See https://bit.ly/2mxDS1R for a primer on pipeline tests for data quality.

Gradual, optional typing
^^^^^^^^^^^^^^^^^^^^^^^^

Dagster contains a type system to describe the values flowing through the pipeline and the
configuration of the pipeline. This allows nodes in a pipeline know if they are properly
arranged and configuration prior to execution before execution, and serves as value
documentation and runtime error checking. 
