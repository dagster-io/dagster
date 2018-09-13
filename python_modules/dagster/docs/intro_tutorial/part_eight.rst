Basic Typing
------------

Dagster includes an optional type system that can be applied to both runtime values
and configuration. We can use these types to both provide runtime type guarantees
as well as improve documentation and understandability.

There actually *have* been types during all previous parts of this tutorial. If the
use does not specify types for inputs, outputs, or config in dagster, they default
to the Any type, which can accept any and all values.

We are going to incrementally add typing to the example in part eight.

Before we had this:

.. code-block:: python

    from dagster import *

    @solid
    def double_the_word(info):
        return info.config['word'] * 2

We are going to make the configuration of this strongly typed prevent errors and improve
documentation.

.. code-block:: python

    from dagster import *

    @solid(config_def=ConfigDefinition(types.ConfigDictionary({'word': Field(types.String)})))
    def double_the_word_with_typed_config(info):
        return info.config['word'] * 2

The previous env.yml file works as before:

.. code-block:: yaml

    context:
        config:
            log_level: DEBUG

    solids:
        double_the_word_with_typed_config:
            config:
                word: quux

Now let's imagine we made a mistake and passed an int to word:

.. code-block:: yaml

    context:
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
    dagster.core.errors.DagsterTypeError: Error evaluating config for double_the_word_with_typed_config: Expected valid value for String but got 1

Or if we passed the wrong field:

.. code-block:: yaml

    context:
        config:
            log_level: DEBUG

    solids:
        double_the_word_with_typed_config:
            config:
                wrong_word: quux

And then ran it:

.. code-block:: sh

    $ dagster pipeline execute part_eight -e env.yml
    dagster.core.errors.DagsterTypeError: Error evaluating config for double_the_word_with_typed_config: Field wrong_word not found. Defined fields: {'word'}

The type system is also used to evaluate the runtime values that flow between solids,
not just config. Types are attached, optionally, to inputs and outputs. If a type is not
specified, it defaults to the Any type.

.. code-block:: python

    @solid(
        config_def=ConfigDefinition(types.ConfigDictionary({
            'word': Field(types.String)
        })),
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
        config_def=ConfigDefinition(types.ConfigDictionary({
            'word': Field(types.String)
        })),
        outputs=[OutputDefinition(types.Int)],
    )
    def typed_double_word(info):
        return info.config['word'] * 2

When we run it, it errors:

.. code-block:: sh

    $ dagster pipeline execute part_eight -e env.yml
    dagster.core.errors.DagsterInvariantViolationError: Solid typed_double_word_mismatch output name result
    output quuxquux type failure: Expected valid value for Int but got 'quuxquux'


