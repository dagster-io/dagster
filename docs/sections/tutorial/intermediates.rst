.. _tutorial-intermediates:

Intermediates
-------------

.. toctree::
  :maxdepth: 1
  :hidden:

We've already seen how solids can describe their persistent artifacts to the system using
`materializations <materializations.html>`_.

Dagster also has a facility for automatically materializing the intermediate values that actually
pass between solids.

This can be very useful for debugging, when you want to inspect the value output by a solid and
ensure that it is as you expect; for audit, when you want to understand how a particular
downstream output was created; and for re-executing downstream solids with cached results from
expensive upstream computations.

To turn intermediate storage on, just set another key in the pipeline config:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/intermediates.yaml
   :linenos:
   :emphasize-lines: 6-7
   :caption: intermediates.yaml
   :language: YAML

When you execute the pipeline using this config, you'll see new structured entries in the Dagit
log viewer indicating that intermediates have been stored on the filesystem.

.. thumbnail:: intermediates.png

Intermediate storage for types that cannot be pickled
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
By default, Dagster will try to pickle intermediate values to store them on the filesystem. Some
custom data types cannot be pickled (for instance, a Spark RDD), so you will need to tell Dagster
how to serialize them.

Our toy ``LessSimpleDataFrame`` is, of course, pickleable, but supposing it was not, let's set a
custom :py:class:`SerializationStrategy <dagster.SerializationStrategy>` on it to tell Dagster how
to store intermediates of this type.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/serialization_strategy.py
   :lines: 16-39
   :linenos:
   :lineno-start: 16
   :caption: serialization_strategy.py
   :language: python

Now, when we set the ``storage`` key in pipeline config and run this pipeline, we'll see that our
intermediate is automatically persisted as a human-readable .csv:

.. thumbnail:: serialization_strategy.png

Reexecution
^^^^^^^^^^^

Once intermediates are being stored, Dagit makes it possible to individually execute solids
whose outputs are satisfied by previously materialized intermediates.

Click on the ``sort_by_calories.compute`` execution step, and you'll see the option appear to
reexecute only this step, using the automatically materialized intermediate output of the
previous solid.

.. thumbnail:: reexecution.png

.. thumbnail:: reexecution_results.png

Reexecuting individual solids can be very helpful while you're writing solids, or while you're
actively debugging them.

You can also manually specify intermediates from previous runs as inputs to solids. Recall the
syntax we used to set input values using the config system:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/inputs_env.yaml
   :language: YAML
   :linenos:
   :caption: inputs_env.yaml

Instead of setting the key ``value`` (i.e., providing a ), we can also set ``pickle``, as follows:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/reexecution_env.yaml
   :language: YAML
   :linenos:
   :caption: reexecution_env.yaml

(Of course, you'll need to use the path to an intermediate that is actually present on your
filesystem.)

If you directly substitute this config into Dagit, you'll see an error, because the system still
expects the input to ``sort_by_calories`` to be satisfied by the output from ``read_csv``.

.. thumbnail:: reexecution_errors.png

To make this config valid, we'll need to tell Dagit to execute only a subset of the pipeline --
just the ``sort_by_calories`` solid. Click on the subset-selector button in the top left of
the playground, to the left of the Mode selector (which, when no subset has been specified, will
read "*"):

.. thumbnail:: subset_selection.png

Hit "Apply", and this config will now pass validation, and the individual solid can be reexecuted:

.. thumbnail:: subset_config.png

This facility is especially valuable during test, since it allows you to validate newly written
solids against values generated during previous runs of a known good pipeline.
