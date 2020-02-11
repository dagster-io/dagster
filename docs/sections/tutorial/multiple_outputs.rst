Multiple and conditional outputs
--------------------------------

Solids can have arbitrarily many outputs, and downstream solids can depends on any number of these.

What's more, outputs don't necessarily have to be yielded by solids, which lets us write pipelines
where some solids conditionally execute based on the presence of an upstream output.

Suppose we're interested in splitting hot and cold cereals into separate datasets and processing
them separately, based on config.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/multiple_outputs.py
   :linenos:
   :lineno-start: 31
   :caption: multiple_outputs.py
   :lines: 31-55
   :emphasize-lines: 6-13, 20, 25

Solids that yield multiple outputs must declare, and name, their outputs (passing ``output_defs``
to the :py:func:`@solid <dagster.solid>` decorator). Output names must be unique and each
:py:func:`Output <dagster.Output>` yielded by a solid's compute function must have a name that
corresponds to one of these declared outputs.

We'll define two downstream solids and hook them up to the multiple outputs from ``split_cereals``.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/multiple_outputs.py
   :linenos:
   :lineno-start: 58
   :caption: multiple_outputs.py
   :lines: 58-82
   :emphasize-lines: 23-25

As usual, we can visualize this in Dagit:

.. thumbnail:: multiple_outputs.png

Notice that the logical DAG corresponding to the pipeline definition includes both dependencies --
we won't know about the conditionality in the pipeline until runtime, when one of the outputs
is not yielded by ``split_cereal``.

.. thumbnail:: multiple_outputs_zoom.png

Zooming in, Dagit shows us the details of the multiple outputs from ``split_cereals`` and their
downstream dependencies.

When we execute this pipeline with the following config, we'll see that the cold cereals output is
omitted and that the execution step corresponding to the downstream solid is marked skipped in the
right hand pane.

.. thumbnail:: conditional_outputs.png


Reusable solids
---------------

Solids are intended to abstract chunks of business logic, but abstractions aren't very meaningful
unless they can be reused. 

Our conditional outputs pipeline included a lot of repeated code -- ``sort_hot_cereals_by_calories``
and ``sort_cold_cereals_by_calories``, for instance. In general, it's preferable to build pipelines
out of a relatively restricted set of well-tested library solids, using config liberally to
parametrize them. (You'll certainly have your own version of ``read_csv``, for instance, and
Dagster includes libraries like ``dagster_aws`` and ``dagster_spark`` to wrap and abstract
interfaces with common third party tools.)

Let's replace ``sort_hot_cereals_by_calories`` and ``sort_cold_cereals_by_calories`` by two aliases
of the same library solid:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/reusable_solids.py
   :linenos:
   :lineno-start: 59
   :lines: 59-76
   :emphasize-lines: 15-16
   :caption: reusable_solids.py

You'll see that Dagit distinguishes between the two invocations of the single library solid and the
solid's definition. The invocation is named and bound via a dependency graph to other invocations
of other solids. The definition is the generic, resuable piece of logic that is invoked many times
within this pipeline.

.. thumbnail:: reusable_solids.png

Configuring solids also uses the aliases, as in the following YAML:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/reusable_solids.yaml
   :linenos:
   :emphasize-lines: 6, 8
   :caption: reusable_solids.yaml
