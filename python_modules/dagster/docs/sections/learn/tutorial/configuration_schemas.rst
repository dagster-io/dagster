Configuration Schemas
---------------------

Dagster includes a system for strongly-typed, self-describing configurations schemas. These
descriptions are very helpful when learning how to operate a pipeline, make a rich configuration
editing experience possible, and help to catch configuration errors before pipeline execution. 

Let's see how the configuration schema can prevent errors and improve pipeline documentation.
We'll replace the config field in our solid definition with a structured, strongly typed schema.

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/configuration_schemas.py
   :linenos:
   :caption: configuration_schemas.py

The configuration YAML file works as before:

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/configuration_schemas.yml
   :linenos:
   :caption: configuration_schemas.yml

Now let's imagine we made a mistake and passed a ``string`` in our configuration:

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/configuration_schemas_runtime_error.yml
   :linenos:
   :emphasize-lines: 12
   :caption: configuration_schemas_runtime_error.yml

And then ran it:

.. code-block:: console

    $ dagster pipeline execute -f configuration_schemas.py \
    -n define_demo_configuration_schema_repo \
    demo_configuration_schema \
    -e configuration_schemas_runtime_error.yml
    ...
    Traceback (most recent call last):
    ...
    File "configuration_schemas.py", line 20, in multiply_the_word
        return word * context.solid_config['factor']
    TypeError: can't multiply sequence by non-int of type 'str'

    The above exception was the direct cause of the following exception:

    Traceback (most recent call last):
    ...
    dagster.core.errors.DagsterExecutionStepExecutionError: Error occured during the execution of step:
        step key: "multiply_the_word.transform"
        solid instance: "multiply_the_word"
        solid definition: "multiply_the_word"


This pipeline is not typechecked and therefore error is caught at runtime. It would be preferable
to catch this before execution.

In order to do that, let us use the typed config solid.

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/configuration_schemas_type_mismatch_error.yml
   :linenos:
   :emphasize-lines: 12
   :caption: configuration_schemas_runtime_error.yml

And then run the pipeline

.. code-block:: console

    $ dagster pipeline execute -f configuration_schemas.py \
    -n define_demo_configuration_schema_repo \
    typed_demo_configuration_schema \
    -e configuration_schemas_type_mismatch_error.yml

And you'll get a nice error *prior* to execution:

.. code-block:: console

    dagster.core.execution.PipelineConfigEvaluationError:
    Pipeline "typed_demo_configuration_schema" config errors:
    Error 1: Type failure at path
    "root:solids:typed_multiply_the_word:config:factor" on type
    "Int". Got "'not_a_number'". Value not_a_number is not
    valid for type Int.


Now, instead of a runtime failure which might arise deep inside a time-consuming or expensive
pipeline execution, and which might be tedious to trace back to its root cause, we get a clear,
actionable error message before the pipeline is ever executed.

Let's see what happens if we pass config with the wrong structure:

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/configuration_schemas_wrong_field.yml
   :linenos:
   :emphasize-lines: 9 
   :caption: configuration_schemas_wrong_field.yml

And then run the pipeline:

.. code-block:: console

    $ dagster pipeline execute -f configuration_schemas.py \
    -n define_demo_configuration_schema_pipeline -e configuration_schemas_wrong_field.yml
    ...
    dagster.core.execution.PipelineConfigEvaluationError: Pipeline "demo_configuration_schema" config errors:
        Error 1: Undefined field "multiply_the_word_with_typed_config" at path root:solids
        Error 2: Missing required field "multiply_the_word" at path root:solids

Next, we'll see how to use the  :doc:`Execution Context <execution_context>` to further configure
how pipeline execution interacts with its environment.
