"""

Dagster Contexts

Dagster defines a hierarchy of execution contexts. These contexts are threaded through to provision
access to resources, logging, and other shared state throughout the execution.

The inheritance structure of contexts is currently as follows:
====================================================================================================

 construct_pipeline_execution_context()
 |
 V
SystemPipelineExecutionContext                  (contains SystemExecutionContextData)
 |
 |--> SystemStepExecutionContext                (produced by .for_step() on pipeline context)
       |
       |--> SystemComputeExecutionContext     (produced by .for_transform() on step context)

====================================================================================================
In the system contexts, immutable state is stored in SystemPipelineExecutionContextData, and any
additional mutable fields are stored alongside that state as fields in the context object.

The below contexts are provisioned to wrap the corresponding system instance:
====================================================================================================

StepExecutionContext
 |                       AbstractComputeExecutionContext
 |                                     |
 |                -------------------------------------------
 |                |                                         |
 |                V                                         V
 |--> SolidExecutionContext              DagstermillInNotebookExecutionContext
                                             (defined in dagstermill)

====================================================================================================
These contexts exist so that we can add system-defined stuff to the System* contexts without
exposing them to users. System*Context classes are totally internal, whereas
SolidExecutionContext et all are passed to the user and exported at the global level.
"""
