.. py:currentmodule:: dagster

.. _executing-our-first-pipeline:

Executing our first pipeline
----------------------------

.. toctree::
  :maxdepth: 1
  :hidden:

Assuming you've saved this pipeline as ``hello_cereal.py``, we can execute it via any of three
different mechanisms:

1. From the command line, using the ``dagster`` CLI.
2. From a rich graphical interface, using the ``dagit`` GUI tool.
3. From arbitrary Python scripts, using dagster's Python API.

Using the dagster CLI to execute a pipeline
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

From the directory in which you've saved the pipeline file, just run:

.. code-block:: console

    $ dagster pipeline execute -f hello_cereal.py -n hello_cereal_pipeline

You'll see the full stream of events emitted by dagster appear in the console, including our
call to the logging machinery, which will look like:

.. code-block:: console
  :emphasize-lines: 1

    2019-10-10 11:46:50 - dagster - INFO - system - a91a4cc4-d218-4c2b-800c-aac50fced1a5 - Found 77 cereals
                  solid = "hello_cereal"
        solid_definition = "hello_cereal"
                step_key = "hello_cereal.compute"

Success!

Using dagit to execute a pipeline
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To visualize your pipeline (which only has one node) in dagit, from the directory in which you've
saved the pipeline file, just run:

.. code-block:: console

   $ dagit -f hello_cereal.py -n hello_cereal_pipeline

You'll see output like

.. code-block:: console

    Loading repository...
    Serving on http://127.0.0.1:3000

You should be able to navigate to http://127.0.0.1:3000/p/hello_cereal_pipeline/explore in
your web browser and view your pipeline. It isn't very interesting yet, because it only has one
node.

.. thumbnail:: hello_cereal_figure_one.png

Clicking on the "Execute" tab (http://127.0.0.1:3000/p/hello_world_pipeline/execute) and you'll
see the two-paned view below.

.. thumbnail:: hello_cereal_figure_two.png

The left hand pane is empty here, but in more complicated pipelines, this is where you'll be able
to edit pipeline configuration on the fly.

The right hand pane shows the concrete execution plan corresponding to the logical structure of
the pipeline -- which also only has one node, ``hello_cereal.compute``.

Click the "Start Execution" button to execute this plan directly from dagit. A new window should
open, and you'll see a much more structured view of the stream of Dagster events start to appear in
the left-hand pane.

(If you have pop-up blocking enabled, you may need to tell your browser to allow pop-ups from
127.0.0.1 -- or, just navigate to the "Runs" tab to see this, and every run of your pipeline.)

.. thumbnail:: hello_cereal_figure_three.png

In this view, you can filter and search through the logs corresponding to your pipeline run.

Using the Python API to execute a pipeline
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you'd rather execute your pipelines as a script, you can do that without using the dagster CLI
at all. Just add a few lines to ``hello_cereal.py``:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/hello_cereal.py
   :linenos:
   :lineno-start: 26
   :lines: 26-28
   :caption: hello_cereal.py
   :language: python

Now you can just run:

.. code-block:: console

    $ python hello_cereal.py

The :py:func:`execute_pipeline` function called here is the core Python API for executing Dagster
pipelines from code.