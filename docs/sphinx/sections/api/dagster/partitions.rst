.. currentmodule:: dagster

##########
Partitions
##########

**********************
Partitions Definitions
**********************

.. autoclass:: PartitionsDefinition

.. autoclass:: HourlyPartitionsDefinition

.. autoclass:: DailyPartitionsDefinition

.. autoclass:: WeeklyPartitionsDefinition

.. autoclass:: MonthlyPartitionsDefinition

.. autoclass:: TimeWindowPartitionsDefinition

.. autoclass:: TimeWindow

.. autoclass:: StaticPartitionsDefinition

.. autoclass:: MultiPartitionsDefinition

.. autoclass:: MultiPartitionKey

.. autoclass:: DynamicPartitionsDefinition

.. autoclass:: PartitionKeyRange

*********************
Partitioned schedules
*********************

.. autofunction:: build_schedule_from_partitioned_job
    :noindex:

*****************
Partition mapping
*****************

.. autoclass:: PartitionMapping

.. autoclass:: TimeWindowPartitionMapping

.. autoclass:: IdentityPartitionMapping

.. autoclass:: AllPartitionMapping

.. autoclass:: LastPartitionMapping

.. autoclass:: StaticPartitionMapping

.. autoclass:: SpecificPartitionsPartitionMapping

.. autoclass:: MultiToSingleDimensionPartitionMapping

.. autoclass:: MultiPartitionMapping

***************
Backfill policy
***************

.. autoclass:: BackfillPolicy

******************
Partitioned config
******************

.. autoclass:: PartitionedConfig

.. autofunction:: static_partitioned_config

.. autofunction:: dynamic_partitioned_config

.. autofunction:: hourly_partitioned_config

.. autofunction:: daily_partitioned_config

.. autofunction:: weekly_partitioned_config

.. autofunction:: monthly_partitioned_config

*************************
Partition loading context
*************************

.. autofunction:: partition_loading_context