Writing a partition ready pipeline
==================================


To get a clearer understanding of how partitioning works in Dagster, we'll work
 through an example pipeline that calculates the total volume traded for a given stock. Volume is defined as the number of shares traded in a given time period.

We'll use the `Financial Modeling Prep API <https://financialmodelingprep.com/developer/docs>`_ as our data source. The API has an endpoint that can give us historical price data for a given stock over a time range:

.. code-block:: console

    https://financialmodelingprep.com/api/v3/historical-price-full/AAPL?from=2019-01-01&to=2019-01-31

If we query this URL, we'll recieve a JSON response containing historical data (partitioned by day) for the stock we queried for - in this case AAPL. In the historical data, notice how we have volume traded information.

.. code-block:: JSON

    {
      "symbol" : "AAPL",
      "historical" : [ {
        "date" : "2019-01-02",
        "open" : 154.89,
        "high" : 158.85,
        "low" : 154.23,
        "close" : 157.92,
        "adjClose" : 156.05,
        "volume" : 3.70397E7,
        "unadjustedVolume" : 3.70397E7,
        "change" : -3.03,
        "changePercent" : -1.956,
        "vwap" : 157.0,
        "label" : "January 02, 19",
        "changeOverTime" : -0.01956
      }, {
        "date" : "2019-01-03",
        "open" : 143.98,
        "high" : 145.72,
        "low" : 142.0,
        "close" : 142.19,
        "adjClose" : 140.51,
        "volume" : 9.13122E7,
        "unadjustedVolume" : 9.13122E7,
        "change" : 1.79,
        "etc.": "..."
      }]
    }

Let's write our first pipeline to query this URL and calculate the total volume traded during January 2019.

Before we begin, let's set up a project structure to organize our code:

.. code-block:: console

    partition-tutorial
    ├── repository.py
    └── repository.yaml

And point our `repository.yaml` to our repository:

repository.yaml:

.. code-block:: YAML

    repository:
        file: repository.py
        fn: define_repo

To make a pipline partitionable, we'll use solid config. This will allow us to simply change the config to run the pipeline for different partitions. If you haven't explored the dagster config system, take a look at the `tutorial <../../../tutorial/config.html>`_.

Our first solid will take the stock ticker symbol as config, and query the API to return the volume traded from Jan 01 - Jan 31 2019. We pass the json response to the downstream solid.


.. literalinclude:: ../../../../../examples/dagster_examples/stocks/pipelines_stock.py
   :linenos:
   :lines: 5-20
   :language: python
   :caption: repository.py
   :emphasize-lines: 4-16

Our second solid will take the json response and total the volume amounts over all the days:

.. literalinclude:: ../../../../../examples/dagster_examples/stocks/pipelines_stock.py
   :linenos:
   :lines: 23-32
   :language: python
   :caption: repository.py


Great! Now we can wrap this up in a pipeline and repository, then open the repository in dagit to execute the pipeline.

.. literalinclude:: ../../../../../examples/dagster_examples/stocks/pipelines_stock.py
   :linenos:
   :lines: 23-32
   :language: python
   :caption: repository.py

.. code-block:: python

    from dagster import pipeline, RepositoryDefinition

    @pipeline
    def compute_total_stock_volume():
        sum_volume(query_historical_stock_data())

    def define_repo():
        return RepositoryDefinition(
            name='partitioning-tutorial', pipeline_defs=[compute_total_stock_volume]
        )

.. thumbnail:: pipeline.png

We can configure the pipeline run in the playground to calculate the total volume for Apple shares:

.. code-block:: YAML

    solids:
        query_historical_stock_data:
            config:
                symbol: "AAPL"

.. thumbnail:: config_1.png

Now if we wanted to calculate the total volume for several different stocks, it's easy to simply change our configuration to run for a different ticker:

.. code-block:: YAML

    solids:
        query_historical_stock_data:
            config:
                symbol: "GOOG"