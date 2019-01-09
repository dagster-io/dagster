Configuration Schemas
---------------------

Dagster includes a system for strongly-typed, self-describing configurations schemas. These
descriptions are very helpful when learning how to operate a pipeline, make a rich configuration
editing experience possible, and help to catch configuration errors before pipeline execution. 

Let's see how the configuration schema can prevent errors and improve pipeline documentation.
We'll replace the config field in our solid definition with a structured, strongly typed schema.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/configuration_schemas.py
   :linenos:
   :caption: configuration_schemas.py
   :emphasize-lines: 15

The previous env.yml file works as before:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/configuration_schemas.yml
   :linenos:
   :caption: configuration_schemas.yml

Now let's imagine we made a mistake and passed an ``int`` in our configuration:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/configuration_schemas_error_1.yml
   :linenos:
   :emphasize-lines: 9 
   :caption: configuration_schemas_error_1.yml

And then ran it:

.. code-block:: console

    $ dagster pipeline execute -f configuration_schemas.py \
    -n define_demo_configuration_schema_pipeline -e configuration_schemas_error_1.yml
    ...
    dagster.core.execution.PipelineConfigEvaluationError: Pipeline "demo_configuration_schema" config errors:
        Error 1: Type failure at path "root:solids:double_the_word:config:word" on type "String". Got "1".

Now, instead of a runtime failure which might arise deep inside a time-consuming or expensive
pipeline execution, and which might be tedious to trace back to its root cause, we get a clear,
actionable error message before the pipeline is ever executed.

Let's see what happens if we pass config with the wrong structure:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/configuration_schemas_error_2.yml
   :linenos:
   :emphasize-lines: 9 
   :caption: configuration_schemas_error_2.yml

And then run the pipeline:

.. code-block:: console

    $ dagster pipeline execute -f configuration_schemas.py \
    -n define_demo_configuration_schema_pipeline -e configuration_schemas_error_2.yml
    ...
    dagster.core.execution.PipelineConfigEvaluationError: Pipeline "demo_configuration_schema" config errors:
        Error 1: Undefined field "double_the_word_with_typed_config" at path root:solids
        Error 2: Missing required field "double_the_word" at path root:solids

Besides configured values, the type system is also used to evaluate the runtime values that flow
between solids. Types are attached, optionally, both to inputs and to outputs. If a type
is not specified, it defaults to the :py:class:`Any <dagster.core.types.Any>` type.

.. code-block:: python

    @solid(
        config_field=types.Field(
            types.Dict({'word': Field(types.String)})
        ),
        outputs=[OutputDefinition(types.String)],
    )
    def typed_double_word(info):
        return info.config['word'] * 2

You'll see here that now the output is annotated with a type. This both ensures
that the runtime value conforms requirements specified by the type (in this case
an instanceof check on a string) and also provides metadata to view in tools such
as dagit. That the output is a string is now guaranteed by the system. If you
violate this, execution halts.

So imagine we made a coding error (mistyped the output) such as:

.. code-block:: python

    @solid(
        config_field=types.Field(
            types.Dict({'word': Field(types.String)})
        ),
        outputs=[OutputDefinition(types.Int)],
    )
    def typed_double_word_mismatch(info):
        return info.config['word'] * 2

When we run it, it errors:

.. code-block:: sh

    $ dagster pipeline execute part_eight -e env.yml
    dagster.core.errors.DagsterInvariantViolationError: Solid typed_double_word_mismatch output name result output quuxquux
                type failure: Expected valid value for Int but got 'quuxquux'
