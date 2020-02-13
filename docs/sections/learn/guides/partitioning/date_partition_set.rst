Creating a Date Partition Set
===============================

The most common partitioning scheme is date based partitions. We'll now create a :py:class:`PartitionSetDefinition <dagster.PartitionSetDefinition>` for a set of dates.

First, let's modify our solid to take a date range as config:


.. literalinclude:: ../../../../../examples/dagster_examples/stocks/repository.py
   :linenos:
   :lines: 4-19
   :language: python
   :caption: repository.py


Just as before, we write a function that returns a list of partitions, but this time we return a list of ``datetime`` objects.

.. literalinclude:: ../../../../../examples/dagster_examples/stocks/date_partitions.py
   :linenos:
   :lines: 9-15
   :language: python
   :caption: repository.py


Next, we define a function that takes a date :py:class:`Partition <dagster.Partition>` and returns config. Here, we calculate the first and last days of the previous month for each date partition to pass to the solid config.

.. literalinclude:: ../../../../../examples/dagster_examples/stocks/date_partitions.py
   :linenos:
   :lines: 18-34
   :language: python
   :caption: repository.py

Since it's not practical to hardcode all the possible date partitions, and we usually want date partitions between two date ranges, Dagster provides a utility to generate a list of partitions given a date range and time interval: :py:func:`date_partition_range <dagster.utils.partitions.date_partition_range>`. We'll use this function instead of the one we wrote above.

.. literalinclude:: ../../../../../examples/dagster_examples/stocks/date_partitions.py
   :linenos:
   :lines: 37-46
   :language: python
   :caption: repository.py


Now, let's load dagit again and head to the Playground tab. This time, we'll see our date partitions in the partition selector.

.. thumbnail:: playground_date_partitions.png