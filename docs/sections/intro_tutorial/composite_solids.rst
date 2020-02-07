Composing solids
----------------

Abstracting business logic into reusable, configurable solids is one important step towards making
data applications like other software applications. The other basic facility that we expect from
software in other domains is composability -- the ability to combine building blocks into larger
functional units.

Composite solids can be used to organize and refactor large or complicated pipelines, abstracting
away complexity, as well as to wrap reusable general-purpose solids together with domain-specific
logic.

As an example, let's compose two instances of a complex, general-purpose ``read_csv`` solid along
with some domain-specific logic for the specific purpose of joining our cereal dataset with a
lookup table providing human-readable names for the cereal manufacturers.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/composite_solids.py
   :linenos:
   :lines: 126-130
   :lineno-start: 126
   :caption: composite_solids.py

Defining a composite solid is similar to defining a pipeline, except that we use the
:py:func:`@composite_solid <dagster.composite_solid>` decorator instead of
:py:func:`@pipeline <dagster.pipeline>`.

Dagit has sophisticated facilities for visualizing composite solids:

.. thumbnail:: composite_solids.png

All of the complexity of the composite solid is hidden by default, but we can expand it at will by
clicking into the solid (or on the "Expand" button in the right-hand pane):

.. thumbnail:: composite_solids_expanded.png

Note the line indicating that the output of ``join_cereal`` is returned as the output of the
composite solid as a whole.

Config for the individual solids making up the composite is nested, as follows:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/composite_solids.yaml
   :linenos:
   :language: YAML
   :caption: composite_solids.yaml
   :emphasize-lines: 1-3

When we execute this pipeline, Dagit includes information about the nesting of individual execution
steps within the composite:

.. thumbnail:: composite_solids_expanded.png
