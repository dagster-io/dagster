.. currentmodule:: dagster

IO Managers
==================================

IO Managers
---------------

IO managers are user-provided objects that specify how to store step outputs and load step inputs.

.. autodecorator:: io_manager

.. autoclass:: IOManager
    :members:
    :show-inheritance:

.. autoclass:: IOManagerDefinition
    :members:


Input and Output Contexts
-------------------------

.. autoclass:: InputContext
    :members:

.. autoclass:: OutputContext
    :members:


Root Input Managers
--------------

Root input managers are user-provided objects that specify how to load step inputs.

.. autodecorator:: root_input_manager

.. autoclass:: RootInputManager
    :members:

.. autoclass:: RootInputManagerDefinition
    :members:


Built-in IO Managers
------------------------

.. autodata:: mem_io_manager

.. autodata:: fs_io_manager

.. autodata:: custom_path_fs_io_manager
