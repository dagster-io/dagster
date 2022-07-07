.. currentmodule:: dagster

IO Managers
==================================

IO managers are user-provided objects that store op outputs and load them as inputs to downstream
ops.

.. autodecorator:: io_manager

.. autoclass:: IOManager
    :members:

.. autoclass:: IOManagerDefinition
    :members:


Input and Output Contexts
-------------------------

.. autoclass:: InputContext
    :members:

.. autoclass:: OutputContext
    :members:


.. autofunction:: build_input_context

.. autofunction:: build_output_context



.. currentmodule:: dagster

Built-in IO Managers
------------------------

.. autodata:: mem_io_manager
  :annotation: IOManagerDefinition

.. autodata:: fs_io_manager
  :annotation: IOManagerDefinition

.. autodata:: custom_path_fs_io_manager
  :annotation: IOManagerDefinition


Input Managers
----------------------------------

Input managers are user-provided objects that specify how to load inputs.

.. autodecorator:: input_manager

.. autoclass:: InputManager
    :members:

.. autoclass:: InputManagerDefinition
    :members: