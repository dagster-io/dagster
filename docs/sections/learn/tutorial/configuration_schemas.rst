Configuration Schemas
---------------------

Dagster includes a system for strongly-typed, self-describing configurations schemas. These
descriptions are very helpful when learning how to operate a pipeline, make a rich configuration
editing experience possible, and help to catch configuration errors before pipeline execution.

Let's see how the configuration schema can prevent errors and improve pipeline documentation. First,
consider a simple pipeline that replicates a word several times, then counts the number of resulting
characters:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/configuration_schemas_basic.py
   :lines: 3-22
   :linenos:
   :caption: configuration_schemas.py

The configuration YAML file works as before -- note that we are providing both ``inputs`` and
``config`` for ``multiply_the_word``, whereas ``count_letters`` has no config and takes its input
from the dependency on ``multiply_the_word``:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/configuration_schemas.yaml
   :caption: configuration_schemas.yaml

You should be able to run this with the usual CLI invocation:

.. code-block:: console

    $ dagster pipeline execute \
        -f configuration_schemas.py \
        -n configuration_schema_pipeline \
        -e configuration_schemas.yaml

Now let's imagine we made a mistake and passed a ``string`` in our configuration:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/configuration_schemas_bad_config.yaml
   :emphasize-lines: 7
   :caption: configuration_schemas_bad_config.yaml

And then ran it:

.. code-block:: console

    $ dagster pipeline execute \
        -f configuration_schemas.py \
        -n configuration_schema_pipeline \
        -e configuration_schemas_bad_config.yaml

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
        solid invocation: "multiply_the_word"
        solid definition: "multiply_the_word"


This pipeline is not typechecked and therefore error is caught at runtime. It would be preferable to
catch this before execution. We'll replace the config field in our solid definition with a
structured, strongly typed schema. In the example below, we've updated ``multiply_the_word`` to
require an integer field ``factor`` in its configuration:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/configuration_schemas.py
   :linenos:
   :emphasize-lines: 8
   :lines: 3-22
   :caption: configuration_schemas.py

Now, if we run the pipeline with the same incorrect configuration:

.. code-block:: console

    $ dagster pipeline execute \
        -f configuration_schemas.py \
        -n configuration_schema_pipeline \
        -e configuration_schemas_bad_config.yaml

We'll get a nice error *prior* to execution:

.. code-block:: console

    dagster.core.execution.context_creation_pipeline.DagsterInvalidConfigError: Pipeline
      "configuration_schema_pipeline" config errors:
    Error 1: Type failure at path "root:solids:multiply_the_word:config:factor" on type "Int". Value
      at path root:solids:multiply_the_word:config:factor is not valid. Expected "Int".


Now, instead of a runtime failure which might arise deep inside a time-consuming or expensive
pipeline execution which might be tedious to trace back to its root cause, we get a clear,
actionable error message before the pipeline is ever executed.

Let's see what happens if we pass config with the wrong structure:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/configuration_schemas_wrong_field.yaml
   :linenos:
   :emphasize-lines: 7
   :caption: configuration_schemas_wrong_field.yaml

And then run the pipeline:

.. code-block:: console

    $ dagster pipeline execute \
        -f configuration_schemas.py \
        -n configuration_schema_pipeline \
        -e configuration_schemas_wrong_field.yaml

    ...
    dagster.core.execution.context_creation_pipeline.DagsterInvalidConfigError:
    Pipeline "configuration_schema_pipeline" config errors:

    Error 1: Undefined field "multiply_the_word_with_typed_config" at path root:solids

    Error 2: Missing required field "multiply_the_word" at path root:solids
        Available Fields: "['count_letters', 'multiply_the_word']".

Next, we’ll see how to use the :doc:`Execution Context <execution_context>` to further configure
how pipeline execution interacts with its environment.
