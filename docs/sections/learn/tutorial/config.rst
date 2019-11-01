Parametrizing solids with config
--------------------------------

Solids often depend in predictable ways on features of the external world or the pipeline in which
they're invoked. For example, consider an extended version of our csv-reading solid that implements
more of the options available in the underlying Python API:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/config_bad_1.py
   :lines: 6-26
   :linenos:
   :lineno-start: 6
   :emphasize-lines: 8-14
   :caption: config_bad_1.py

We obviously don't want to have to write a separate solid for each permutation of these parameters
that we use in our pipelines -- especially because, in more realistic cases like configuring a
Spark job or even parametrizing the ``read_csv`` function from a popular package like
`Pandas <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html#pandas.read_csv>`__,
we might have dozens or hundreds of parameters like these. 

But hoisting all of these parameters into the signature of the solid function as inputs isn't the
right answer either:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/config_bad_2.py
   :lines: 6-36
   :linenos:
   :lineno-start: 6
   :emphasize-lines: 5-11
   :caption: config_bad_2.py

Defaults are often sufficient for configuation values like these, and sets of parameters are often
reusable. And it's unlikely that values like this will be provided dynamically by the outputs of
other solids in a pipeline.

Inputs, on the other hand, will usually be provided by the outputs of other solids in a pipeline,
even though we might sometimes want to stub them using the config facility. 

For all these reasons, it's bad practice to mix configuration values like these with true input
values.

The solution is to define a config schema for our solid:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/config.py
   :linenos:
   :lines: 1-102
   :emphasize-lines: 15, 33-41, 87
   :caption: config.py

First, we pass the ``config`` argument to the :py:func:`@solid <dagster.solid>` decorator.
This tells Dagster to give our solid a config field structured as a dictionary, whose keys are the
keys of this argument, and the types of whose values are defined by the values of this argument 
(instances of :py:func:`Field <dagster.Field>`).

Then, we define one of these fields, ``escapechar``, to be a string, setting a default value,
making it optional, and setting a human-readable description.

Finally, inside the body of the solid function, we access the config value set by the
user using the ``solid_config`` field on the familiar
:py:class:`context <dagster.SystemComputeExecutionContext>` object. When Dagster executes our pipeline,
the framework will make validated config for each solid available on this object.

Let's see how all of this looks in dagit. As usual, run:

.. code-block:: console

   $ dagit -f config.py -n config_pipeline

.. thumbnail:: config_figure_one.png

As you may by now expect, Dagit provides a fully type-aware and schema-aware config editing
environment with a typeahead. The human-readable descriptions we provided on our config fields
appear in the config context minimap, as well as in typeahead tooltips and in the Explore pane
when clicking into the individual solid definition.

.. thumbnail:: config_figure_two.png

You can see that we've added a new section to the solid config. In addition to the ``inputs``
section, which we'll still use to set the ``csv_path`` input, we now have a ``config`` section,
where we can set values defined in the ``config`` argument to :py:func:`@solid <dagster.solid>`.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/config_env_bad.yaml
   :linenos:
   :language: YAML
   :caption: config_env_bad.yaml

Of course, this config won't give us the results we're expecting. The values in ``cereal.csv``
are comma-separated, not semicolon-separated, as they might be if this were a .csv from Europe,
where commas are frequently used in place of the decimal point.

We'll see later how we can use Dagster's facilities for automatic data quality checks to guard
against semantic issues like this, which won't be caught by the type system.
