Dagster
=======

.. docs-include

Dagster is a library that helps you organize, run and test your data processing pipelines. Instead of writing ad-hoc data processing script, Dagster encourages separating data input, data processing and data output, as well as separating your processing in several steps.


The core abstraction in Dagster is a **Solid**, a logical unit of computation in a data pipeline. At its core a Solid is a coarse-grained pure function. It takes multiple inputs, performs a computation, produces an output. Inputs can either be received from outputs from upstream solids in the pipeline or external sources (e.g. files). Likewise, outputs from the transform can either be flowed to downstream solids or materialized (e.g. to a file in an object store) so that it can be inspected or accessed by an external system.

Solid formally separates the notion of inputs, outputs, the core transform. The core goal of this is cleanly and clearly separate the domain logic of each transform and its operational environments. This  allows solids or pipelines of solids to easily be executable in a number of environments: unit-testing, local development, integration tests, CI/CD, staging environments, production environments, and so on and so forth.

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
      source,
      materialization,
  )

  # Sources define *how* to get data. Let's define a source that
  # reads a CSV file and returns a pandas dataframe
  @source(
      # Name of the source
      name="CSV",
      # What arguments it should get from environment
      argument_def_dict={'path': ArgumentDefinition(dagster.core.types.Path) })
  )
  def csv_to_dataframe_source(path):
      return pd.read_csv(path)

  # Materializations define how to convert a transform result
  # into an artifact, for example a file. Let's define one that
  # outputs a CSV file. Note that materializations that are
  # defined for solids are optional, and are only triggered if
  # environment says so
  @materialization(
      # Name of the materialization
      name="CSV",
      # What arguments it should get from environment
      argument_def_dict={'path': ArgumentDefinition(dagster.core.types.Path) })
  )
  def dataframe_to_csv_materialization(data, path):
      data.to_csv(path)

  # Solids can be created by annotating transform function with
  # a decorator
  @solid(
      # Solid inputs define arguments passed to transform function
      inputs=[
          InputDefinition(
              name='num',
              # Inputs can have sources. While inputs define
              # *what* transform should receive, sources define
              # *how* this data should be retrieved
              sources=[csv_to_dataframe_source]
          )
      ],
      # Solid output determines what solid should return.
      output=OutputDefinition(materializations=[
          dataframe_to_csv_materialization,
      ])
  )
  def sum_solid(num):
      sum_df = num.copy()
      # Here we add a new column to dataframe to sum up num1 and
      # num2 columns
      sum_df['sum'] = sum_df['num1'] + sum_df['num2']
      return sum_df


  @solid(
      inputs=[
          # This solid is a *dependency*. It depends on a result
          # of previous solid as one of the inputs
          InputDefinition(name="sum", depends_on=sum_solid)
      ],
      output=OutputDefinition(materializations=[
          dataframe_to_csv_materialization,
      ])
  )
  def sum_sq_solid(sum):
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

  environment = config.Environment(
    sources={
      'sum_solid' : {
        'num' : config.Source(name='CSV', args={'path': 'path/to/num.csv'})
      }
    }
  )

  pipeline_result = dagster.execute_pipeline(
      dagster.ExecutionContext(),
      pipeline,
      environment
  )


We can simplify the above example by using built-in dagster pandas inputs and outputs.

.. code-block:: python

  import dagster.core
  from dagster import config
  from dagster.core.decorators import solid, with_context
  import dagster.pandas_kernel as dagster_pd

  @solid(
      inputs=[
          # We are using a pre-made input that should be a dataframe
          dagster_pd.dataframe_input(
              'num',
              sources=[
                  # A built-in pandas csv-dataframe source reads
                  # a CSV file andproduces a pandas dataframe
                  dagster_pd.csv_dataframe_source()
              ]
          )
      ],
      # This built-in dataframe knows how to materialize dataframes
      # out of the box
      output=dagster_pd.dataframe_output()
  )
  def sum_solid(num):
      sum_df = num.copy()
      # Here we add a new column to dataframe to sum up num1 and num2 columns
      sum_df['sum'] = sum_df['num1'] + sum_df['num2']
      return sum_df


  @solid(
      inputs=[
          # This input will check that the source solid outputs a
          # dataframe
          dagster_pd.dataframe_dependency(name="sum", solid=sum_solid)
      ],
      output=dagster_pd.dataframe_output()
  )
  def sum_sq_solid(sum):
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

We can specify in order to get artifacts for the results. We can materialize output from any solid, this can be useful to see if intermediate results make sense.

.. code-block:: python

    environment = config.Environment(
        sources={
          'sum' : {
            'num' : config.Source(name='CSV', args={'path': 'path/to/num.csv'})
          }
        }
    )

  materializations = [
      config.Materialization(
          solid='sum',
          name='CSV',
          args={'path': 'path/to/output.csv'},
      ),
      config.Materialization(
          solid='sum_sq',
          name='CSV',
          args={'path': 'path/to/output.csv'},
      )
  ]

  pipeline_result = dagster.execute_pipeline(
      dagster.ExecutionContext(),
      pipeline,
      environment,
      materializations,
  )


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

  pipelines:
    - module: pipeline_project_name.pipeline_module_1.pipeline
      fn: define_pipeline
    - module: pipeline_project_name.pipeline_module_2.pipeline
      fn: define_pipeline


.. code-block:: yaml

  environment:
    inputs:
      - input_name: num
        source: CSV
        args:
          path: "input/num.csv"

  materializations:
    - solid: sum
      type: CSV
      args:
        path: 'sum.csv'
    - solid: sum_sq
      type: CSV
      args:
        path: 'sum_sq.csv'


