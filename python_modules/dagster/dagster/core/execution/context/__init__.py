'''

Dagster Contexts

Dagster defines a hierarchy of execution contexts. These contexts are threaded through to provision
access to resources, logging, and other shared state throughout the execution.

The inheritance structure of contexts is currently as follows:
====================================================================================================

ExecutionContext                                (user facing, used to construct )
 |
 construct_pipeline_execution_context()
 |
 V
SystemPipelineExecutionContext                  (contains SystemPipelineExecutionContextData)
 |
 |--> SystemStepExecutionContext                (produced by .for_step() on pipeline context)
       |
       |--> SystemTransformExecutionContext     (produced by .for_transform() on step context)
       |
       |--> SystemExpectationExecutionContext   (produced by .for_expectation() on step context)

====================================================================================================
In the system contexts, immutable state is stored in SystemPipelineExecutionContextData, and any
additional mutable fields are stored alongside that state as fields in the context object.

The below contexts are provisioned to wrap the corresponding system instance:
====================================================================================================

StepExecutionContext
 |                       AbstractTransformExecutionContext
 |                                     |
 |                -------------------------------------------
 |                |                                         |
 |                V                                         V
 |--> TransformExecutionContext              DagstermillInNotebookExecutionContext
 |                                           (defined in dagstermill)
 |--> ExpectationExecutionContext

====================================================================================================
These contexts exist so that we can add system-defined stuff to the System* contexts without
exposing them to users. System*Context classes are totally internal, whereas
TransformExecutionContext et all are passed to the user and exported at the global level.
'''
