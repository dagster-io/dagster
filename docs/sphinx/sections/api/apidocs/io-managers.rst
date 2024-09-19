.. currentmodule:: dagster

IO Managers
==================================

IO managers are user-provided objects that store op outputs and load them as inputs to downstream
ops.


.. autoclass:: ConfigurableIOManager

.. autoclass:: ConfigurableIOManagerFactory


.. autoclass:: IOManager

.. autoclass:: IOManagerDefinition

.. autodecorator:: io_manager

Input and Output Contexts
-------------------------

.. autoclass:: InputContext

.. autoclass:: OutputContext


.. autofunction:: build_input_context

.. autofunction:: build_output_context



.. currentmodule:: dagster

Built-in IO Managers
------------------------

.. autodata:: FilesystemIOManager
  :annotation: IOManagerDefinition

.. autodata:: InMemoryIOManager
  :annotation: IOManagerDefinition


The ``UPathIOManager`` can be used to easily define filesystem-based IO Managers.

.. autoclass:: UPathIOManager


Input Managers (Experimental)
----------------------------------

Input managers load inputs from either upstream outputs or from provided default values.

.. autodecorator:: input_manager

.. autoclass:: InputManager

.. autoclass:: InputManagerDefinition


Legacy
------

.. autodata:: fs_io_manager
  :annotation: IOManagerDefinition

.. autodata:: mem_io_manager
  :annotation: IOManagerDefinition