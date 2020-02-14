Type-checking inputs
--------------------

Note that this section requires Python 3.

If you zoom in on the **Explore** tab in Dagit and click on one of our pipeline solids, you'll see
that its inputs and outputs are annotated with types.

.. thumbnail:: inputs_figure_four.png

By default, every untyped value in Dagster is assigned the catch-all type :py:class:`Any`. This means that
any errors in the config won't be surfaced until the pipeline is executed.

For example, when we execute our pipeline with this config, it'll fail at runtime:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/inputs_env_bad.yaml
   :language: YAML
   :linenos:
   :caption: inputs_env_bad.yaml

When we enter this mistyped config in Dagit and execute our pipeline, you'll see that an error
appears in the structured log viewer pane of the **Execute** tab:

.. thumbnail:: inputs_figure_five.png

Click on "View Full Message" or on the red dot on the execution step that failed and a detailed
stacktrace will pop up.

.. thumbnail:: inputs_figure_six.png

It would be better if we could catch this error earlier, when we specify the config. So let's
make the inputs typed.

A user can apply types to inputs and outputs using Python 3's type annotation syntax. In this case,
we just want to type the input as the built-in ``str``.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/inputs_typed.py
   :lines: 6-12
   :emphasize-lines: 2
   :linenos:
   :lineno-start: 6
   :caption: inputs_typed.py
   :language: python

By using typed input instead we can catch this error prior to execution, and reduce the surface
area we need to test and guard against in user code.

.. thumbnail:: inputs_figure_seven.png
