Multiple and conditional outputs
--------------------------------

Solids can have arbitrarily many outputs, and downstream solids can depend on any number of these.

What's more, outputs don't necessarily have to be yielded by solids, which lets us write pipelines
where some solids conditionally execute based on the presence of an upstream output.

Suppose we're interested in splitting hot and cold cereals into separate datasets and processing
them separately, based on config.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/multiple_outputs.py
   :linenos:
   :lineno-start: 33
   :caption: multiple_outputs.py
   :lines: 33-58
   :emphasize-lines: 7-12, 21, 26
   :language: python

Solids that yield multiple outputs must declare, and name, their outputs (passing ``output_defs``
to the :py:func:`@solid <dagster.solid>` decorator). Output names must be unique and each
:py:func:`Output <dagster.Output>` yielded by a solid's compute function must have a name that
corresponds to one of these declared outputs.

We'll define two downstream solids and hook them up to the multiple outputs from ``split_cereals``.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/multiple_outputs.py
   :linenos:
   :lineno-start: 56
   :caption: multiple_outputs.py
   :lines: 56-80
   :emphasize-lines: 23-25
   :language: python

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
right hand pane:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/multiple_outputs.yaml
   :linenos:
   :caption: multiple_outputs.yaml
   :language: YAML

.. thumbnail:: conditional_outputs.png
