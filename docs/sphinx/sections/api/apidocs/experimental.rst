Experimental Core APIs
======================

These are a set of API changes that seek to improve on the original Dagster Pipeline & Solid model in response to feedback from our users so far.

A toggle is available in the Dagit settings menu (top right) to view things in terms of these new APIs.

Graph
-----

The replacement for :py:class:`composite_solid` / :py:class:`CompositeSolidDefinition` . It has a more intuitive name and there is no longer a distinction between a graph for execution (pipeline) and a graph for composition (composite solid).

.. currentmodule:: dagster

.. autodecorator:: graph

.. autoclass:: GraphDefinition
    :members:

Job
---

The replacement for :py:class:`pipeline` / :py:class:`PipelineDefinition`, a ``Job`` binds a ``Graph`` and the resources it needs to be executable.

Jobs are created by calling :py:meth:`GraphDefinition.to_job` on a graph instance.

.. currentmodule:: dagster

.. autoclass:: JobDefinition
    :members:

Op
--

The replacement for :py:class:`solid`, has a more intuitive name and offers a more concise way of defining inputs & outputs.

.. currentmodule:: dagster

.. autodecorator:: op

.. autoclass:: In

.. autoclass:: Out

.. autoclass:: DynamicOut


Testing
-------

.. currentmodule:: dagster

.. autofunction:: build_op_context

Explicit in-process execution APIs have been added to better facilitate testing of Graphs and Jobs.

Jobs can be tested with :py:meth:`JobDefinition.execute_in_process`, and Graphs with :py:meth:`GraphDefinition.execute_in_process`

.. currentmodule:: dagster.core.execution.execution_results

.. autoclass:: InProcessGraphResult
    :members:

.. autoclass:: InProcessOpResult
    :members:

.. autoclass:: NodeExecutionResult
    :members:

Partition-Based Schedules
---------

New APIs have been added to better integrate partition-based scheduling with the job API. These new APIs replace the existing :py:meth:`daily_schedule`, :py:meth:`weekly_schedule`, :py:meth:`monthly_schedule`, and :py:meth:`hourly_schedule` decorators.

.. currentmodule:: dagster

.. autodecorator:: daily_partitioned_config

.. autodecorator:: monthly_partitioned_config

.. autodecorator:: hourly_partitioned_config

.. autodecorator:: weekly_partitioned_config
