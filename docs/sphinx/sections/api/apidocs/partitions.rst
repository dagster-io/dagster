.. currentmodule:: dagster

Partitions
==========

.. autoclass:: Partition
.. autoclass:: PartitionedConfig
    :members:

.. autofunction:: schedule_from_partitions

Legacy Functions
================

The following functions are useful for working with partitions on legacy pipelines.

.. autoclass:: PartitionSetDefinition
    :members: get_partitions, create_schedule_definition

.. autofunction:: date_partition_range
.. autofunction:: identity_partition_selector
.. autofunction:: create_offset_partition_selector