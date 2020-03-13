Scheduling Date Partitions
==========================

When using date partitions,  it is common to want to set up a schedule to run the date partitioned pipeline on a regular cadence, where at each scheduled execution time we execute a pipeline run corresponding to the most recently elapsed date partition.

To support this use case, we've added helpful decorators to define a schedule definition and a corresponding date partition set:

- :py:func:`@hourly_schedule <dagster.hourly_schedule>`
- :py:func:`@daily_schedule <dagster.daily_schedule>`
- :py:func:`@weekly_schedule <dagster.weekly_schedule>`
- :py:func:`@monthly_schedule <dagster.monthly_schedule>`

We can use the monthly decorator to create a partition set and schedule definition for our pipeline:

.. literalinclude:: ../../../../../examples/dagster_examples/stocks/schedules.py
   :linenos:
   :language: python
   :caption: schedules.py

Make sure to include a reference to the function in ``repository.yaml``:

.. code-block:: YAML

   scheduler:
        file: schedules.py
        fn: define_schedules

When we load dagit, we'll see our schedule as expected:

.. thumbnail:: schedule.png