.. code-block:: sh

    pip install dagster
    # List pipelines
    dagster pipeline list
    # Print info about pipeline solids
    dagster pipeline print pipeline1
    # Execute pipeline
    dagster pipeline execute pipeline1
    # Execute pipeline from intermediate step
    dagster pipeline execute pipeline1 --from-solid SOLID_NAME


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

Sources
^^^^^^^

Sources are the the way that one can create an input to a transform from
external resources. A source is a function that takes a set of arguments
and produces a value that is passed to the transform for processing. In
this case, a CSV file is the only source type. One can imagine adding
other source types to create pandas dataframes for Json, Parquet, and so
forth. End users will typically rely on pre-existing libraries to
specify sources.

Sources also declare what arguments they expect. These are inspectable
and could be used to render information for web or command line tools,
to verify the validity of confie files, and other tooling contexts. The
framework verifies when solids or pipelines of solids are executed, that
the arguments abide by the declaration. These arguments are then sent to
the source function in the ``arg_dict`` parameter.

Output
---------

The ``OutputDefinition`` represents the output of the transform
function.

Materializations
^^^^^^^^^^^^^^^^

Materializations are the other end of source. This specifies the way the
output of a transform can be materialized. In this example which uses
pandas dataframes, the sources and materializations will be symmetrical.
In the above example we specified a single materialization, a CSV. One
could expand this to include JSON, Parquet, or other materialiations as
appropriate.

However in other contexts that might be true. Take solids that operate
on SQL-based data warehouses or similar. The core transform would be the
SQL command, but the materialization would specify a
``CREATE TABLE AS``, a table append, or a partition creation, as
examples.

Higher-level APIs
------------------

These definitions will typically be composed with higher level APIs. For
example, the above solid could be expressed using APIs provided by the
pandas kernel. (Note: the "kernel" terminology is not settled)

.. code-block:: python

    import dagster
    import dagster.pandas_kernel as dagster_pd

    def sum_transform(num_df):
        num_df['sum'] = num_df['num1'] + num_df['num2']
        return num_df

    sum_solid = SolidDefinition(
        name='sum',
        description='This computes the sum of two numbers.'
        inputs=[dagster_pd.dataframe_csv_input(name='num_df')],
        transform_fn=sum_transform,
        output=dagster_pd.dataframe_output(),
    )

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

    print(pipeline_result.result_named('sum').transformed_value)

Execute pipeline does a purely in-memory transform, materializing
nothing. This is useful in testing and CI/CD contexts.

Materialization
----------------

In order to produce outputs that are available to external systems, you
must materialize them. In this case, that means producing files. In
addition to your environment, you must specify your materializations.

.. code-block:: python

    materializations = [
        config.Materialization(
            solid='sum',
            name='CSV',
            args={'path': 'path/to/output.csv'},
        )
    ]

    dagster.execute_pipeline(
        dagster.ExecutionContext(),
        pipeline,
        environment,
        materializations,
    )

Dependencies
------------

So far we have demonstrated a single stage pipeline, which is obviously
of limited value.

Imagine we wanted to add another stage which took the sum we produced
and squared that value. (Fancy!)

.. code-block:: python

    def sum_sq_transform(sum_df):
        sum_df['sum_sq'] = sum_df['sum'] * sum_df['sum']
        return sum_df

    # Fully expanded InputDefintion. Should be wrapped in higher-level
    # but this is here for explanatory code.
    sum_sq_input = InputDefinition(
        name='sum_df',
        sources=[
            SourceDefinition(
                source_type='CSV',
                argument_def_dict={'path': ArgumentDefinition(types.Path)},
                source_fn=lambda arg_dict: pd.read_csv(arg_dict['path']),
            ),
        ],
        depends_on=sum_solid,
    )

    sum_sq_solid = SolidDefinition(
        name='sum_sq',
        inputs=[sum_sq_input],
        transform_fn=sum_sq_transform,
        output=dagster_pd.dataframe_output(),
    )

Note that input specifies that dependency. This means that the input
value passed to the transform can be generated by an upstream dependency
OR by an external source. This allows for the solid to be executable in
isolation or in the context of a pipeline.

.. code-block:: python

    pipeline = dagster.PipelineDefinition(solids=[sum_solid, sum_sq_solid])

    environment = config.Environment(
        sources={
          'sum' : {
              'num_df' : config.Source(name='CSV', args={'path': 'path/to/num.csv'})
          }
        }
    )

    pipeline_result = dagster.execute_pipeline(
        dagster.ExecutionContext(),
        pipeline,
        environment
    )

The above executed both solids, even though one input was provided. The
input into sum\_sq\_solid was provided by the upstream result from the
output of sum\_solid.

You can also execute subsets of the pipeline. Given the above pipeline,
you could specify that you only want to specify the first solid:

.. code-block:: python

    environment = config.Environment(
        sources={
            'num_df' : config.Source(name='CSV', args={'path': 'path/to/num.csv'})
        }
    )

    pipeline_result = dagster.execute_pipeline(
        dagster.ExecutionContext(),
        pipeline,
        environment,
        through=['sum'],
    )

Or you could specify just the second solid. In that case the environment
would have to be changed.

.. code-block:: python

    environment = config.Environment(
        sources={
          'sum_sq' : { 
              'sum_df' : config.Source(name='CSV', args={'path': 'path/to/sum.csv'})
          }
        }
    )

    pipeline_result = dagster.execute_pipeline(
        dagster.ExecutionContext(),
        pipeline,
        environment,
        from=['sum_sq'],
        through=['sum_sq'],
    )

Expectations
------------

Expectations are another reason to introduce logical seams between data
computations. They are a way to perform data quality tests or
statistical process control on data pipelines.

TODO: Complete this section when the APIs and functionality are more
fleshed out.
