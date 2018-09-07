.. image:: https://user-images.githubusercontent.com/28738937/44878798-b6e17e00-ac5c-11e8-8d25-2e47e5a53418.png
   :align: center

.. docs-include

============
Introduction
============

Dagster is an opinionated system and programming model for data pipelines. This process goes by many names -- ETL (extract-load-transform), ELT (extract-transform-load), model production, data integration, and so on -- but in essence they all describe the same activity: Performing a set of computations structured as a DAG (directed, acyclic graph) that end up producing data assets, whether those assets be tables, files, machine-learning models, etc.

There are a few tools in this repo

This repo has a few primary components:

- **Dagster**: The core programming model and abstraction stack; a stateless single-node and -process execution engine; and a CLI tool for driving that engine.
* **Dagit**: Dagit is a rich viewer for Dagster assets.
* **Dagster GE**: A Dagster integration with Great Expectations. (see https://github.com/great-expectations/great_expectations)

-------------------
Opinions and Values
-------------------

As noted above Dagster has a point of view and values regarding how data pipelines should be built and structured. We list them in no particular order:

* **Functional Data Pipelines**: We believe that data pipelines should be organized as DAGs of functional, idempotent computations. These computations injest input, do computation, and produce output, either with no side effects or well-known, un-externalized side effects. Given the same inputs and configuration, the computation should always produce the same output. These computations should also be parameterizable, so that they can execute in different environments. See https://bit.ly/2LxDgnr for an excellent overview of functional programing in batch computations.
* **Self-describing**: Pipelines should be self-describing with rich metadata and types. Users should be able to approach a pipeline, and use tooling to inspect the pipelines for their structure and capabilities. This metadata should be co-located with actual code of the pipeline. Documentation and code is delivered as a single artifact.
* **Compute-agnostic**: Dagster has opinions about the structure and best practices of data pipelines. It has no opinions about what libraries and engines use to do actual compute. The core computation within a dagster pipeline is user-specified code, meaning that it could be anything: Pandas, Spark, SQL computations on a data warehouse, vanilla python, or any combination therein.
* **Testable by design and by default**: Testing data pipelines is notoriously difficult. Because it is so difficult it is often never done, or done poorly. Dagster pipelines are designed to be tested. They have explicit support for pipeline authors to manage and maintain multiple operating environments -- for example, unit testing, integration testing, and production environments, among others. In addition dagster can execute arbitrary subsets and nodes of the pipeline, critical testability. (This capability happens to be useful in operational contexts as well).
* **First-class data quality tests**: Testing code is important in data pipelines, but it is not sufficient. Data quality tests -- run during every meaningful stage of production -- are critical to reduce the maintenance burden of data pipelines. Pipeline authors generally do not have control of their input data, and make many implicit assumptions about that data. The data formats can also change over time. In order to control this entropy, Dagster encourages users to computationally verify assumptions (known as expectations) about the data as part of the piplien process. This way if those assumptions are broken, the breakage can be reported quickly, easily, and with rich metadata and diagnostic information. These expectations can also serve as contracts between teams.  See https://bit.ly/2mxDS1R for a primer on pipeline tests for data quality.
* **Gradual, optional typing**: Dagster contains a type system to describe the values flowing through the pipeline. This allows nodes in a pipeline know if they are compatible before execution, and serves as value documentation and runtime error checking.


The core abstraction in Dagster is a *solid*, a logical unit of computation in a data pipeline. At its core a solid is a configurable function that accepts abstract inputs and produces outputs.

* Inputs:
* Outputs:
* Configuration:
* Transform:

Inputs are things.

* Name:
* Type:
* Expectations:

Outputs are things:

* Name
* Type
* Expectations

Solids are group together in *pipelines*. Pipelines are comprised of:

* Solids
* Dependencies
* Context Definitions



Solid formally separates the notion of inputs, outputs, the core transform. The core goal of this is cleanly and clearly separate the domain logic of each transform and its operational environments. This allows solids or pipelines of solids to easily be executable in a number of environments: unit-testing, local development, integration tests, CI/CD, staging environments, production environments, and so on and so forth.

Alongside with the core abstraction, Dagster provides helpers to create Solids that operate on Pandas dataframes and SQL databases.

Example
-------



.. code-block:: python


  import pandas as pd
  import dagster.core
  from dagster.core.definitions import (
      InputDefinition,
      OutputDefinition
  )
  from dagster.core.decorators import (
      solid,
  )

  # Solids can be created by annotating transform function with
  # a decorator
  @solid(
      # Solid inputs define arguments passed to transform function
      inputs=[
          InputDefinition(
              name='num',

          )
      ],
      # Solid output determines what solid should return.
      output=OutputDefinition(materializations=[
          dataframe_to_csv_materialization,
      ])
  )
  def sum_solid(info, num):
      sum_df = num.copy()
      # Here we add a new column to dataframe to sum up num1 and
      # num2 columns
      sum_df['sum'] = sum_df['num1'] + sum_df['num2']
      return sum_df


  @solid(
      inputs=[
          InputDefinition(name="sum")
      ],
      output=OutputDefinition(materializations=[
          dataframe_to_csv_materialization,
      ])
  )
  def sum_sq_solid(info, sum):
      sum_sq = sum.copy()
      sum_sq['sum_sq'] = sum['sum']**2
      return sum_sq


  # After definining a solid, we are grouping them into a pipeline
  pipeline = dagster.core.pipeline(
      name='pandas_hello_world',
      solids=[
          sum_solid,
          sum_sq_solid,
      ],
  )

You might notice that there is no actual CSV file specified as inputs. This is because such parameters are passed in environment. This allows you to customize it in runtime. To run your solid, we'll pass that environment to the execution function.

.. code-block:: python

  pipeline_result = dagster.execute_pipeline(pipeline, environment)


We can simplify the above example by using built-in dagster pandas inputs and outputs.

.. code-block:: python

   # TODO updated example definition

We can specify in order to get artifacts for the results. We can materialize output from any solid, this can be useful to see if intermediate results make sense.

.. code-block:: python

   # TODO updated example config driving

Dagster CLI
===========

In addition to programmatic API, you can also use dagster CLI to run the pipelines. In that case the environment is specified through yaml configuration files.

The folder structure should be as follows.

.. code-block

  pipeline_project_name/
    pipelines.yml
    pipeline_module_1/
      env.yml
    pipeline_module_2/
      env.yml

Pipelines yml specify the pipelines that are present in current project. Env specifies environment for each particular pipeline.

.. code-block:: yaml

 # TODO pipelines file

.. code-block:: yaml

 # TODO example config file


.. code-block:: sh

# TODO example  CLI driving


Concepts
========

Transform
---------

This is core, user-defined transform that performs the logical data
computation. In this case the transform is ``hello_world_transform_fn``
and it is passed as parameter into the solid. It takes one or more
inputs and produces an output. All other concepts in a solid are the
metadata and structure that surround this core computation

Inputs
---------

For each argument to the transform function, there is one
``InputDefinition`` object. It has a name, which must match the
parameters to the transform function. The input definitions define a
name, a dependency for the input (what upstream solid produces its
value, see below) and a number of sources. An input definition must
specify at least a dependency or a source. The input can have any number
of sources.


Output
---------

The ``OutputDefinition`` represents the output of the transform
function.



Higher-level APIs
------------------

# TODO keep this section?

Execution
---------

These are useless without being able to execute them. In order to
execute a solid, you need to package it up into a pipeline.

.. code-block:: python

    pipeline = dagster.PipelineDefinition(name='hello_world', solids=[sum_solid])

Then you an execute it by providing an environment. You must provide
enough source data to create all the inputs necessary for the pipeline.

.. code-block:: python

    environment = config.Environment(
        sources={
          'sum' : {
            'num_df' : config.Source(name='CSV', args={'path': 'path/to/input.csv'})
          }
        }
    )

    pipeline_result = dagster.execute_pipeline(
        dagster.ExecutionContext(),
        pipeline,
        environment
    )

    print(pipeline_result.result_for_solid('sum').transformed_value)


Dependencies
------------

So far we have demonstrated a single stage pipeline, which is obviously
of limited value.

Imagine we wanted to add another stage which took the sum we produced
and squared that value. (Fancy!)

.. code-block:: python

    # TODO example dependencies

Note that input specifies that dependency. This means that the input
value passed to the transform can be generated by an upstream dependency
OR by an external source. This allows for the solid to be executable in
isolation or in the context of a pipeline.

.. code-block:: python

   # TODO example driving

The above executed both solids, even though one input was provided. The
input into sum\_sq\_solid was provided by the upstream result from the
output of sum\_solid.

You can also execute subsets of the pipeline. Given the above pipeline,
you could specify that you only want to specify the first solid:

.. code-block:: python

    # TODO example subdag execution



Expectations
------------

Expectations are another reason to introduce logical seams between data
computations. They are a way to perform data quality tests or
statistical process control on data pipelines.
