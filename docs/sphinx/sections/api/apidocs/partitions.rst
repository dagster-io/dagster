.. currentmodule:: dagster

Partitions
==========

.. autoclass:: dagster.core.definitions.PartitionedConfig
    :members:

.. autofunction:: static_partitioned_config

.. autofunction:: dynamic_partitioned_config

.. autofunction:: hourly_partitioned_config

.. autofunction:: daily_partitioned_config

.. autofunction:: weekly_partitioned_config

.. autofunction:: monthly_partitioned_config

.. autofunction:: schedule_from_partitions
    :noindex:

Legacy Functions
================

The following functions are useful for working with partitions on legacy pipelines.

.. autoclass:: Partition

.. autoclass:: PartitionSetDefinition
    :members: get_partitions, create_schedule_definition

.. autofunction:: date_partition_range

.. autofunction:: identity_partition_selector

.. autofunction:: create_offset_partition_selector