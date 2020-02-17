Using the Dagit config editor
-----------------------------

Dagit provides a powerful, schema-aware, typeahead-enabled config editor to enable rapid
experimentation with and debugging of parameterized pipeline executions. As always, run:

.. code-block:: console

   $ dagit -f inputs.py -n inputs_pipeline

Notice the error in the right hand pane of the **Execute** tab.

.. thumbnail:: inputs_figure_one.png

Because Dagit is schema-aware, it knows that this pipeline now requires configuration in order to
run without errors. In this case, since the pipeline is relatively trivial, it wouldn't be
especially costly to run the pipeline and watch it fail. But when pipelines are complex and slow,
it's invaluable to get this kind of feedback up front rather than have an unexpected failure deep
inside a pipeline.

Recall that the execution plan, which you will ordinarily see above the log viewer in the
**Execute** tab, is the concrete pipeline that Dagster will actually execute. Without a valid
config, Dagster can't construct a parametrization of the logical pipeline -- so no execution plan
is available for us to preview.

Press `CTRL-Space` in order to bring up the typeahead assistant.

.. thumbnail:: inputs_figure_two.png

Here you can see all of the sections available in the environment dict. Don't worry, we'll get to
them all later.

Let's enter the config we need in order to execute our pipeline.

.. thumbnail:: inputs_figure_three.png

Note that as you type and edit the config, the config minimap hovering on the right side of the
editor pane changes to provide context -- so you always know where in the nested config schema you
are while making changes.
