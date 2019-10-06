User-Defined Types
------------------

Throughout the tutorial you have seen the use of builtins such as :py:class:`Int <dagster.Int>`
and :py:class:`String <dagster.String>` for types. However you will want to be able to define your
own dagster types to fully utilize the system. We'll go over that here.

As a simple example, we will create a custom type, ``Sauce`` and progressively add features to explore
whats possible with the type system.

Basic Typing
^^^^^^^^^^^^

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/custom_types.py
   :lines: 16, 45-47
   :linenos:

What this code doing is annotating/registering our new ``Sauce`` class as a dagster type. Now
one can include this type and use it as an input or output of a solid. The system will do a
typecheck to ensure that the object is of type ``Sauce``.

Now one can use it to define a solid:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/custom_types.py
   :lines: 60-63
   :linenos:


The type metadata now appears in dagit and the system will ensure the input and output to this
solid are indeed data frames.

Input Hydration Config
^^^^^^^^^^^^^^^^^^^^^^

This solid as defined is only expressed in terms of an in-memory object; it says nothing about
how this data should be sourced from or materialized to disk. This is where the notion of
input hydration and output materialization configs come into play. Once the user provides those
she is able to use the configuration language in order to parameterize the computation. Note:
one can always just write code in an upstream solid *instead* of using the configuration
system to do so.

Let us now add the input hydration config:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/custom_types.py
   :lines: 21-24
   :linenos:

Then insert this into the original declaration:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/custom_types.py
   :lines: 34-35,44-47
   :emphasize-lines: 2
   :linenos:

Now if you run a pipeline with this solid from dagit you will be able to provide sources for
these inputs via config:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/custom_type_input.yaml
   :linenos:


Output Materialization Config
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We will add output materialization config now. They are similar to input hydration config, except
that they are responsible for taking the in-memory object flowed through your computation and
materializing it to some persistent store. Outputs are purely *optional* for any computation,
whereas inputs *must* be provided for a computation to proceed. You will likely want outputs as for
a pipeline to be useful it should produce some materialization that outlives the computation.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/custom_types.py
   :lines: 27-31
   :linenos:

This has a similar aesthetic to an input hydration config but performs a different function. Notice that
it takes a third argument, ``sauce`` (it can be named anything), that is the value that was
outputted from the solid in question. It then takes the configuration data as "instructions" as to
how to materialize the value.

One connects the output materialization config to the type as follows:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/custom_types.py
   :lines: 34-36,44-47
   :emphasize-lines: 3
   :linenos:

Now we can provide a list of materializations to a given execution.

You'll note you can provide an arbitrary number of materializations. You can materialize any
given output any number of times in any number of formats.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/custom_type_output.yaml
   :linenos:


Type Metadata
^^^^^^^^^^^^^
User-defined types can also provide a metadata function that returns a :py:class:`TypeCheck <dagster.TypeCheck>`
object containing metadata entries about an instance of the type when it successfully passes the instanceof check.

We will use this to emit some summary statistics about our DataFrame type:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/custom_types.py
   :lines: 34-47
   :emphasize-lines: 4-10
   :linenos:
