.. currentmodule:: dagster

IO Managers
==================================

IO Managers
---------------

IO managers are user-provided objects that store solid outputs and load them as inputs to downstream
solids.

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


Root Input Managers
--------------

Root input managers are user-provided objects that specify how to load inputs that aren't connected
to upstream outputs.

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
