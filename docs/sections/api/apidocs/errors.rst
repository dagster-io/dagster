Errors
=========

.. currentmodule:: dagster

Core dagster error classes. All errors thrown by the Dagster framework inherit from
:class:`DagsterError <dagster.DagsterError>`. Users should not subclass this base class for their
own exceptions.


.. autoexception:: DagsterError

.. autoexception:: DagsterEventLogInvalidForRun

.. autoexception:: DagsterExecutionStepExecutionError

.. autoexception:: DagsterExecutionStepNotFoundError

.. autoexception:: DagsterInvalidConfigError

.. autoexception:: DagsterInvalidDefinitionError

.. autoexception:: DagsterInvariantViolationError

.. autoexception:: DagsterResourceFunctionError

.. autoexception:: DagsterRunNotFoundError

.. autoexception:: DagsterStepOutputNotFoundError

.. autoexception:: DagsterSubprocessError

.. autoexception:: DagsterTypeCheckDidNotPass

.. autoexception:: DagsterTypeCheckError

.. autoexception:: DagsterUnknownResourceError

.. autoexception:: DagsterUnmetExecutorRequirementsError

.. autoexception:: DagsterUserCodeExecutionError
