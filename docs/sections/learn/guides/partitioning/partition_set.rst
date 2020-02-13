Creating a Simple Partition Set
==================================

If we're trying to calculate the total volume of trades for all stocks in January 2019, it might be difficult to get and process all the data in one query. Since we already have a pipeline that calculates total volume for a single stock, and it takes the stock ticker symbol as config, we can create a partition set to make it easy to run the pipeline for each partition.

Let's assume there's only four stocks in the world: ``AAPL``, ``GOOG``, ``MSFT``, ``TSLA``

First, we write a function that returns a list of partitions. Here, our partitions are simply the stock tickers, and we wrap them in :py:class:`Partition <dagster.Partition>` objects.

.. literalinclude:: ../../../../../examples/dagster_examples/stocks/simple_partitions.py
   :linenos:
   :lines: 1-10
   :language: python
   :caption: repository.py
   :emphasize-lines: 4-10


Next, we define a function that takes a :py:class:`Partition <dagster.Partition>` and returns config. We pass the :py:class:`Partition <dagster.Partition>` value to the ``query_historical_stock_data`` solid config, just like we did in the previous section.

.. literalinclude:: ../../../../../examples/dagster_examples/stocks/simple_partitions.py
   :linenos:
   :lines: 13-16
   :language: python
   :caption: repository.py

Finally, using these two functions, we create a :py:class:`PartitionSetDefinition <dagster.PartitionSetDefinition>` named ``stock_data_partitions_set``. We can register these partitions decorating a function that returns a list of partition set definitions with the :py:class:`@repository_partitions <dagster.repository_partitions>`


.. literalinclude:: ../../../../../examples/dagster_examples/stocks/simple_partitions.py
   :linenos:
   :lines: 19-39
   :language: python
   :caption: repository.py


Finally, we add a reference to this function in ``repository.yaml``, alongside our repository definition function reference.

.. code-block:: yaml

    repository:
        file: repository.py
        fn: define_partitions

Now, let's load dagit again and head to the playground. If we click on the preset button, we now also see our partition set. If we select it, we can see all the partitions we have and preview the config they generate.

.. thumbnail:: playground_partitions.png