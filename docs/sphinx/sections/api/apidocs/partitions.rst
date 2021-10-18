.. currentmodule:: dagster

Partitions
==========

.. autoclass:: PartitionedConfig
    :members:
.. autofunction:: static_paritioned_config
.. autofunction:: dynamic_paritioned_config
.. autofunction:: hourly_paritioned_config
.. autofunction:: daily_paritioned_config
.. autofunction:: weekly_paritioned_config
.. autofunction:: monthly_paritioned_config

.. autofunction:: schedule_from_partitions

Legacy Functions
================

The following functions are useful for working with partitions on legacy pipelines.

.. autoclass:: Partition
.. autoclass:: PartitionSetDefinition
    :members: get_partitions, create_schedule_definition

.. autofunction:: date_partition_range
.. autofunction:: identity_partition_selector
.. autofunction:: create_offset_partition_selector