Multiple Outputs
----------------

So far all of our examples have been solids that have a single output. But
solids can have an arbitrary number of outputs. Downstream solids can 
depend on any number of these outputs. Additionally, these outputs do
not *necessarily* have to be fired, therefore unlocking the ability for
downstream solids to be invoked conditionally based on something that
happened during the computation.

``MultipleResults`` Class
^^^^^^^^^^^^^^^^^^^^^^^^^

Here we present an example of a solid that has multiple outputs within a pipeline:

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/multiple_outputs.py
   :linenos:
   :caption: multiple_outputs.py
   :lines: 53-67, 26-34, 67-82

This can be visualized in dagit:

.. image:: multiple_results_figure_one.png


Notice how ``return_dict_results`` has two outputs. For the first time
we have provided the name argument to an :py:class:`OutputDefinition <dagster.OutputDefinition>`.
(The name of an output defaults to ``'result'``, as it does for a
:py:class:`DependencyDefinition <dagster.DependencyDefinition>`) Output names must be unique
and each result returned by a solid's transform function must have a name that corresponds to
one of these outputs.

So from ``return_dict_results`` we used :py:class:`MultipleResults <dagster.MultipleResults>`
to return all outputs from this transform.

Just as this tutorial gives us the first example of a named
:py:class:`OutputDefinition <dagster.OutputDefinition>`, this is also the first time that we've
seen a named :py:class:`DependencyDefinition <dagster.DependencyDefinition>`. Recall that dependencies
point to a particular **output** of a solid, rather than to the solid itself. 

With this we can run the pipeline (condensed here for brevity):

.. code-block:: console

    $ dagster pipeline execute -f multiple_outputs.py \
    -n define_multiple_outputs_step_one_pipeline

    ... log spew
    2019-04-05 22:23:37 - dagster - INFO -
            orig_message = "Solid return_dict_results emitted output \"out_one\" value 23"
            ...
        solid_definition = "return_dict_results"
    ...
    2019-04-05 22:23:37 - dagster - INFO -
            orig_message = "Solid return_dict_results emitted output \"out_two\" value 45"
            ...
        solid_definition = "return_dict_results"
    ... more log spew

Iterator of ``Result``
^^^^^^^^^^^^^^^^^^^^^^

The :py:class:`MultipleResults <dagster.MultipleResults>` class is not the only way
to return multiple results from a solid transform function. You can also yield
multiple instances of the ``Result`` object. (Note: this is actually the core
specification of the transform function: all other forms are implemented in terms of
the iterator form.)

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/multiple_outputs.py
   :linenos:
   :caption: multiple_outputs.py
   :lines: 15-24

Conditional Outputs
^^^^^^^^^^^^^^^^^^^

Multiple outputs are the mechanism by which we implement branching or conditional execution. Let's
modify the first solid above to conditionally emit one output or the other based on config
and then execute that pipeline.

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/multiple_outputs.py
    :linenos:
    :caption: multiple_outputs.py
    :lines: 36-52,86-97

You must create a config file

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/conditional_outputs.yml
    :linenos:
    :caption: conditional_outputs.yml

And then run it.

.. code-block:: console

    $ dagster pipeline execute -f multiple_outputs.py \
    -n define_multiple_outputs_step_three_pipeline \
    -e conditional_outputs.yml

    ... log spew
    2019-04-05 22:29:31 - dagster - INFO -
            orig_message = "Solid conditional emitted output \"out_two\" value 45"
            ...

    2019-04-05 22:29:31 - dagster - INFO -
            orig_message = "Solid conditional did not fire outputs {'out_one'}"
            ...
    ... log spew

Note that we are configuring this solid to *only* emit ``out_two`` which will end up
only triggering ``log_num_squared``. The solid ``log_num`` will never be executed.

Next, let's look at writing :doc:`Reusable Solids <reusable_solids>` so we can avoid duplicating
common data pipeline work.
