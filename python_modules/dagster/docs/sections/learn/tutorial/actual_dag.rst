An actual DAG
-------------

Next we will build a slightly more topologically complex DAG that demonstrates how dagster
determines the execution order of solids in a pipeline:

.. image:: actual_dag_figure_one.png

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/actual_dag.py
   :linenos:
   :caption: actual_dag.py

Again, it is worth noting how we are connecting *inputs* and *outputs* rather than just *tasks*.
Point your attention to the ``solid_d`` entry in the dependencies dictionary: we declare
dependencies on a per-input basis.

When you execute this example, you'll see that ``solid_a`` executes first, then ``solid_b`` and
``solid_c`` -- in any order -- and ``solid_d`` executes last, after ``solid_b`` and ``solid_c``
have both executed.

In more sophisticated execution environments, ``solid_b`` and ``solid_c`` could execute not just
in any order, but at the same time, since their inputs don't depend on each other's outputs --
but both would still have to execute after ``solid_a`` (because they depend on its output to
satisfy their inputs) and before ``solid_d`` (because their outputs in turn are depended on by
the input of ``solid_d``).

Try it in dagit or from the command line:

.. code-block:: console

   $ dagster pipeline execute -f actual_dag.py -n define_diamond_dag_pipeline

What's the output of this DAG?

We've seen how to wire solids together into DAGs. Now let's look more deeply at their
:doc:`Inputs <inputs>`, and start to explore how solids can interact with their external
environment.
