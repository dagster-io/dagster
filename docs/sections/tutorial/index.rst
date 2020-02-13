Hello, cereal!
==============

.. toctree::
  :maxdepth: 1
  :includehidden:
  :hidden:

  self
  hello_solid
  hello_pipeline
  execute_pipeline
  testing
  hello_dag
  inputs
  dagit_config_editor
  typed_inputs
  config
  types
  metadata
  multiple_outputs
  reusable
  composite_solids
  materializations
  intermediates
  resources
  modes
  presets
  repos
  scheduler

If you're new to Dagster, we recommend working through this tutorial to become
familiar with Dagster's feature set and tooling, using small examples that are
intended to be illustrative of real data problems.

We'll build these examples around a simple but scary .csv dataset,
``cereal.csv``, which contains nutritional facts about 80 breakfast cereals.
You can find this dataset on
`Github <https://raw.githubusercontent.com/dagster-io/dagster/master/examples/dagster_examples/intro_tutorial/cereal.csv>`_.
Or, if you've cloned the dagster git repository, you'll find this dataset at
``dagster/examples/dagster_examples/intro_tutorial/cereal.csv``.

To get the flavor of this dataset, let's look at the header and the first five rows:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/cereal.csv
   :linenos:
   :lines: 1-6
   :caption: cereals.csv
   :language: text

You can find all of the tutorial code checked into the dagster repository at
``dagster/examples/dagster_examples/intro_tutorial``.
