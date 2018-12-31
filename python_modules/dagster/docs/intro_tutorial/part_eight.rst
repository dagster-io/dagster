Configuration Schema
--------------------

Dagster has a system for strongly-typed, self-describing configurations schemas. These descriptions
are very helpful when learning how to operate a pipeline, schema allows for an improved configuration
editting experience, and catches configuration errors before pipeline execution. 


We are going show how the configuration schema can prevent errors and improve documentation.

.. code-block:: python

    @solid(
        config_field=types.Field(
            types.Dict{'word': Field(types.String)})
        )
    )
    def double_the_word(info):
        return info.config['word'] * 2

The previous env.yml file works as before:

.. code-block:: yaml

    context:
      default:
        config:
          log_level: DEBUG

    solids:
      double_the_word:
        config:
          word: quux

Now let's imagine we made a mistake and passed an ``int`` to word configuration:

.. code-block:: yaml

    context:
      default:
        config:
          log_level: DEBUG

    solids:
      double_the_word_with_typed_config:
        config:
          word: 1

And then ran it:

.. code-block:: sh

    $ dagster pipeline execute part_eight -e env.yml
    ...
    dagster.core.errors.DagsterTypeError: Invalid config value on type PartEight.Environment: Expected valid value for String but got 1.
    ...

Or if we passed the wrong field:

.. code-block:: yaml

    context:
      default:
        config:
          log_level: DEBUG

    solids:
      double_the_word_with_typed_config:
        config:
          wrong_word: quux

And then ran it:

.. code-block:: sh

    $ dagster pipeline execute part_eight -e env.yml
    ...
    dagster.core.errors.DagsterTypeError: Invalid config value on type PartEight.Environment: Field "wrong_word" is not defined on "double_the_word_with_typed_config". Defined {'word'}.
    ...

The type system is also used to evaluate the runtime values that flow between solids,
not just config. Types are attached, optionally, to inputs and outputs. If a type is not
specified, it defaults to the Any type.

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
