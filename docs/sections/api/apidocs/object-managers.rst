.. currentmodule:: dagster

Object, Input, and Output Managers
==================================

Object Managers
---------------

Object managers are user-provided objects that specify how to store step outputs and load step inputs.

.. autodecorator:: object_manager

.. autoclass:: ObjectManager
    :members:
    :show-inheritance:

.. autoclass:: ObjectManagerDefinition
    :members:


Input and Output Contexts
-------------------------

.. autoclass:: InputContext
    :members:

.. autoclass:: OutputContext
    :members:


Input Managers
--------------

Input managers are user-provided objects that specify how to load step inputs.

.. autodecorator:: input_manager

.. autoclass:: InputManager
    :members:

.. autoclass:: InputManagerDefinition
    :members:


Output Managers
---------------

Output managers are user-provided objects that specify how to handle step outputs.

.. autodecorator:: output_manager

.. autoclass:: OutputManager
    :members:

.. autoclass:: OutputManagerDefinition
    :members:


Built-in Object Managers
------------------------

.. autodata:: mem_object_manager

.. autodata:: fs_object_manager

.. autodata:: custom_path_fs_object_manager
