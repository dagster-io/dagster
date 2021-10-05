Jobs
====

The replacement for :py:class:`pipeline` / :py:class:`PipelineDefinition`, a ``Job`` binds a ``Graph`` and the resources it needs to be executable.

Jobs are created by calling :py:meth:`GraphDefinition.to_job` on a graph instance, or using the :py:class:`job` decorator.

.. currentmodule:: dagster

.. autodecorator:: job

.. autoclass:: JobDefinition
    :members: