Materializations
----------------

.. toctree::
  :maxdepth: 1
  :hidden:

Steps in a data pipeline often produce persistent artifacts, for instance, graphs or tables
describing the result of some computation. Typically these artifacts are saved to disk (or to
cloud storage) with a `name <https://xkcd.com/1459/>`__ that has something to do with their origin.
But it can be hard to organize and cross-reference artifacts produced by many different runs of a
pipeline, or to identify all of the files that might have been created by some pipeline's logic.

Dagster solids can describe their persistent artifacts to the system by yielding
:py:class:`Materialization <dagster.Materialization>` events. Like
:py:class:`TypeCheck <dagster.TypeCheck>` and :py:class:`ExpectationResult <dagster.ExpectationResult>`,
materializations are side-channels for metadata -- they don't get passed to downstream solids and
they aren't used to define the data dependencies that structure a pipeline's DAG.

Suppose that we rewrite our ``sort_calories`` solid so that it saves the newly sorted data frame to
disk.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/materializations.py
   :lines: 23-46
   :linenos:
   :lineno-start: 23
   :caption: materializations.py
   :language: python

We've taken the basic precaution of ensuring that the saved csv file has a different filename for
each run of the pipeline. But there's no way for Dagit to know about this persistent artifact.
So we'll add the following lines:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/materializations.py
   :lines: 23-56
   :linenos:
   :lineno-start: 23
   :emphasize-lines: 24-33
   :caption: materializations.py
   :language: python

Note that we've had to add the last line, yielding an :py:class:`Output <dagster.Output>`. Until
now, all of our solids have relied on Dagster's implicit conversion of the return value of a solid's
compute function into its output. When we explicitly yield other types of events from solid logic,
we need to also explicitly yield the output so that the framework can recognize them.

Now, if we run this pipeline in Dagit:

.. thumbnail:: materializations.png


Configurably materializing custom data types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Data types can also be configured so that outputs materialize themselves, obviating the need to
explicitly yield a :py:class:`Materialization <dagster.Materialization>` from solid logic. Dagster
calls this facility the
:py:func:`@output_materialization_config <dagster.output_materialization_config>`.

Suppose we would like to be able to configure outputs of our toy custom type, the
``SimpleDataFrame``, to be automatically materialized to disk as both as a pickle and as a .csv.
(This is a reasonable idea, since .csv files are human-readable and manipulable by a wide variety
of third party tools, while pickle is a binary format.)

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/output_materialization.py
   :lines: 28-61
   :linenos:
   :lineno-start: 28
   :caption: output_materialization.py
   :language: python

We set the output materialization config on the type:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/output_materialization.py
   :lines: 64-71
   :linenos:
   :lineno-start: 64
   :emphasize-lines: 5
   :caption: output_materialization.py
   :language: python

Now we can tell Dagster to materialize intermediate outputs of this type by providing config:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/output_materialization.yaml
   :linenos:
   :emphasize-lines: 6-10
   :caption: output_materialization.yaml
   :language: YAML

When we run this pipeline, we'll see that materializations are yielded (and visible in the
structured logs in Dagit), and that files are created on disk (with the semicolon separator we
specified).

.. thumbnail:: output_materializations.png
